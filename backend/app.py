# IMPORTS

# render_template: displays an HTML page from the "templates" folder
# request: gives access to the data sent by a form
# redirect / url_for: send the user to another page
# flash: stores a short message to display on the next page
# session: remembers data about the user between pages (who is logged in)
from flask import render_template, request, redirect, url_for, flash, session

# Flask-SQLAlchemy: an ORM (Object-Relational Mapper)
# It lets us use the database with Python classes and objects instead of writing SQL queries
from flask_sqlalchemy import SQLAlchemy

# generate_password_hash: turns a password into a hash (registration)
# check_password_hash: checks if a typed password matches a saved hash (login)
from werkzeug.security import generate_password_hash, check_password_hash

# os: lets us read environment variables (here, DATABASE_URL)
import os

# APIFlask also builds the Swagger/OpenAPI documentation.
from apiflask import APIFlask, Schema, abort
from apiflask.fields import Float, Integer, String, Email
from apiflask.validators import Length, OneOf
from marshmallow import ValidationError
from batch_details import BatchCreateSchema, BatchDetailsSchema, CATEGORIES

# ---------------------------------------------------------------------------------------------------
# SCHEMAS
class ReservationSchema(Schema):
    message = String(required=True)
    batch_id = Integer(required=True)
    status = String(required=True)
    charity_id = Integer(required=True)

class UserRegisterSchema(Schema):
    email = Email(required=True)
    password = String(required=True, validate=Length(min=6))
    role = String(required=True, validate=OneOf(["donor", "charity"]))

class UserLoginSchema(Schema):
    email = Email(required=True)
    password = String(required=True)

class UserOutSchema(Schema):
    id = Integer(required=True)
    email = Email(required=True)
    role = String(required=True)


# ---------------------------------------------------------------------------------------------------
# APP CONFIGURATION

app = APIFlask(__name__, title="Food-aid Connect API", version="0.1")

# Secret key used by Flask to sign data kept between pages
app.config["SECRET_KEY"] = "dev-secret-key"

# The database URL is read from the DATABASE_URL environment variable
# (PostgreSQL, no password stored in the code).
# If the variable is not set, we fall back to a local SQLite file.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///food.db"
)

# "db" is the object we use for everything related to the database
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------------------------------
# DATABASE TABLES

# Each class is a table and each db.Column is a column of that table
class User(db.Model):
    # Unique number for each user, created automatically (1, 2...)
    id = db.Column(db.Integer, primary_key=True)
    # unique=True: two accounts cannot have the same email
    # nullable=False: this field cannot be empty
    email = db.Column(db.String(120), unique=True, nullable=False)
    # We store the hash of the password, never the password itself
    password_hash = db.Column(db.String(256), nullable=False)
    # The type of user: "donor" or "charity"
    role = db.Column(db.String(20), nullable=False)

# A Batch represents surplus food posted by a donor
class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Information entered by the donor
    title = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    pickup_date = db.Column(db.String(20), nullable=False)

    # Nullable details preserve legacy batches and demo seed records.
    category = db.Column(db.String(80), nullable=True)
    quantity_kg = db.Column(db.Numeric(10, 3), nullable=True)
    use_by_date = db.Column(db.Date, nullable=True)
    pickup_address = db.Column(db.String(255), nullable=True)
    pickup_start = db.Column(db.Time, nullable=True)
    pickup_end = db.Column(db.Time, nullable=True)

    # A new batch is available by default
    status = db.Column(db.String(20), nullable=False, default="available")

    # The donor who posted the batch
    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # No charity has reserved the batch yet
    charity_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )


# Creates the tables in the database if they do not exist yet
# app_context() is needed because the database is linked to the Flask app
with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------------------------------
# ROUTES (each page of the website)
# Home page, at the address "/"
@app.route("/")
def home():
    return render_template("index.html")

