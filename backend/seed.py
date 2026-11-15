"""Reset an explicitly selected disposable local database with demo data."""
import argparse
from datetime import date, timedelta
import os
import re

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from werkzeug.security import generate_password_hash


DEMO_ACCOUNTS = (
    ("donor.bakery@example.org", "donor"),
    ("donor.market@example.org", "donor"),
    ("charity.community@example.org", "charity"),
    ("charity.shelter@example.org", "charity"),
)
DEMO_PASSWORD = "demo123"


def validate_demo_database(database_url):
    """Fail closed before loading app (which creates tables on import)."""
    for name in ("APP_ENV", "FLASK_ENV", "ENVIRONMENT", "ENV"):
        if os.environ.get(name, "").strip().lower() in ("prod", "production"):
            raise ValueError("Refusing to seed in a production environment.")
    if not database_url:
        raise ValueError("Set DATABASE_URL explicitly; SQLite fallback is not allowed.")
    try:
        url = make_url(database_url)
        allowed_name = re.fullmatch(
            r"foodaid_demo|foodaid_seed_test(?:_[a-f0-9]{32})?", url.database or ""
        )
        if (url.drivername != "postgresql+psycopg"
                or url.host not in ("localhost", "127.0.0.1", "::1")
                or not allowed_name or url.query):
            raise ValueError
    except (ArgumentError, ValueError, TypeError):
        raise ValueError(
            "Refusing reset: use postgresql+psycopg on localhost with database "
            "foodaid_demo or foodaid_seed_test (optionally suffixed with a UUID), "
            "without URL query parameters. The foodaid database is never allowed."
        ) from None
    return url


def populate_demo_data(db, User, Batch):
    """Insert the demo records into an empty database; does not delete data."""
    users = [User(email=email, role=role,
                  password_hash=generate_password_hash(DEMO_PASSWORD))
             for email, role in DEMO_ACCOUNTS]
    db.session.add_all(users)
    db.session.flush()
    tomorrow = date.today() + timedelta(days=1)
    examples = (
        ("Fresh sourdough bread", "20 loaves", 0, "available", None),
        ("Seasonal vegetables", "15 kg", 1, "available", None),
        ("Apples and pears", "10 kg", 1, "available", None),
        ("Wholegrain rolls", "40 rolls", 0, "available", None),
        ("Rice and lentils", "12 sealed 1 kg bags", 1, "reserved", users[2].id),
    )
    for title, quantity, donor, status, charity_id in examples:
        db.session.add(Batch(title=title, quantity=quantity,
                             pickup_date=tomorrow.isoformat(), status=status,
                             donor_id=users[donor].id, charity_id=charity_id))
    db.session.commit()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-demo", action="store_true",
                        help="DELETE all tables/data in the allowed demo database and seed it")
    args = parser.parse_args(argv)
    if not args.reset_demo:
        parser.error("--reset-demo is required; no database has been changed")
    try:
        url = validate_demo_database(os.environ.get("DATABASE_URL"))
    except ValueError as error:
        parser.error(str(error))

    # Deliberately lazy: importing seed or rejecting arguments never loads app.
    from app import app, db, User, Batch

    with app.app_context():
        if db.engine.url != url:
            parser.error("Application connection differs from DATABASE_URL; refusing reset")
        db.drop_all()
        db.create_all()
        populate_demo_data(db, User, Batch)
    print("Demo seed complete: 2 donors, 2 charities, 4 available batches, 1 reserved batch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
