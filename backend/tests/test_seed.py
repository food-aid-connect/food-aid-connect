import os
from pathlib import Path
import subprocess
import sys

import pytest
from werkzeug.security import check_password_hash

from app import app, db, Batch, User
from seed import DEMO_ACCOUNTS, DEMO_PASSWORD, main, populate_demo_data, validate_demo_database


BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def database(isolated_database):
    # Reuse main's isolation/cleanup and only supply the context seed tests need.
    with app.app_context():
        yield db


def assert_demo_data(db):
    assert User.query.count() == 4
    assert User.query.filter_by(role="donor").count() == 2
    assert User.query.filter_by(role="charity").count() == 2
    assert Batch.query.count() == 5
    assert Batch.query.filter_by(status="available").count() == 4
    reserved = Batch.query.filter_by(status="reserved").one()
    assert db.session.get(User, reserved.charity_id).role == "charity"
    assert all(db.session.get(User, batch.donor_id).role == "donor" for batch in Batch.query.all())
    assert all(batch.charity_id is None for batch in Batch.query.filter_by(status="available"))
    assert all(batch.title and batch.quantity and batch.pickup_date for batch in Batch.query.all())
    hashes = []
    for user in User.query.all():
        assert user.password_hash != DEMO_PASSWORD
        assert check_password_hash(user.password_hash, DEMO_PASSWORD)
        hashes.append(user.password_hash)
    assert len(set(hashes)) == 4


def test_seed_counts_relationships_and_passwords(database):
    populate_demo_data(database, User, Batch)
    assert_demo_data(database)


@pytest.mark.parametrize("email, role", DEMO_ACCOUNTS)
def test_demo_accounts_can_log_in(database, email, role):
    populate_demo_data(database, User, Batch)
    with app.test_client() as client:
        response = client.post('/login', data={'email': email, 'password': DEMO_PASSWORD})
        assert response.status_code == 302
        with client.session_transaction() as session:
            assert session['email'] == email
            assert session['role'] == role


def test_no_confirmation_preserves_existing_data(database):
    populate_demo_data(database, User, Batch)
    with pytest.raises(SystemExit) as error:
        main([])
    assert error.value.code == 2
    assert_demo_data(database)


def test_application_database_refused_even_with_confirmation(database, monkeypatch):
    populate_demo_data(database, User, Batch)
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://localhost/foodaid')
    with pytest.raises(SystemExit) as error:
        main(['--reset-demo'])
    assert error.value.code == 2
    assert_demo_data(database)


@pytest.mark.parametrize('name', ['foodaid_demo', 'foodaid_seed_test',
                                  'foodaid_seed_test_' + 'a' * 32])
def test_disposable_database_names_allowed(name):
    assert validate_demo_database(f'postgresql+psycopg://localhost/{name}').database == name


@pytest.mark.parametrize("url", [None, "invalid", "sqlite:///food.db",
    "postgresql+psycopg://localhost/foodaid", "postgresql+psycopg://localhost/production",
    "postgresql+psycopg://remote.example.org/foodaid_demo",
    "postgresql+psycopg:///foodaid_demo",
    "postgresql+psycopg://localhost/foodaid_demo?dbname=foodaid",
    "postgresql+psycopg://localhost/foodaid_demo?options=-csearch_path=public"])
def test_unsafe_database_rejected(url):
    with pytest.raises(ValueError):
        validate_demo_database(url)


@pytest.mark.parametrize("variable", ["APP_ENV", "FLASK_ENV", "ENVIRONMENT", "ENV"])
def test_production_environment_rejected(monkeypatch, variable):
    monkeypatch.setenv(variable, "production")
    with pytest.raises(ValueError, match="production"):
        validate_demo_database("postgresql+psycopg://localhost/foodaid_demo")


def test_import_and_rejected_cli_do_not_load_app():
    env = dict(os.environ, DATABASE_URL="not-a-valid-database-url")
    result = subprocess.run([sys.executable, '-c',
        'import sys; import seed; assert "app" not in sys.modules'],
        cwd=BACKEND, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for args in ([], ['--help'], ['--reset-demo']):
        result = subprocess.run([sys.executable, 'seed.py', *args], cwd=BACKEND,
                                env=env, capture_output=True, text=True)
        assert result.returncode == (0 if args == ['--help'] else 2)
        assert 'Traceback' not in result.stderr


def test_available_api_acceptance(database):
    populate_demo_data(database, User, Batch)
    response = app.test_client().get('/api/batches?status=available')
    assert response.status_code == 200
    payload = response.get_json()
    batches = payload if isinstance(payload, list) else payload['batches']
    assert len(batches) == 4
    assert all(batch['status'] == 'available' for batch in batches)


def test_demo_charity_sees_four_batches(database):
    populate_demo_data(database, User, Batch)
    with app.test_client() as client:
        client.post('/login', data={'email': 'charity.community@example.org', 'password': DEMO_PASSWORD})
        response = client.get('/batches')
        assert response.status_code == 200
        assert response.get_data(as_text=True).count('<article>') == 4
        assert response.get_data(as_text=True).count('>Reserve</button>') == 4
