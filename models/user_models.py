from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
import uuid


bcrypt = Bcrypt()

db = SQLAlchemy()


def connect_db(app):
    db.app = app
    db.init_app(app)


class User(db.Model, UserMixin):
    """Database model for user management"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    email = db.Column(db.String(40), unique=True,
                      nullable=False)  # email address

    password = db.Column(db.Text, nullable=False)

    first_name = db.Column(db.String(40), nullable=False)

    last_name = db.Column(db.String(40), nullable=False)

    active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())

    updated_at = db.Column(
        db.TIMESTAMP, default=db.func.now(), onupdate=db.func.now())

    fs_uniquifier = db.Column(
        db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy='dynamic'))

    bookings = db.relationship('Booking', backref='users')

    company = db.relationship(
        'Company', secondary='user_company', backref=db.backref('users', lazy='dynamic'))


class Role(db.Model, RoleMixin):
    """Database model for role records"""

    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(50), nullable=False)

    description = db.Column(db.Text, nullable=False)

    # permissions = db.relationship(
    #     'Permission', secondary='role_permissions', backref=db.backref('roles', lazy='dynamic'))


class User_Role(db.Model):
    """Manages the many to many relationship between users and roles"""

    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete="CASCADE"), nullable=False)

    role_id = db.Column(db. Integer, db.ForeignKey(
        'roles.id', ondelete="CASCADE"), nullable=False)


# class Permission(db.Model):  Not Implemented
#     """Manages available permissions"""

#     __tablename__ = 'permissions'

#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)

#     name = db.Column(db.String(75), nullable=False)

#     description = db.Column(db.Text, nullable=False)


# class Role_Permission(db.Model): Not Implemented
#     """Manages the many to many relationship between roles and permissions"""

#     __tablename__ = 'role_permissions'

#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)

#     role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

#     permission_id = db.Column(db.Integer, db.ForeignKey(
#         'permissions.id'), nullable=False)
