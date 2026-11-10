"""Use a disposable database even when DATABASE_URL points at production."""
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_test_directory = TemporaryDirectory(prefix="fac-reservation-tests-")
_original_url = os.environ.get("DATABASE_URL")
_postgres_url = os.environ.get("FAC_TEST_POSTGRES_URL")
if _postgres_url:
    # Create a new schema before importing app: importing it calls create_all().
    # Never run tests against application tables, even if the URL names foodaid.
    _url = make_url(_postgres_url)
    if _url.drivername != "postgresql+psycopg":
        raise ValueError("FAC_TEST_POSTGRES_URL must use postgresql+psycopg")
    _schema = f"fac_test_{uuid4().hex}"
    _setup_engine = create_engine(_url)
    with _setup_engine.begin() as connection:
        connection.execute(CreateSchema(_schema))
    _setup_engine.dispose()
    _options = _url.query.get("options", "")
    _url = _url.update_query_dict({"options": f"{_options} -csearch_path={_schema}".strip()})
    os.environ["DATABASE_URL"] = _url.render_as_string(hide_password=False)
else:
    os.environ["DATABASE_URL"] = f"sqlite:///{_test_directory.name}/test.db"
from app import app, db, User, Batch

if _original_url is None:
    os.environ.pop("DATABASE_URL", None)
else:
    os.environ["DATABASE_URL"] = _original_url


@pytest.fixture(autouse=True)
def isolated_database():
    app.config["TESTING"] = True
    with app.app_context():
        if _postgres_url:
            # Each test gets fresh tables, including concurrent requests using
            # separate connections. Keep schemas afterwards; never delete data.
            schema = f"fac_test_{uuid4().hex}"
            with db.engine.begin() as connection:
                connection.execute(CreateSchema(schema))
            db.engine.update_execution_options(schema_translate_map={None: schema})
        else:
            db.drop_all()
        db.create_all()
    yield
    with app.app_context():
        db.session.remove()
        if not _postgres_url:
            db.drop_all()


@pytest.fixture
def client():
    return app.test_client()


@pytest.fixture
def records():
    with app.app_context():
        donor = User(email="donor@example.org", password_hash="unused", role="donor")
        charity = User(email="charity@example.org", password_hash="unused", role="charity")
        other = User(email="other@example.org", password_hash="unused", role="charity")
        db.session.add_all([donor, charity, other])
        db.session.flush()
        batch = Batch(title="Fresh bread", quantity="10 loaves", pickup_date="2026-11-11",
                      donor_id=donor.id)
        db.session.add(batch)
        db.session.commit()
        return {"donor": donor.id, "charity": charity.id, "other": other.id, "batch": batch.id}


@pytest.fixture
def sign_in():
    def login(client, user_id, role="charity"):
        with client.session_transaction() as session:
            session["user_id"] = user_id
            session["role"] = role
            session["email"] = "test@example.org"
    return login
