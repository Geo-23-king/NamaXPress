from flask import Flask, render_template, redirect, url_for, request, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, func, desc
from flask_socketio import SocketIO
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime, date
from forms import BookingForm, Namakwa_Users, DriverSignupForm,TOWNS
from booking import Booking
from werkzeug.security import generate_password_hash, check_password_hash


# --------------------------
# Initialize App & DB
# --------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///namax.db"

socketio = SocketIO(app)

# Base model for SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)


# --------------------------
# Database Models
# --------------------------
class Namakwaland(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_name: Mapped[str] = mapped_column(String(250), nullable=False)
    pickup: Mapped[str] = mapped_column(Integer, nullable=True)
    dropoff: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())


class NamakwaUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


    def __repr__(self):
        return f"<NamakwaUsers {self.name}>"


class RiderBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    pickup = db.Column(db.String(100))
    dropoff = db.Column(db.String(100))
    seats = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, default=date.today)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=True)
    pickup = db.Column(db.String(100))
    dropoff = db.Column(db.String(100))
    seats = db.Column(db.Integer)
    is_available = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



# Create all tables
with app.app_context():
    db.create_all()


# --------------------------
# Global Variables
# --------------------------
online_users = 0
connected_users = {}  # Mapping of connected users to Socket.IO session IDs

# --------------------------
# Test Data Function
# --------------------------
def create_test_data():

    # Create test users if they don't exist
    if not NamakwaUsers.query.filter_by(name="Rider1").first():
        rider = NamakwaUsers(name="Rider1", password=generate_password_hash("Pass123"))
        driver = NamakwaUsers(name="Driver1", password=generate_password_hash("Pass123"))
        db.session.add_all([rider, driver])
        db.session.commit()

    # Create a booking for Rider1 if it doesn't exist
    if not Namakwaland.query.filter_by(user_name="Rider1", dropoff="Nababeep").first():
        booking = Namakwaland(user_name="Rider1", pickup="Steinkopf", dropoff="Nababeep", status="Pending")
        db.session.add(booking)
        db.session.commit()


