from dotenv import load_dotenv
import os


from flask import (
    Flask,
    render_template,
    redirect,
    session,
    flash,
    url_for,
    request,
    g,
    jsonify
)

from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    auth_required,
    hash_password,
    verify_password,
    login_user,
    logout_user,
    current_user
)

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
from forms import (
    RegistrationForm,
    UserLoginForm,
    AppointmentForm,
    EditProfileForm,

)

from app_logic import (
    create_user,
    validate_user,
    signin_required,
    available_apt_evt,
    booked_apt_evt,
    drivers_by_company_id,
    get_trip_info,
    utc_to_local,
    set_form_choices,
    book_appointments

)

app = Flask(__name__)

load_dotenv()

app.config["DEBUG"] = True
app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
app.config["SESSION_COOKIE_SAMESITE"] = "strict"
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
app.config["SECURITY_PASSWORD_HASH"] = 'bcrypt'
app.config["SECURITY_PASSWORD_SALT"] = os.environ.get("PASSWORD_SALT")
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://mktuxilm:7q4YLdsCeBddl-Bz_y45LXs60pCajuGu@lallah.db.elephantsql.com/mktuxilm"
app.config["SQLALCHEMY_ECHO"] = False
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, }
# app.config["SECURITY_LOGIN_URL"] = '/signin'


connect_db(app)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@app.before_request
def before_request():
    g.user = current_user


# User registration and signin routes
@app.route('/signin', methods=["GET", "POST"])
def sign_in():
    """Handles UserLoginForm, validates user, logs user in if validated else returns invalid user message."""
    form = UserLoginForm()
    if form.validate_on_submit():
        info = validate_user(form)
        if info['msg'] == True:
            login_user(user=info['user'], remember=form.remember.data)
            if current_user.roles[0] == "Planner":
                return redirect(url_for('appointment_table'))
            return redirect(url_for('home'))
        else:
            flash(info['msg'], "danger")

    return render_template('/security/user_login.html', form=form)


@app.route('/signout', methods=["POST"])
@signin_required
def sign_out():
    """Logs user out"""
    logout_user()
    flash("Log out successful", "success")
    return redirect(url_for('sign_in'))


@app.route('/register', methods=["GET", "POST"])
def register():
    """User Registration"""
    form = RegistrationForm()
    form.company.choices = [('', 'Select an option...')] + [(company.id, company.name)
                                                            for company in Company.query.all()]

    if form.validate_on_submit():
        new_user = create_user(form)
        if isinstance(new_user, User):
            return redirect(url_for('home'))
        else:
            flash(new_user, "danger")
            return redirect(url_for('register'))
    return render_template('register.html', form=form)


@app.route('/reset-pw')
def reset_password():
    """User Password reset - Not Implemented"""
    # build this route              <-----
    return redirect(url_for('sign_in'))


# Routes containing user views
@app.route('/')
@signin_required
def home():
    """Route for calendar view"""

    return render_template('cal.html')


@app.route('/appointment_table')
@signin_required
def appointment_table():
    """Route for appointment table view"""

    return render_template('booking_table.html')


@app.route('/editprofile/<int:user_id>', methods=["GET", "POST"])
@signin_required
def edit_profile(user_id):
    """Route for user to edit their profile, handles form submission and database updates. """
    form = EditProfileForm()
    if form.validate_on_submit():
        form.email.data = current_user.email
        verified = validate_user(form)
        if verified:
            user = User.query.get(current_user.id)
            user_info = Contact_Detail.query.filter(
                Contact_Detail.entity_id == user.id,
                Contact_Detail.entity_type == 'user'
            ).first()
            user.first_name = form.first_name.data if form.first_name.data else user.first_name
            user.last_name = form.last_name.data if form.last_name.data else user.last_name
            user.password = hash_password(
                form.new_password.data) if form.new_password.data else user.password
            user_info.phone_number = form.phone_number.data if form.phone_number.data else user_info.phone_number

            add_to_db = [user, user_info]
            db.session.add_all(add_to_db)
            db.session.commit()
            flash('Profile updated', "success")

        else:
            flash(
                'Password was incorrect, please check you password and try again.', "warning")

        return redirect(url_for('home'))

    return render_template('edit_profile.html', form=form)


@app.route('/book/<loc_id>/<apt_id>', methods=["GET", "POST"])
@signin_required
def book_appointment(loc_id, apt_id):
    """Get and Post route for booking an appointment, handles form submission and database updates"""
    form = AppointmentForm()
    appointment = Appointment_Slot.query.get_or_404(apt_id)

    form = set_form_choices(loc_id, form)

    if form.validate_on_submit():
        confirmation = book_appointments(form, appointment)

        if confirmation['type'] != 'warning':
            flash(f'{confirmation['message']}', confirmation['type'])
            return redirect(url_for('home'))

        else:
            flash(f'{confirmation['message']}', confirmation['type'])
            return render_template('cal.html', alt_apt=confirmation['appointments'])

    return render_template('book.html', form=form, slot=appointment)