# Registration page, at the address "/register"
# GET  = the user opens the page : we show the form
# POST = the user submits the form : we create the account
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Read the values typed in the form
        # The names ("email", "password", "role") must match the
        # name="..." attributes in register.html
        email = request.form["email"].strip()   # strip() to remove extra spaces
        password = request.form["password"]
        role = request.form["role"]

        # Check 1: every field is filled in and the role is valid
        if not email or not password or role not in ("donor", "charity"):
            flash("Please fill in all fields.")
            return render_template("register.html")

        # Check 2: the email is not already used by another account
        # filter_by(...).first() returns the first matching user, or None
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.")
            return render_template("register.html")


        # Create the new user, with a hashed password
        user = User(email=email,
                    password_hash=generate_password_hash(password),
                    role=role)
        db.session.add(user)    # prepare the new row
        db.session.commit()     # save it for good in the database

        flash("Account created. You can now log in.")

        # After registration, the user goes to the login page
        return redirect(url_for("login"))

    # GET request: just display the empty form
    return render_template("register.html")


# Login page, at the address "/login"
# GET  = the user opens the page : we show the form
# POST = the user submits the form : we check the email and password
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        # Look for the user with this email (None if it does not exist)
        user = User.query.filter_by(email=email).first()

        # check_password_hash hashes the typed password and compares it with the hash saved in the database.
        # We show the same message if the email or the password is wrong
        if user is None or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.")
            return render_template("login.html")

        # The login is correct: we remember the user in the session
        # The session is kept by the browser in a cookie signed with the SECRET_KEY, so it cannot be modified by the user
        session["user_id"] = user.id
        session["email"] = user.email
        session["role"] = user.role

        flash("You are logged in.")
        return redirect(url_for("home"))

    # GET request: just display the empty form
    return render_template("login.html")


# Logout, at the address "/logout".
# There is no page: we empty the session and go back to the home page
@app.route("/logout")
def logout():
    session.clear()   # forget everything about the logged-in user
    flash("You are logged out.")
    return redirect(url_for("home"))


@app.post("/api/register")
@app.input(UserRegisterSchema, location="json")
@app.output(UserOutSchema, status_code=201)
@app.doc(summary="Register a new account", tags=["Users"], responses={409: "This email is already registered"})
def api_register(json_data):
    email = json_data["email"]
    if User.query.filter_by(email=email).first():
        abort(409, message="This email is already registered")

    # Create the User with the HASH of the password
    user = User(email=email, password_hash=generate_password_hash(json_data["password"]), role=json_data["role"])

    db.session.add(user)
    db.session.commit()

    return user


@app.post("/api/login")
@app.input(UserLoginSchema, location="json")
@app.output(UserOutSchema)
@app.doc(summary="Log in", tags=["Users"], responses={401: "Invalid email or password."})
def api_login(json_data):
    email = json_data["email"].strip()
    password = json_data["password"]

    # Look for the user with this email (None if it does not exist)
    user = User.query.filter_by(email=email).first()

    # check_password_hash hashes the typed password and compares it with the hash saved in the database.
    # If the user does not exist OR the password is wrong
    if user is None or not check_password_hash(user.password_hash, password):
        abort(401, message="Invalid email or password.")

    # Remember the user in the session (user_id, email, role)
    session["user_id"] = user.id
    session["email"] = user.email
    session["role"] = user.role

    return user


@app.post("/api/logout")
@app.output({}, status_code=204)
@app.doc(summary="Empty the session", tags=["Users"])
def api_logout():
    # empty the session, return an empty response
    session.clear()
    return ""


@app.get("/api/me")
@app.output(UserOutSchema)
@app.doc(summary="Find the logged-in user", tags=["Users"], responses={401: "Login required"})
def api_me():
    # Find the logged-in user
    user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
    if user is None:
        abort(401, message="Please log in to see your account")
    return user


