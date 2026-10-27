# IMPORTS

# Flask: the web framework.
# render_template: displays an HTML page from the "templates" folder.
# request: gives access to the data sent by a form.
# redirect / url_for: send the user to another page.
# flash: stores a short message to display on the next page.
from flask import Flask, render_template, request, redirect, url_for, flash

# Flask-SQLAlchemy: an ORM (Object-Relational Mapper). It lets us use the
# database with Python classes and objects instead of writing SQL queries.
from flask_sqlalchemy import SQLAlchemy

# Turns a password into a "hash": a scrambled version that cannot be
# turned back into the original password. We never store real passwords.
from werkzeug.security import generate_password_hash


# APP CONFIGURATION

app = Flask(__name__)

# Secret key used by Flask to sign data kept between pages
app.config["SECRET_KEY"] = "dev-secret-key"

# The database is SQLite: a single file called food.db
# Flask creates it automatically in the "instance" folder.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///food.db"

# "db" is the object we use for everything related to the database
db = SQLAlchemy(app)


# DATABASE TABLES

# Each class is a table; each db.Column is a column of that table.
class User(db.Model):
    # Unique number for each user, created automatically (1, 2...)
    id = db.Column(db.Integer, primary_key=True)
    # unique=True: two accounts cannot have the same email.
    # nullable=False: this field cannot be empty.
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
# Home page, at the address "/".
@app.route("/")
def home():
    return render_template("index.html")

# Registration page, at the address "/register".
# GET  = the user opens the page -> we show the form.
# POST = the user submits the form -> we create the account.
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Read the values typed in the form.
        # The names ("email", "password", "role") must match the
        # name="..." attributes in register.html.
        email = request.form["email"].strip()   # strip() to remove extra spaces
        password = request.form["password"]
        role = request.form["role"]

        # Check 1: every field is filled in and the role is valid
        if not email or not password or role not in ("donor", "charity"):
            flash("Please fill in all fields.")
            return render_template("register.html")

        # Check 2: the email is not already used by another account
        # filter_by(...).first() returns the first matching user, or None.
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.")
            return render_template("register.html")


        # Create the new user, with a hashed password.
        user = User(email=email,
                    password_hash=generate_password_hash(password),
                    role=role)
        db.session.add(user)    # prepare the new row
        db.session.commit()     # save it for good in the database

        flash("Account created. You can now log in.")

        # We go back to the home page
        return redirect(url_for("home"))

    # GET request: just display the empty form.
    return render_template("register.html")

# STARTING THE APP

# Runs only when we start the file with "python app.py".
# debug=True: shows detailed errors and restarts the server automatically
# when the code changes (for development only).
if __name__ == "__main__":
    app.run(debug=True)