from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, EmailField, PasswordField, HiddenField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length, Email, Optional
from flask_security.forms import PasswordFormMixin
import typing as t


class RegistrationForm(FlaskForm):
    """User registration form"""

    email = EmailField('Email:',
                       validators=[InputRequired(), Email()])

    password = PasswordField('Password:', validators=[
                             InputRequired(), Length(min=8, max=40)])

    first_name = StringField('First Name:', validators=[
                             InputRequired(), Length(max=40)])

    last_name = StringField('Last Name:', validators=[
                            InputRequired(), Length(max=40)])

    phone_number = StringField('Mobile Number:', validators=[
                               InputRequired(), Length(min=10, max=10)])

    company = SelectField('Company affiliation:', choices=[],
                          validators=[InputRequired()])

    role = SelectField('What is your role?', choices=[
        ('', 'Select an option...'),
        ('Driver', 'Driver'),
        ('Dispatcher', 'Dispatcher'),
        ('Hub_Manager', 'Hub Manager'),
        ('Planner', 'Planning Team')
    ], validators=[InputRequired()])


class UserLoginForm(FlaskForm, PasswordFormMixin):
    """User Login Form"""

    email = EmailField('Email', validators=[InputRequired(), Email()], render_kw={
                       'class': 'form-control'})

    password = PasswordField('Password:', validators=[
        InputRequired(), Length(min=8, max=40)], render_kw={'class': 'form-control'})

    remember = BooleanField('Remember Me')

    submit = SubmitField('Log in', render_kw={
                         'class': 'btn btn-primary w-100'})

    requires_confirmation = False


class EditProfileForm(FlaskForm):
    """Form for user to edit profile."""

    email = HiddenField()

    first_name = StringField('First Name:', validators=[
                             Length(max=40)], render_kw={'class': 'form-control'})

    last_name = StringField('Last Name:', validators=[
                            Length(max=40)], render_kw={'class': 'form-control'})

    phone_number = StringField('Mobile Number:', validators=[Optional(),
                               Length(min=10, max=10)], render_kw={'class': 'form-control'})

    password = PasswordField('Current Password:', validators=[
        InputRequired(), Length(min=8, max=40)], render_kw={'class': 'form-control'})

    new_password = PasswordField('New Password:', validators=[
        Optional(), Length(min=8, max=40)], render_kw={'class': 'form-control', 'placeholder': 'Optional'})


# create driver
# create company
