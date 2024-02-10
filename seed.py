from models import db, connect_db, Location, Hours_of_Operation, Appointment_Slot, Booking, Company, User_Company, Driver, Contact_Detail, User, Role, User_Role
from faker import Faker
import random
from datetime import timedelta, datetime

from app import app

# Initialize Faker for generating random data
fake = Faker()
app.app_context().push()
# Connect to DB (ensure this matches your actual DB connection logic)
# ...
db.drop_all()
db.create_all()
# Create 10 Locations
post_offices = [{'name': 'Rocklin',
                 'street_address': '5515 Pacific St',
                 'city': 'Rocklin',
                 'state': 'CA',
                 'zip_code': '95677',
                 'time_zone': 'PT'},
                {'name': 'Denver',
                 'street_address': '7550 E 53rd Pl',
                 'city': 'Denver',
                 'state': 'CO',
                 'zip_code': '80217',
                 'time_zone': 'MT'},
                {'name': 'Waco',
                 'street_address': '424 Clay Ave',
                 'city': 'Waco',
                 'state': 'TX',
                 'zip_code': '76706',
                 'time_zone': 'CT'},
                {'name': 'Hammond',
                 'street_address': '5530 Sohl Ave',
                 'city': 'Hammond',
                 'state': 'IN',
                 'zip_code': '46320',
                 'time_zone': 'CT'},
                {'name': 'Nashville',
                 'street_address': '525 Royal Pkwy',
                 'city': 'Nashville',
                 'state': 'TN',
                 'zip_code': '37229',
                 'time_zone': 'CT'},
                {'name': 'Mobile',
                 'street_address': '3410 Joe Treadwell Dr',
                 'city': 'Mobile',
                 'state': 'AL',
                 'zip_code': '36606',
                 'time_zone': 'CT'},
                {'name': 'Richmond',
                 'street_address': '1645 W Broad St',
                 'city': 'Richmond',
                 'state': 'VA',
                 'zip_code': '23220',
                 'time_zone': 'ET'},
                {'name': 'Charlotte',
                 'street_address': '201 N McDowell St',
                 'city': 'Charlotte',
                 'state': 'NC',
                 'zip_code': '28204',
                 'time_zone': 'ET'},
                {'name': 'Atlanta',
                 'street_address': '3900 Crown Rd SE',
                 'city': 'Atlanta',
                 'state': 'GA',
                 'zip_code': '30304',
                 'time_zone': 'ET'},
                {'name': 'Orlando',
                 'street_address': '51 E Jefferson St',
                 'city': 'Orlando',
                 'state': 'FL',
                 'zip_code': '32801',
                 'time_zone': 'ET'}]

for loc in post_offices:
    location = Location(name=loc['name'])
    db.session.add(location)
    db.session.commit()  # Commit to assign an ID to the location
    contact_detail = Contact_Detail(
        street_address=loc['street_address'],
        city=loc['city'],
        state=loc['state'],
        zip_code=loc['zip_code'],
        entity_id=location.id, entity_type='location',
        time_zone=loc['time_zone'])
    db.session.add(contact_detail)

db.session.commit()  # Final commit for remaining data


# Create 10 Companies
for _ in range(10):
    company = Company(name=fake.company())
    db.session.add(company)

# Create 20 Drivers
for i in range(20):
    driver = Driver(company_id=(i // 2) + 1,
                    first_name=fake.first_name(), last_name=fake.last_name())
    db.session.add(driver)

# Create Hours of Operation
for i in range(1, 11):
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        open_time = fake.time()
        close_time = (datetime.strptime(open_time, '%H:%M:%S') +
                      timedelta(hours=random.choice([10, 12, 24]))).time()
        hours = Hours_of_Operation(
            location_id=i, day_of_week=day, open_time=open_time, close_time=close_time)
        db.session.add(hours)

# Create Appointment Slots
for i in range(1, 11):
    # Assuming each location has a fixed number of slots per day
    for _ in range(5):  # 5 slots per day as an example
        start_time = fake.date_time_between(
            start_date=datetime.utcnow(), end_date='+7d')
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=2)
        slot = Appointment_Slot(
            location_id=i, start_time=start_time, end_time=end_time, is_booked=False)
        db.session.add(slot)

db.session.commit()

roles = [
    ("Driver", "Driver role enabling the user to view, edit, cancel, create appointments for only themselves"),
    ("Dispatcher", "Dispatcher role can view, edit, cancel or create appointments for any drivers in their company"),
    ("Hub_Manager", "Hub Manager role can view, edit, cancel or create an appointment for any hub location"),
    ("Admin", "Full Admin access to CRUD functions")
]

for name, desc in roles:
    role = Role(name=name, description=desc)
    db.session.add(role)
    db.session.commit()
