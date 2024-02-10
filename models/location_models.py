from sqlalchemy import DateTime, Time
from sqlalchemy.sql import and_
from . import db
from datetime import datetime
from . import Contact_Detail, User
import pytz


class Location(db.Model):
    """Location records"""

    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    loc_num = db.Column(db.Integer)

    name = db.Column(db.String(50), nullable=False)

    hours = db.relationship('Hours_of_Operation', backref='locations')

    def avail_appts(self, start_date, end_date):
        return Appointment_Slot.get_available_slots(self.id, start_date, end_date)

    def booked_appts(self, start_date, end_date):
        return Appointment_Slot.get_active_bookings(self.id, start_date, end_date)

    def get_contact_info(self):
        return Contact_Detail.query.filter_by(
            entity_type='location',
            entity_id=self.id
        ).first()


class Hours_of_Operation(db.Model):
    """Records the hours of operation for a location"""

    __tablename__ = 'operating_hours'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id'), nullable=False)

    day_of_week = db.Column(db.String(10), nullable=False)

    open_time = db.Column(Time, nullable=False)

    close_time = db.Column(Time, nullable=False)


class Appointment_Slot(db.Model):
    """Appointment availability for a location"""

    __tablename__ = 'appointment_slots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    location_id = db.Column(db.Integer, db.ForeignKey(
        'locations.id', ondelete='CASCADE'), nullable=False)

    start_time = db.Column(DateTime(timezone=True), nullable=False)

    end_time = db.Column(DateTime(timezone=True), nullable=False)

    is_booked = db.Column(db.Boolean, default=False, nullable=False)

    notes = db.Column(db.Text)

    booking = db.relationship('Booking', backref='appointment_slots')

    location = db.relationship('Location', backref='appointment_slots')

    @classmethod
    def get_available_slots(cls, location_id, start_date=None, end_date=None):
        if start_date is None:
            start_date = datetime.utcnow()
        query = cls.query.filter(
            cls.location_id == location_id,
            cls.is_booked == False,
            cls.start_time >= start_date
        )

        if end_date:
            query = query.filter(cls.start_time <= end_date)

        return query.all()

    @classmethod
    def get_active_bookings(cls, location_id, start_date=None, end_date=None):
        if start_date is None:
            start_date = datetime.utcnow()
        query = cls.query.filter(
            cls.location_id == location_id,
            cls.is_booked == True,
            cls.start_time >= start_date
        )

        if end_date:
            query = query.filter(cls.start_time <= end_date)

        return query.all()

    zones = {
        'ET': 'America/New_York',
        'CT': 'America/Chicago',
        'MT': 'America/Denver',
        'PT': 'America/Los_Angeles',
        'AZ': 'America/Phoenix'
    }

    def local_start_time(self):

        loc_tz = self.location.get_contact_info().time_zone
        tz = self.zones[loc_tz]
        target_tz = pytz.timezone(tz)
        local_dt = self.start_time.astimezone(target_tz)

        return local_dt

    def local_end_time(self):

        loc_tz = self.location.get_contact_info().time_zone
        tz = self.zones[loc_tz]
        target_tz = pytz.timezone(tz)
        local_dt = self.end_time.astimezone(target_tz)

        return local_dt


class Booking(db.Model):
    """Booked Appointments"""

    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    slot_id = db.Column(db.ForeignKey('appointment_slots.id'), nullable=False)

    # destination, can be null if drop only
    delivery_id = db.Column(db.ForeignKey('locations.id'))

    driver_id = db.Column(db.ForeignKey('drivers.id'), nullable=False)

    company_id = db.Column(db.ForeignKey('companies.id'), nullable=False)

    is_load_planned = db.Column(db.Boolean, default=False)

    is_complete = db.Column(db.Boolean, default=False)

    booking_time = db.Column(db.DateTime(timezone=True), default=db.func.now())

    created_by = db.Column(db.ForeignKey('users.id'), nullable=False)

    # scheduled, completed, cancelled
    status = db.Column(db.String(15))

    def delivery_name(self):
        if self.delivery_id:
            return Location.query.get(int(self.delivery_id))
        else:
            return "Delivery Only"

    def creator(self):
        return User.query.get(int(self.created_by))

    def serialize(self):
        origin_contact_info = self.appointment_slots.location.get_contact_info()
        dest_info = self.delivery_name()
        return {
            'id': self.id,
            'slot_id': self.slot_id,
            'origin_id': self.appointment_slots.location_id,
            'origin_name': self.appointment_slots.location.name,
            'delivery_id': self.delivery_id if self.delivery_id else '',
            'delivery_name': self.delivery_name().name if self.delivery_name() != 'Delivery Only' else 'Delivery Only',
            'appointment_time': self.appointment_slots.start_time,
            'company_id': self.company_id,
            'company_name': self.companies.name,
            'driver_id': self.driver_id,
            'driver_name': self.drivers.first_name + ' ' + self.drivers.last_name,
            # 'driver_phone': self.drivers.get_contact_info().phone_number if self.drivers.get_contact_info().phone_number else '',
            'is_planned': self.is_load_planned,
            'is_complete': self.is_complete,
            'created_by': self.creator().first_name + ' ' + self.creator().last_name,
            'booking_time': self.booking_time,
            'origin_timezone': origin_contact_info.time_zone,
            'origin_street_address': origin_contact_info.street_address,
            'origin_city': origin_contact_info.city,
            'origin_state': origin_contact_info.state,
            'origin_zip_code': origin_contact_info.zip_code,
            'destination_timezone': dest_info.get_contact_info().time_zone if self.delivery_name() != 'Delivery Only' else 'Delivery Only',
            'destination_street_address': dest_info.get_contact_info().street_address if self.delivery_name() != 'Delivery Only' else 'Delivery Only',
            'destination_city': dest_info.get_contact_info().city if self.delivery_name() != 'Delivery Only' else 'Delivery Only',
            'destination_state': dest_info.get_contact_info().state if self.delivery_name() != 'Delivery Only' else 'Delivery Only',
            'destination_zip_code': dest_info.get_contact_info().zip_code if self.delivery_name() != 'Delivery Only' else 'Delivery Only',
            'notes': self.appointment_slots.notes,
            'status': self.status

        }
