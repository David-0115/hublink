from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, EmailField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import InputRequired, Length, Email, Optional


class CustomSelectField(SelectField):
    def pre_validate(self, form):
        pass


class NavLocations(FlaskForm):
    """Form for navigation bar location selection"""

    loc = SelectField('location', choices=[])


class AppointmentForm(FlaskForm):

    company_id = SelectField("Company:", choices=[],
                             validators=[InputRequired()], render_kw={
        'class': 'form-control', 'id': 'company-select'})

    driver_id = CustomSelectField("Driver:", choices=[],
                                  render_kw={
        'class': 'form-control', 'id': 'driver-select'})

    delivery_only = BooleanField("Delivery Only?", default=False, render_kw={
        'id': 'delivery-only'
    })

    destination = SelectField("Destination:", choices=[], render_kw={
        'class': 'form-control', 'id': 'destination'})

    notes = TextAreaField("Notes:", validators=[Length(max=255)], render_kw={
        'class': 'form-control'})