# Post a new surplus food batch
# GET: display the form
# POST: validate the form and save the batch
@app.route("/batches/new", methods=["GET", "POST"])
@app.input(BatchCreateSchema, location="form", validation=False)
@app.doc(responses={400: {
    "description": "Invalid or missing batch details",
    "content": {"text/html": {"schema": {"type": "string"}}}
}})
def new_batch(form_data):
    # Only logged-in users can post a batch
    if "user_id" not in session:
        flash("Please log in to post a batch.")
        return redirect(url_for("login"))

    # Only donors can post a batch (FAC-34)
    # session.get("role") returns None if the role is missing so this check never crashes
    if session.get("role") != "donor":
        flash("Only donors can post a batch.")
        return redirect(url_for("home"))

    if request.method == "POST":
        # Validate once; keep form errors as HTML with HTTP 400.
        schema = BatchCreateSchema()
        values = {key: value.strip() for key, value in request.form.items()
                  if key in schema.fields and value.strip()}
        try:
            details = schema.load(values)
        except ValidationError as error:
            for field, messages in error.messages.items():
                flash(f"{field}: {' '.join(messages)}")
            return render_template("new_batch.html", categories=CATEGORIES), 400

        # The existing column stores pickup dates as ISO strings.
        details["pickup_date"] = details["pickup_date"].isoformat()
        batch = Batch(donor_id=session["user_id"], **details)

        # Save the batch to the database
        db.session.add(batch)
        db.session.commit()

        flash("Batch posted.")
        return redirect(url_for("home"))

    # GET request: display the empty form
    return render_template("new_batch.html", categories=CATEGORIES)

# ---------------------------------------------------------------------------------------------------
# API SCHEMAS
# A schema describes the shape of the data sent by the API
class BatchOutSchema(BatchDetailsSchema):
    quantity_kg = Float(allow_none=True)
    id = Integer()
    title = String()
    quantity = String()
    pickup_date = String()
    status = String()
    donor_id = Integer()
    charity_id = Integer(allow_none = True)

@app.get("/batches")
def batches():
    available_batches = Batch.query.filter_by(status="available").order_by(Batch.id).all()
    user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
    return render_template("batches.html", batches=available_batches,
                           can_reserve=user is not None and user.role == "charity")


@app.post("/api/batches/<int:batch_id>/reserve")
@app.output(ReservationSchema)
@app.doc(summary="Reserve an available batch", tags=["Batches"], responses={
    401: "Login required", 403: "Only charities can reserve batches",
    404: "Batch not found", 409: "This batch is already reserved"
})
def reserve_batch(batch_id):
    user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
    if user is None:
        abort(401, message="Please log in to reserve a batch")
    if user.role != "charity":
        abort(403, message="Only charities can reserve batches")

    # The condition is checked by the database as part of the update, so only
    # one request can change an available batch to reserved.
    updated = Batch.query.filter_by(id=batch_id, status="available").update(
        {Batch.status: "reserved", Batch.charity_id: user.id},
        synchronize_session=False
    )
    if not updated:
        exists = db.session.get(Batch, batch_id) is not None
        db.session.rollback()
        if not exists:
            abort(404, message="Batch not found")
        abort(409, message="This batch is already reserved")

    charity_id = user.id
    db.session.commit()
    return {"message": "Batch reserved successfully", "batch_id": batch_id,
            "status": "reserved", "charity_id": charity_id}


class BatchQuerySchema(Schema):
    status = String(load_default="available", validate=OneOf(["available", "reserved"]))

# API ROUTES
@app.get("/api/batches")
@app.input(BatchQuerySchema, location="query")
@app.output(BatchOutSchema(many=True))
def list_batches(query_data):
    # query_data["status"] is already validated by BatchQuerySchema
    # Read the matching batches from the database (ORM, no SQL)
    batches = db.session.execute(
        db.select(Batch).filter_by(status = query_data['status'])
    ).scalars().all()
    return batches


# ---------------------------------------------------------------------------------------------------

# STARTING THE APP
# Runs only when we start the file with "python app.py"
# debug=True: shows detailed errors and restarts the server automatically
# when the code changes (for development only)
if __name__ == "__main__":
    app.run(debug=True)
