from models import (
    db,
    connect_db,
    User,
    Role,
    Company,
    User_Company,
    User_Role,
    Contact_Detail,
    Company,
    Driver,
    Location,
    Hours_of_Operation,
    Appointment_Slot,
    Booking
)
from functools import wraps
from sqlalchemy import and_, distinct, func
from datetime import datetime, timedelta
import pytz

from flask import request, url_for, redirect, jsonify

from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    hash_password,
    verify_password,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import requests
import os
user_datastore = SQLAlchemyUserDatastore(db, User, Role)


def signin_required(func):
    """Custom signin required decorator, ensures user is logged in."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('sign_in', next=request.url))
        return (func(*args, **kwargs))
    return decorated_view


def is_current_driver(first_name, last_name, company_id) -> bool:
    """Determines if submitted user is currently in drivers table"""

    fn = first_name
    ln = last_name
    driver_name = fn.lower() + ln.lower()
    current_drivers = Driver.query.filter_by(company_id=company_id).all()
    for driver in current_drivers:
        name = driver.first_name.lower() + driver.last_name.lower()
        if name == driver_name:
            return True

    return False


def create_user(form):
    """Creates user, role and contact information for user, logs in the user"""
    try:
        e = form.email.data.lower()
        pw = hash_password(form.password.data)
        fn = form.first_name.data.capitalize()
        ln = form.last_name.data.capitalize()
        m = form.phone_number.data
        c = form.company.data
        r = form.role.data

        # Attempt to create a new user
        user_datastore.create_user(
            email=e, password=pw, first_name=fn, last_name=ln)
        db.session.commit()

        # Fetch the newly created user, create related records
        user = User.query.filter_by(email=e).first()
        if not user:
            raise ValueError("User creation failed or user not found.")

        company = User_Company(user_id=user.id, company_id=c)
        user_role = Role.query.filter_by(name=r).first()
        if not user_role:
            raise ValueError("Role not found.")

        role = User_Role(user_id=user.id, role_id=user_role.id)
        contact = Contact_Detail(
            phone_number=m, email=e, entity_id=user.id, entity_type='user')

        if r == "Driver":
            is_driver = is_current_driver(fn, ln, c)
            if not is_driver:
                new_driver = Driver(company_id=c, first_name=fn, last_name=ln)
                db.session.add(new_driver)
                db.session.commit()
                driver_contact = Contact_Detail(
                    phone_number=m, email=e, entity_id=new_driver.id, entity_type='driver')
                db.session.add(driver_contact)
                db.session.commit()

        # Add company, role, and contact to the database
        add_to_db = [company, role, contact]
        db.session.add_all(add_to_db)
        db.session.commit()

        # Attempt to log in the user
        return login_user(user=user)

    except IntegrityError:
        db.session.rollback()
        return "An integrity error occurred. The user might already exist."
    except ValueError as e:
        db.session.rollback()
        return str(e)
    except SQLAlchemyError:
        db.session.rollback()
        return "A database error occurred."
    except Exception as e:
        # Catch-all for any other unforeseen errors
        db.session.rollback()
        return f"An unexpected error occurred: {e}"


def validate_user(form):
    """Validates user from form data"""

    user = User.query.filter_by(email=form.email.data).first()

    if user:
        if not verify_password(password=form.password.data, password_hash=user.password):
            return {'msg': f"Username {form.email.data} or password is incorrect please check the information and try again."}

        else:
            return {'user': user, 'msg': True}
    return {'msg': f"Username {form.email.data} does not exist, please register."}


timezones = {
    'ET': 'America/New_York',
    'CT': 'America/Chicago',
    'MT': 'America/Denver',
    'PT': 'America/Los_Angeles',
    'AZ': 'America/Phoenix'
}


def utc_to_local(utc_dt, timezone):
    """Convert the datetime from UTC to the locations local timezone"""
    tz = timezones[timezone]
    target_tz = pytz.timezone(tz)
    local_dt = utc_dt.astimezone(target_tz)

    return local_dt


def booked_apt_evt(loc_id):
    """Takes a location id and returns all booked appointments in the JSON FullCalendar event format - used as API call from Javascript"""
    booked = Booking.query.filter(
        Booking.is_complete == False, Booking.status != 'cancelled').all()
    for booking in booked:
        loc_tz = booking.appointment_slots.location.get_contact_info()

        booking.appointment_slots.start_time = utc_to_local(
            booking.appointment_slots.start_time, loc_tz.time_zone)
        booking.appointment_slots.end_time = utc_to_local(
            booking.appointment_slots.end_time, loc_tz.time_zone)

    loc_booked = NotImplemented
    user = User.query.get(current_user.id)
    if current_user.roles[0].name == "Driver":

        driver = Driver.query.filter_by(
            first_name=current_user.first_name, last_name=current_user.last_name).first()
        loc_booked = [booking for booking in booked if booking.appointment_slots.location_id == loc_id and
                      booking.company_id == user.company[0].id and
                      booking.driver_id == driver.id]

    elif current_user.roles[0].name == "Dispatcher":
        loc_booked = [booking for booking in booked if booking.appointment_slots.location_id == loc_id and
                      user.company[0].id == booking.company_id]

    elif current_user.roles[0].name == "Hub_Manager":
        loc_booked = [
            booking for booking in booked if booking.appointment_slots.location_id == loc_id]

    booked_events = [
        {
            'id': booking.id,
            'title': f"{booking.companies.name} {booking.drivers.first_name}",
            'start': booking.appointment_slots.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': booking.appointment_slots.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'url': f'/booking/{booking.id}',
            'backgroundColor': 'green' if booking.is_load_planned else 'yellow',
            'textColor': 'white' if booking.is_load_planned else 'black',
        }
        for booking in loc_booked] if loc_booked else ''

    # for available attributes see https://fullcalendar.io/docs/event-object

    return booked_events


def available_apt_evt(loc_id):
    """Returns available appointments for the given location in JSON format for FullCalendar"""
    slots = Appointment_Slot
    available = (slots.query
                 .with_entities(slots.start_time, slots.end_time, func.min(slots.id).label('id'))
                 .filter(
                     slots.location_id == loc_id,
                     slots.start_time > datetime.utcnow(),
                     slots.is_booked == False
                 )
                 .group_by(slots.start_time, slots.end_time)
                 .all())

    loc_info = Contact_Detail.query.filter(
        and_(
            Contact_Detail.entity_type == 'location',
            Contact_Detail.entity_id == loc_id)).first()

    available_apt_events = [
        {
            'id': apt.id,
            'title': 'Available',
            'start': utc_to_local(apt.start_time, loc_info.time_zone).strftime('%Y-%m-%dT%H:%M:%S'),
            'end': utc_to_local(apt.end_time, loc_info.time_zone).strftime('%Y-%m-%dT%H:%M:%S'),
            'url': f'/book/{loc_id}/{apt.id}'
        }
        for apt in available
    ]

    return available_apt_events


def drivers_by_company_id(company_id):
    """Queries database for drivers that work for a passed in company id"""
    drivers = Driver.query.filter_by(company_id=company_id).all()

    data = [{driver.id: f"{driver.first_name} {driver.last_name}"}
            for driver in drivers
            ]

    return data


def convert_seconds(sec):
    """Travel time data from BingMaps API call is returned in seconds, this converts it into hours and minutes """
    h = sec // 3600
    remainder = sec % 3600
    m = remainder // 60
    return (f'{h:02d}h {m:02d}m')


def get_trip_info(loc1_id, loc2_id, slot_id):
    """Loc1 (Origin), Loc2 (Destination) and appointment is passed in to get the trip information to load the Truck GPS map
        locatins are converted to addressess then passed to the BingMaps Truck Map API, the response is then parsed and returned to
        the caller formatted for the Map on book.html / booking_detail.html
    """
    loc1 = Location.query.get_or_404(loc1_id)
    info1 = loc1.get_contact_info()
    address1 = f'{info1.street_address}'
    f'{info1.city} {info1.state} {info1.zip_code}'
    loc2 = Location.query.get_or_404(loc2_id)
    info2 = loc2.get_contact_info()
    address2 = f'{info2.street_address}'
    f'{info2.city} {info2.state} {info2.zip_code}'
    slot = Appointment_Slot.query.get_or_404(slot_id)

    api_key = os.environ.get('bing_API_key')
    url = f"https://dev.virtualearth.net/REST/v1/Routes/Truck?key={api_key}"

    req_data = {
        "waypoints": [{
            "address": address1,
        },
            {
                "address": address2,
        },
        ],
        "dateTime": f'{slot.end_time}',
        "routeAttributes": "routePath",
        "vehicleSpec": {
            "weightUnit": "lb",
            "dimensionsUnit": "ft",
            "vehicleHeight": 14,
            "vehicleLength": 80,
            "vehicleWeight": 80000,
            "vehicleAxles": 5,
            "vehicleTrailers": 1,
            "vehicleSemi": True,

        }
    }

    response = requests.post(url, json=req_data)
    data = response.json()
    data_path = data['resourceSets'][0]['resources'][0]['routeLegs'][0]
    travelTime = convert_seconds(data_path['travelDuration'])
    travelTimeTraffic = convert_seconds(
        data['resourceSets'][0]['resources'][0]['travelDurationTraffic'])
    trip_info = [{
        "startLocation": {
            "coordinates": data_path['startLocation']['point']['coordinates'],
            "address": data_path['startLocation']['address']['formattedAddress']
        },
        "endLocation": {
            "coordinates": data_path['endLocation']['point']['coordinates'],
            "address": data_path['endLocation']['address']['formattedAddress']
        },
        "totalDistance": data_path['travelDistance'],
        "travelTime": travelTime,
        "travelTimeTraffic": travelTimeTraffic,
        "routePath": data['resourceSets'][0]['resources'][0]['routePath']['line']['coordinates']

    }]

    return trip_info


def set_form_choices(loc_id, form):
    """Sets the form choices for booking an appointment based upon the users role
    If Driver role, they can only book an appointment for themselves (Company / Driver pre-selected in form)
    If Dispatcher, they can only book an appointment for drivers at their company (Preloads company and drivers for that company)
    If Hub_Manager or Planner they can book an appointment for any company or driver (Preloads company list, then Javascript calls drivers_by_company_id to load the drivers for that company )
    """
    if current_user.roles[0] == 'Driver' or current_user.roles[0] == 'Dispatcher':

        form.company_id.choices = [
            (current_user.company[0].id, current_user.company[0].name)]
        if current_user.roles[0] == 'Driver':
            driver = Driver.query.filter_by(
                company_id=current_user.company[0].id,
                first_name=current_user.first_name,
                last_name=current_user.last_name
            ).first()
            form.driver_id.choices = [
                (driver.id, f"{driver.first_name} {driver.last_name}")]

        if current_user.roles[0] == "Dispatcher":
            form.driver_id.choices = [(driver.id, f"{driver.first_name} {driver.last_name}")
                                      for driver in Driver.query.filter_by(
                                          company_id=current_user.company[0].id,
                                          first_name=current_user.first_name,
                                          last_name=current_user.last_name
            ).all()]

    else:
        form.company_id.choices = [('', 'Select an option...')] + [(company.id, company.name)
                                                                   for company in Company.query.all()]
        # driver choices will be added dynamically with js based upon company selection
    form.destination.choices = [('', 'Select an option...')] + [(location.id, location.name)
                                                                for location in Location.query.filter(
        Location.id != loc_id
    ).all()]

    return form


def check_appointment_status(appointment):
    """Checks the status of an appointment before attempting to book it if the appointment is booked
        trys to return a new appointment with the same time slot.
    """
    if appointment.is_booked == True:
        new_appointment = Appointment_Slot.query.filter(
            Appointment_Slot.start_time == appointment.start_time,
            Appointment_Slot.location == appointment.location,
            Appointment_Slot.is_booked == False).first()

        if new_appointment:
            return new_appointment
        else:
            four_hours = timedelta(hours=4)
            start_range = appointment.start_time - four_hours
            end_range = appointment.start_time + four_hours
            closest_appointments = Appointment_Slot.query.filter(
                Appointment_Slot.location_id == appointment.location_id,
                Appointment_Slot.is_booked == False,
                Appointment_Slot.start_time >= start_range,
                Appointment_Slot.start_time <= end_range
            ).order_by(Appointment_Slot.start_time).all()
            if closest_appointments:
                return closest_appointments
            else:
                return None
    return appointment


def book_appointments(form, appointment):
    valid_appointment = check_appointment_status(appointment)
    if valid_appointment:
        if isinstance(valid_appointment, Appointment_Slot):

            try:
                valid_appointment.is_booked = True
                if form.delivery_only.data:
                    valid_appointment.notes = "Delivery Only" + " " + form.notes.data
                else:
                    valid_appointment.notes = form.notes.data

                booked = Booking(
                    slot_id=valid_appointment.id,
                    delivery_id=None if form.delivery_only.data else int(
                        form.destination.data),
                    driver_id=int(form.driver_id.data),
                    company_id=int(form.company_id.data),
                    created_by=current_user.id,
                    status='scheduled'
                )

                add_to_db = [valid_appointment, booked]
                db.session.add_all(add_to_db)
                db.session.commit()
                loc_data = valid_appointment.location.get_contact_info()
                start_time = utc_to_local(
                    valid_appointment.start_time, loc_data.time_zone)
                format = '%m-%d-%Y %H:%M %p'
                msg = dict(
                    message=f'Your appointment at {
                        valid_appointment.location.name} for'
                    f'{start_time.strftime(format)} is scheduled. ',
                    type='success'
                )

                return msg

            except Exception as e:
                db.session.rollback()
                msg = dict(message='There was an error processing your request please try again',
                           type='danger')
                print(msg)
                return msg
        else:

            msg = dict(
                message="The appointment time you selected has been booked. Unfortunately, there is not another appointment available with the same time. Below are the closest available appointment times. Please click one to book it or close this window to return to the calendar view. ",
                appointments=[dict(
                    location_id=apt.location.id,
                    appointment_id=apt.id,
                    start_time=apt.local_start_time(),
                    end_time=apt.local_end_time()
                )for apt in valid_appointment],
                type='warning'
            )
            return msg
    else:
        msg = dict(
            message='Sorry, this appointment has been booked. The system checked for available appointments with in 4 hours of this appointment and none were found. Please select another appointment',
            type='danger'
        )
        print(msg)
        return msg

# TODO: create the function for converting address to coords
# https://learn.microsoft.com/en-us/bingmaps/rest-services/locations/find-a-location-by-address
