"""Keep all default tests away from the application's configured database."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_test_directory = TemporaryDirectory(prefix="fac-seed-tests-")
_original_url = os.environ.get("DATABASE_URL")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_directory.name}/tests.db"
from app import app, db

if _original_url is None:
    os.environ.pop("DATABASE_URL", None)
else:
    os.environ["DATABASE_URL"] = _original_url


@pytest.fixture
def database():
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()
