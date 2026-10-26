# IMPORTS

# Flask: the web framework
# render_template: displays an HTML page from the "templates" folder
# request: gives access to the data sent by a form
# redirect / url_for: send the user to another page
# flash: stores a short message to display on the next page
# session: remembers data about the user between pages (who is logged in)
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Flask-SQLAlchemy: an ORM (Object-Relational Mapper) 
# It lets us use the database with Python classes and objects instead of writing SQL queries
from flask_sqlalchemy import SQLAlchemy

# generate_password_hash: turns a password into a hash (registration)
# check_password_hash: checks if a typed password matches a saved hash (login)
from werkzeug.security import generate_password_hash, check_password_hash


# APP CONFIGURATION

app = Flask(__name__)

# Secret key used by Flask to sign data kept between pages
app.config["SECRET_KEY"] = "dev-secret-key"

# The database is SQLite: a single file called food.db
# Flask creates it automatically in the "instance" folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///food.db"

# "db" is the object we use for everything related to the database
db = SQLAlchemy(app)


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


# Creates the tables in the database if they do not exist yet
# app_context() is needed because the database is linked to the Flask app
with app.app_context():
    db.create_all()

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


# STARTING THE APP

# Runs only when we start the file with "python app.py"
# debug=True: shows detailed errors and restarts the server automatically
# when the code changes (for development only)
if __name__ == "__main__":
    app.run(debug=True)