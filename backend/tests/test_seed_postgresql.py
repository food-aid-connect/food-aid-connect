"""Exercise the real reset CLI in an explicitly selected disposable database."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from seed import validate_demo_database


BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def postgres_environment():
    database_url = os.environ.get('FAC_SEED_TEST_DATABASE_URL')
    if not database_url:
        pytest.skip('Set FAC_SEED_TEST_DATABASE_URL to a disposable PostgreSQL seed test database')
    url = validate_demo_database(database_url)
    if not url.database.startswith('foodaid_seed_test'):
        pytest.fail('Integration tests only reset foodaid_seed_test databases')
    return dict(os.environ, DATABASE_URL=database_url)


def run_python(env, *args):
    result = subprocess.run([sys.executable, *args], cwd=BACKEND, env=env,
                            capture_output=True, text=True, timeout=60)
    return result


def test_postgresql_seed_reset_and_login(postgres_environment):
    env = postgres_environment
    # Running twice verifies that reset replaces old data rather than duplicating it.
    for _ in range(2):
        result = run_python(env, 'seed.py', '--reset-demo')
        assert result.returncode == 0, 'PostgreSQL seed command failed (credentials suppressed)'
        assert '4 available batches, 1 reserved batch' in result.stdout
    result = run_python(env, '-c', '''
from app import app, db, User, Batch
from seed import DEMO_PASSWORD
from werkzeug.security import check_password_hash
from sqlalchemy import select, func
with app.app_context():
    assert db.engine.dialect.name == "postgresql"
    assert db.engine.driver == "psycopg"
    assert db.session.scalar(select(func.current_database())).startswith("foodaid_seed_test")
    assert User.query.count() == 4
    assert User.query.filter_by(role="donor").count() == 2
    assert User.query.filter_by(role="charity").count() == 2
    assert Batch.query.count() == 5
    assert Batch.query.filter_by(status="available").count() == 4
    reserved = Batch.query.filter_by(status="reserved").one()
    assert db.session.get(User, reserved.charity_id).role == "charity"
    for user in User.query.all():
        assert check_password_hash(user.password_hash, DEMO_PASSWORD)
        with app.test_client() as client:
            response = client.post("/login", data={"email": user.email, "password": DEMO_PASSWORD})
            assert response.status_code == 302
            with client.session_transaction() as session:
                assert session["user_id"] == user.id
    db.session.add(User(email="preserve-me@example.org", role="donor", password_hash="sentinel"))
    db.session.commit()
''')
    assert result.returncode == 0, 'PostgreSQL data/login checks failed (credentials suppressed)'
    result = run_python(env, 'seed.py')
    assert result.returncode == 2
    result = run_python(env, '-c', '''
import seed
from app import app, User
with app.app_context():
    assert User.query.count() == 5
    assert User.query.filter_by(email="preserve-me@example.org").count() == 1
''')
    assert result.returncode == 0, 'Unconfirmed CLI/import changed existing data'
    assert run_python(env, 'seed.py', '--reset-demo').returncode == 0


def test_postgresql_available_api(postgres_environment):
    # Check availability before resetting anything. Do not implement FAC-46 here.
    result = run_python(postgres_environment, '-c', '''
from app import app
import sys
sys.exit(0 if any(rule.rule == "/api/batches" and "GET" in rule.methods
                 for rule in app.url_map.iter_rules()) else 42)
''')
    if result.returncode == 42:
        pytest.skip('FAC-46 acceptance blocked: PR #11 is not merged')
    assert result.returncode == 0
    assert run_python(postgres_environment, 'seed.py', '--reset-demo').returncode == 0
    result = run_python(postgres_environment, '-c', '''
from app import app
response = app.test_client().get("/api/batches?status=available")
assert response.status_code == 200
payload = response.get_json()
batches = payload if isinstance(payload, list) else payload["batches"]
assert len(batches) == 4
assert all(batch["status"] == "available" for batch in batches)
''')
    assert result.returncode == 0, 'Available-batch API acceptance failed'