# --------------------------
# Routes: Home & Signup
# --------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    session["first_time"] = True
    next_page = request.args.get('next')
    if "user_id" in session:
        return redirect(next_page or url_for("namax"))

    user = Namakwa_Users()
    if user.validate_on_submit():
        new_name = user.name.data.strip()
        password = user.password.data.strip()

        # Validate password
        if len(password) < 4:
            flash("Wagwoord moet minstens 4 karakters wees.", "danger")
            return redirect(url_for("signup"))

        existing_user = NamakwaUsers.query.filter_by(name=new_name).first()

        if existing_user:
            if check_password_hash(existing_user.password, password):
                session.permanent = True
                session["user_id"] = existing_user.id
                session["user_name"] = existing_user.name

                session["show_intro"] = True   # <-- ADD THIS

                flash(f"Awe, {existing_user.name}! Jy is klaar deel van Nama X Press 👋", "success")
                return redirect(next_page or url_for("namax"))
            else:
                flash("Oeps! Verkeerde wagwoord. Probeer asseblief weer.", "danger")
                return redirect(url_for("signup"))
        else:
            hashed_pw = generate_password_hash(password)
            new_user = NamakwaUsers(name=new_name, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()

            session.permanent = True
            session["user_id"] = new_user.id
            session["user_name"] = new_user.name

            session["show_intro"] = True

            flash(f"Welkom by Nama X Press, {new_name}! 🚀 Jy is suksesvol geregistreer.", "success")

            return redirect(next_page or url_for("namax"))

    return render_template("signup.html", user=user)


@app.route("/clear_intro", methods=["POST"])
def clear_intro():
    session["show_intro"] = False
    return "", 204


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signup"))

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    user_name = session.get("user_name", "Anonymous")

    if request.method == "POST":
        msg = request.form.get("message").strip()

        if msg:
            new_feedback = Feedback(user_name=user_name, message=msg)
            db.session.add(new_feedback)
            db.session.commit()
            flash("Thanks for your feedback! 😊", "success")
            return redirect(url_for("feedback"))

        flash("Please write something first.", "danger")

    feedback_list = Feedback.query.order_by(desc(Feedback.timestamp)).all()
    return render_template("feedback.html", feedback_list=feedback_list)




# --------------------------
# Routes: Booking
# --------------------------
@app.route("/booking", methods=['GET', 'POST'])
def namax():
    form = BookingForm()
    user_name = session.get("user_name")

    if not user_name:
        flash("Jy moet eers aanmeld om bestuurder te word.", "warning")
        return redirect(url_for("signup", next=url_for('be_a_driver')))

    user_bookings = Namakwaland.query.filter_by(user_name=user_name).order_by(desc(Namakwaland.timestamp)).all()
    show_button = bool(user_bookings)

    # Check if user already booked today
    booking_today = Namakwaland.query.filter(
        Namakwaland.user_name == user_name,
        func.date(Namakwaland.timestamp) == date.today()
    ).first()

    if booking_today:
        flash("Jy het reeds vandag ’n rit bespreek.", "warning")
        formatted_time = booking_today.timestamp.strftime("%H:%M:%S")
        return render_template(
            "booking.html",
            form=form,
            tyd=formatted_time,
            information=[booking_today],
            show_button=True,
            form_submitted=True,
            user_name=user_name
        )

    # Handle new booking
    if form.validate_on_submit():
        pickup = form.pickup.data
        dropoff = form.dropoff.data

        if pickup == dropoff:
            flash("Pickup en Drop-off kan nie dieselfde wees nie!", "danger")
            return render_template(
                "booking.html",
                form=form,
                tyd=None,
                information=[],
                show_button=show_button,
                form_submitted=False,
                user_name=user_name
            )

        new_booking = Namakwaland(user_name=user_name, pickup=pickup, dropoff=dropoff, status="Pending")
        db.session.add(new_booking)
        db.session.commit()

        flash("Booking successful!", "success")
        user_bookings = Namakwaland.query.filter_by(user_name=user_name).order_by(desc(Namakwaland.timestamp)).all()
        show_button = bool(user_bookings)

        formatted_time = new_booking.timestamp.strftime("%H:%M:%S")
        return render_template(
            "booking.html",
            form=form,
            tyd=formatted_time,
            information=[new_booking],
            show_button=show_button,
            form_submitted=True,
            user_name=user_name
        )

    return render_template(
        "booking.html",
        form=form,
        tyd=None,
        information=[],
        show_button=show_button,
        form_submitted=False,
        user_name=user_name
    )


# --------------------------
# Routes: Driver Signup & Info
# --------------------------
@app.route("/be_a_driver", methods=["GET", "POST"])
def be_a_driver():
    if "user_name" not in session:
        flash("Jy moet eers aanmeld om 'n bestuurder te word.", "danger")
        return redirect(url_for("signup"))

    user_name = session["user_name"]
    form = DriverSignupForm()
    driver = Driver.query.filter_by(user_name=user_name).first()
    show_riders_button = bool(driver)

    bookings = Namakwaland.query.order_by(desc(Namakwaland.timestamp)).all()

    def normalize_list(main_val, extras):
        """Return deduped list with main_val first, max length 5."""
        vals = []
        if main_val and str(main_val).strip():
            vals.append(str(main_val).strip())
        for v in extras:
            if v and str(v).strip() and str(v).strip() not in vals:
                vals.append(str(v).strip())
        return vals[:5]

    if request.method == "POST":
        main_pickup = request.form.get("pickup") or (form.pickup.data if form.pickup.data else "")
        main_dropoff = request.form.get("dropoff") or (form.dropoff.data if form.dropoff.data else "")
        extra_pickups = request.form.getlist("pickup[]")
        extra_dropoffs = request.form.getlist("dropoff[]")

        pickups_list = normalize_list(main_pickup, extra_pickups)
        dropoffs_list = normalize_list(main_dropoff, extra_dropoffs)

        try:
            seats_val = int(request.form.get("seats") or (form.seats.data if form.seats.data else 0))
        except Exception:
            seats_val = 0

        if not pickups_list or not dropoffs_list:
            flash("Kies asseblief ten minste een afhaal- en een aflaai-plek.", "danger")
            return render_template(
                "be_a_driver.html",
                user_name=user_name,
                form=form,
                driver=driver,
                show_riders_button=show_riders_button,
                bookings=bookings,
                TOWNS=TOWNS
            )

        pickups_csv = ",".join(pickups_list)
        dropoffs_csv = ",".join(dropoffs_list)

        if driver:
            driver.pickup = pickups_csv
            driver.dropoff = dropoffs_csv
            driver.seats = seats_val
            driver.is_available = True
            driver.timestamp = datetime.utcnow()
        else:
            driver = Driver(
                user_name=user_name,
                pickup=pickups_csv,
                dropoff=dropoffs_csv,
                seats=seats_val,
                is_available=True
            )
            db.session.add(driver)

        db.session.commit()
        flash("Jy is nou beskikbaar as bestuurder!", "success")
        return redirect(url_for("be_a_driver"))

    return render_template(
        "be_a_driver.html",
        user_name=user_name,
        form=form,
        driver=driver,
        show_riders_button=show_riders_button,
        bookings=bookings,
        TOWNS=TOWNS
    )


@app.route("/my_driver_bookings")
def my_driver_bookings():
    user_name = session.get("user_name")
    if not user_name:
        flash("Jy moet eers aanmeld om jou bestuurder besprekings te sien.", "danger")
        return redirect(url_for("signup"))

    # Fetch driver booking from database for the logged-in user
    driver = Driver.query.filter_by(user_name=user_name).first()

    return render_template(
        "my_driver_bookings.html",
        driver=driver,  # pass driver directly
        user_name=user_name
    )


@app.route("/delete_driver_booking/<int:booking_id>", methods=["POST"])
def delete_driver_booking(booking_id):
    user_name = session.get("user_name")
    if not user_name:
        flash("Jy moet eers aanmeld.", "danger")
        return redirect(url_for("signup"))

    driver = Driver.query.get_or_404(booking_id)
    if driver.user_name != user_name:
        flash("Jy kan net jou eie besprekings verwyder.", "danger")
        return redirect(url_for("my_driver_bookings"))

    db.session.delete(driver)
    db.session.commit()
    flash("Driver booking deleted successfully.", "success")
    return redirect(url_for("my_driver_bookings"))


# --------------------------
# Routes: View Riders & Drivers
# --------------------------
@app.route("/riders_today")
def riders_today():
    pickup = request.args.get("pickup")
    dropoff = request.args.get("dropoff")

    if not pickup or not dropoff:
        flash("Geen ritinligting beskikbaar nie.", "warning")
        return redirect(url_for("be_a_driver"))

    # Correct query using func.date
    riders = Namakwaland.query.filter(
        Namakwaland.pickup == pickup,
        Namakwaland.dropoff == dropoff,
        func.date(Namakwaland.timestamp) == date.today()
    ).all()

    return render_template("riders_today.html", riders=riders, pickup=pickup, dropoff=dropoff)


@app.route("/drivers_today")
def drivers_today():
    user_name = session.get("user_name")
    if not user_name:
        flash("Jy moet eers aanmeld om bestuurders te sien.", "danger")
        return redirect(url_for("signup"))

    # Fetch all drivers available today (exclude current user)
    drivers = Driver.query.filter(
        Driver.is_available == True,
        Driver.user_name != user_name,
        func.date(Driver.timestamp) == date.today()
    ).all()

    if not drivers:
        flash("Geen bestuurders beskikbaar vandag nie.", "info")

    return render_template("drivers_today.html", drivers=drivers, user_name=user_name)

# --------------------------
# Routes: My Bookings
# --------------------------
@app.route("/my_bookings")
def my_bookings():
    user_name = request.args.get('user_name') or session.get("user_name")
    if not user_name:
        flash("Jy moet eers aanmeld om jou besprekings te sien.", "danger")
        return redirect(url_for("signup"))

    user_bookings = Namakwaland.query.filter_by(user_name=user_name).order_by(desc(Namakwaland.timestamp)).all()
    return render_template("my_bookings.html", show_drivers_button=True, bookings=user_bookings, user_name=user_name)


@app.route("/delete_booking/<int:booking_id>", methods=["POST"])
def delete_booking(booking_id):
    booking = Namakwaland.query.get(booking_id)
    if booking:
        db.session.delete(booking)
        db.session.commit()
        flash("Booking deleted successfully!", "success")
    else:
        flash("Booking not found.", "danger")
    return redirect(url_for("my_bookings", user_name=session.get("user_name")))


# --------------------------
# Socket.IO: Real-time Users & Messaging
# --------------------------
@socketio.on("connect")
def handle_connect():
    global online_users
    online_users += 1
    session_name = session.get("user_name")
    if session_name:
        connected_users[session_name] = request.sid
    socketio.emit("update_users", {"count": online_users}, to=None)


@socketio.on("disconnect")
def handle_disconnect():
    global online_users
    online_users -= 1 if online_users > 0 else 0
    session_name = session.get("user_name")
    if session_name and session_name in connected_users:
        connected_users.pop(session_name)
    socketio.emit("update_users", {"count": online_users}, to=None)


@socketio.on("private_message")
def handle_private_message(data):
    sender = session.get("user_name")
    recipient = data.get("to")
    message = data.get("message")

    if not sender or not recipient or not message:
        return

    # Save message in database
    chat_message = ChatMessage(sender=sender, recipient=recipient, message=message)
    db.session.add(chat_message)
    db.session.commit()

    # Emit message to recipient if online
    if recipient in connected_users:
        socketio.emit("private_message", {
            "from": sender,
            "message": message,
            "id": chat_message.id
        }, to=connected_users[recipient])

    # Emit message back to sender so it appears instantly
    socketio.emit("private_message", {
        "from": sender,
        "message": message,
        "id": chat_message.id
    }, to=request.sid)

@app.route("/chat/<driver_name>/<rider_name>")
def chat(driver_name, rider_name):
    user_name = session.get("user_name")
    if not user_name:
        flash("Jy moet eers aanmeld om te kan gesels.", "danger")
        return redirect(url_for("signup"))

    # Fetch all messages between the driver and rider
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender == driver_name) & (ChatMessage.recipient == rider_name)) |
        ((ChatMessage.sender == rider_name) & (ChatMessage.recipient == driver_name))
    ).order_by(ChatMessage.timestamp).all()

    return render_template(
        "chat.html",
        messages=messages,
        user_name=user_name,
        chatting_with=driver_name if user_name == rider_name else rider_name
    )

@app.route("/delete_message/<int:msg_id>", methods=["POST"])
def delete_message(msg_id):
    message = ChatMessage.query.get(msg_id)
    current_user = session.get("user_name")

    if message and message.sender == current_user:
        db.session.delete(message)
        db.session.commit()
        flash("Message deleted!", "success")
    else:
        flash("You can only delete your own messages.", "danger")
    return redirect(request.referrer or url_for("home"))



# --------------------------
# Run App
# --------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_test_data()
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, allow_unsafe_werkzeug=True)