@app.route('/booking/<int:booking_id>')
@signin_required
def booking_detail(booking_id):
    """Route to display the booking detail for the booking id passed in"""
    booking = Booking.query.get_or_404(booking_id)

    return render_template('booking_detail.html', booking=booking)


@app.route('/booking-table')
@signin_required
def booking_table():
    """Route to display booking table view"""

    return render_template('booking_table.html')


# API Routes
@app.route('/get_locations')
@signin_required
def list_locations():
    """REST API route to get locations, returns json with location id, location name"""
    loc_query = Location.query.all()

    return jsonify(loc_data={loc.id: loc.name for loc in loc_query})


@app.route('/get_current_booked/<int:loc_id>')
@signin_required
def get_events(loc_id):
    """REST API route to get current booked appointments for the location passed in"""
    return booked_apt_evt(loc_id)


@app.route('/get_current_available/<int:loc_id>')
@signin_required
def get_available(loc_id):
    """REST API route to get current available appointments for the location passed in"""

    return available_apt_evt(loc_id)


@app.route('/get-drivers/<int:company_id>')
@signin_required
def get_drivers(company_id):
    """REST API route to get drivers for a company id passed in"""

    data = drivers_by_company_id(company_id)

    return jsonify(data)


@app.route('/get_map_data/<int:loc1_id>/<int:loc2_id>/<int:slot_id>')
@signin_required
def get_map_data(loc1_id, loc2_id, slot_id):
    """REST API route to get map data from BingMaps"""

    data = get_trip_info(loc1_id, loc2_id, slot_id)

    return data


@app.route('/cancel/<int:booking_id>', methods=["POST"])
@signin_required
def cancel_booking(booking_id):
    """REST API route to cancel a booked appointment for the booking id passed in"""
    booking = Booking.query.get_or_404(booking_id)
    booking.appointment_slots.is_booked = False
    booking.status = "cancelled"
    db.session.add(booking)
    db.session.commit()

    return jsonify({"message": "The appointment has been canceled."})


@app.route('/is_planned/<int:booking_id>', methods=["POST"])
@signin_required
def booking_is_planned(booking_id):
    """REST API route to update the status of the booked appointment passed in to planned"""
    booking = Booking.query.get_or_404(booking_id)
    booking.is_load_planned = True
    booking.status = "planned"
    db.session.add(booking)
    db.session.commit()

    return jsonify({"message": "Load status updated to planned."})


@app.route('/completed/<int:booking_id>', methods=["POST"])
@signin_required
def booking_is_completed(booking_id):
    """REST API route to update the status of the booked appointment passed in to completed"""
    booking = Booking.query.get_or_404(booking_id)
    booking.is_complete = True
    booking.status = "completed"
    db.session.add(booking)
    db.session.commit()

    return jsonify({"message": "Appointment status updated to complete"})


@app.route('/get_booked_not_complete')
@signin_required
def get_all_booked():
    """REST API route to get the appointments that are booked but not completed or cancelled"""
    data = Booking.query.filter(
        Booking.is_complete == False, Booking.status != 'cancelled')
    data_list = [item.serialize() for item in data]
    return jsonify(data_list)


@app.route('/get_my_bookings/<int:id>')
@signin_required
def get_my_bookings(id):
    """REST API route to get booked appointments for the driver id that is passed in"""
    driver = Driver.query.get_or_404(id)
    bookings = driver.bookings
    data_list = [booking.serialize() for booking in bookings]

    return jsonify(data_list)


@app.route('/get_company_bookings/<int:id>')
@signin_required
def get_company_bookings(id):
    """REST API route to get booked appointments for the company id that is passed in"""
    company = Company.query.get_or_404(id)
    bookings = company.bookings
    data_list = [booking.serialize() for booking in bookings]

    return jsonify(data_list)


@app.route('/driver_id')
@signin_required
def get_driver_id():
    """REST API route to get a driver id based on the name of the currently logged in user"""
    driver = Driver.query.filter(Driver.first_name == current_user.first_name,
                                 Driver.last_name == current_user.last_name).first()

    data = {'message': driver.id if driver else False}

    return jsonify(data)


@app.route('/seed')
@signin_required
def load():
    from faker import Faker
    from datetime import datetime, timedelta
    fake = Faker()
    count = 0
    try:
        for i in range(1, 11):
            # Assuming each location has a fixed number of slots per day
            for _ in range(5):  # 5 slots per day as an example
                start_time = fake.date_time_between(
                    start_date=datetime.utcnow(), end_date='+7d')
                start_time = start_time.replace(
                    minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=2)
                slot = Appointment_Slot(
                    location_id=i, start_time=start_time, end_time=end_time, is_booked=False)
                db.session.add(slot)
                count += 1
        db.session.commit()
        flash(f'{count} Appointments created', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')

    return redirect(url_for('home'))
# template filters

# For date / time formatting used in the Jinja templates.


@app.template_filter()
def show_dateformat(value, format='%Y-%m-%d'):
    return value.strftime(format)


@app.template_filter()
def show_timeformat(value, format='%I:%M %p'):
    return value.strftime(format)
