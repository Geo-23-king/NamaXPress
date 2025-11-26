from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,SelectField,PasswordField,IntegerField
from wtforms.validators import DataRequired,ValidationError,Length,NumberRange

# List of supported towns
TOWNS = [
    "Garies","Steinkopf","Vioolsdrif","Nababeep","Kleinzee","Port Nolloth","Okiep",
    "Bulletrap","Aggeneys","Kamieskroon","Bergsig","Carolusberg","Pella",
    "Springbok","Concordia(Dorpie)","Komaggas","Buffelsrivier","Alexanderbaai",
    "Lekkersing","Eksteenfontein","Pofadder","Bergsig","Matjieskloof","Hondeklipbaai","Koingnaas"
]

class BookingForm(FlaskForm):
    pickup = SelectField(
        'Pickup Location',
        choices=[("", "Pickup Location")] + [(town, town) for town in TOWNS],
        validators=[DataRequired(message="Please select a pickup location")]
    )
    dropoff = SelectField(
        'Drop-off Location',
        choices=[("", "Drop-off Location")] + [(town, town) for town in TOWNS],
        validators=[DataRequired(message="Please select a drop-off location")]
    )
    submit = SubmitField('Book Ride')


class Namakwa_Users(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()], render_kw={"placeholder": "Sit jou naam in.."})
    password = StringField('Pickup Location', validators=[DataRequired()], render_kw={"placeholder": "NamaX Password..."})
    accepted = SubmitField("Log In Masekind")

class DriverSignupForm(FlaskForm):
    pickup = SelectField(
        "Pickup Town",
        choices=[(town, town) for town in TOWNS],
        validators=[DataRequired()]
    )
    dropoff = SelectField(
        "Dropoff Town",
        choices=[(town, town) for town in TOWNS],
        validators=[DataRequired()]
    )
    seats = IntegerField(
        "Available Seats",
        validators=[DataRequired(), NumberRange(min=1, max=10)],
        render_kw={"placeholder": "How many seats?"}
    )
    submit = SubmitField("Be a Driver")