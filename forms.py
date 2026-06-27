"""
forms.py
WTForms definitions for authentication, vehicle management, wallet,
reservations, and OCR upload. Centralized here for easy CSRF coverage
and input validation across the app.
"""

from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    FloatField,
    DateField,
    IntegerField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField(
        "Email", validators=[DataRequired(), Email(check_deliverability=False), Length(max=150)]
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class VehicleForm(FlaskForm):
    vehicle_number = StringField(
        "Vehicle Number",
        validators=[
            DataRequired(),
            Length(min=4, max=20),
            Regexp(r"^[A-Za-z0-9]+$", message="Use letters and numbers only, no spaces."),
        ],
    )
    owner_name = StringField("Owner Name", validators=[DataRequired(), Length(max=120)])
    vehicle_type = SelectField(
        "Vehicle Type",
        choices=[("Car", "Car"), ("Bike", "Bike"), ("Truck", "Truck"), ("Bus", "Bus")],
        validators=[DataRequired()],
    )
    registration_date = DateField("Registration Date", validators=[DataRequired()], default=date.today)
    insurance_expiry = DateField("Insurance Expiry", validators=[DataRequired()])
    puc_expiry = DateField("PUC Expiry", validators=[DataRequired()])
    submit = SubmitField("Save Vehicle")


class TopUpForm(FlaskForm):
    amount = FloatField("Amount (₹)", validators=[DataRequired(), NumberRange(min=1, max=100000)])
    submit = SubmitField("Add Funds")


class ReservationForm(FlaskForm):
    vehicle_id = SelectField("Vehicle", coerce=int, validators=[DataRequired()])
    slot_id = SelectField("Slot", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Reserve Slot")


class PlateUploadForm(FlaskForm):
    image = FileField(
        "Vehicle Image",
        validators=[FileRequired(), FileAllowed(["jpg", "jpeg", "png", "bmp"], "Images only!")],
    )
    submit = SubmitField("Detect Plate")


class ManualEntryForm(FlaskForm):
    vehicle_number = StringField("Vehicle Number", validators=[DataRequired(), Length(max=20)])
    slot_id = SelectField("Slot (leave blank for auto-allocate)", coerce=int, validators=[Optional()])
    submit = SubmitField("Record Entry")


class ManualExitForm(FlaskForm):
    vehicle_number = StringField("Vehicle Number", validators=[DataRequired(), Length(max=20)])
    submit = SubmitField("Record Exit")
