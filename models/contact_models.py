from .user_models import db


class Company(db.Model):
    """Company records table"""

    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(50), nullable=False)

    drivers = db.Relationship('Driver', backref='companies')

    bookings = db.Relationship('Booking', backref='companies')

    def get_contact_info(self):
        return Contact_Detail.query.filter_by(
            entity_type='company',
            entity_id=self.id
        ).first()


class User_Company(db.Model):
    """Manages the one to many relationship between users and companies"""

    __tablename__ = 'user_company'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.ForeignKey('users.id', ondelete="CASCADE"),
                        nullable=False)

    company_id = db.Column(db.ForeignKey('companies.id', ondelete="CASCADE"),
                           nullable=False)


class Driver(db.Model):
    """Driver information"""

    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    company_id = db.Column(db.ForeignKey(
        'companies.id', ondelete="CASCADE"), nullable=False)

    first_name = db.Column(db.String(50), nullable=False)

    last_name = db.Column(db.String(50), nullable=False)

    bookings = db.Relationship('Booking', backref='drivers')

    def get_contact_info(self):
        return Contact_Detail.query.filter_by(
            entity_type='driver',
            entity_id=self.id
        ).first()


class Contact_Detail(db.Model):
    """Contact details for users, drivers and locations"""

    __tablename__ = 'contact_details'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    phone_number = db.Column(db.String(10))

    email = db.Column(db.String(50))

    street_address = db.Column(db.String(100))

    city = db.Column(db.String(50))

    state = db.Column(db.String(2))

    zip_code = db.Column(db.Integer)

    latitude = db.Column(db.Float)

    longitude = db.Column(db.Float)

    entity_id = db.Column(db.Integer, nullable=False)

    # 'user', 'location', 'driver', 'company'
    entity_type = db.Column(db.String(50), nullable=False)

    time_zone = db.Column(db.String(2))
