"""Default tests always use a disposable database, never application data."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_directory = TemporaryDirectory(prefix='fac67-tests-')
_original_url = os.environ.get('DATABASE_URL')
_postgres_url = os.environ.get('FAC67_TEST_DATABASE_URL')


def new_postgres_engine():
    url = make_url(_postgres_url)
    if (url.drivername != 'postgresql+psycopg'
            or not (url.database or '').startswith('foodaid_fac67_test_')
            or url.host not in ('localhost', '127.0.0.1', '::1') or url.query):
        raise ValueError('Use a local disposable foodaid_fac67_test_ database without query options')
    engine = create_engine(url)
    schema = 'fac67_' + uuid4().hex
    with engine.begin() as connection:
        connection.execute(CreateSchema(schema))
    engine.dispose()
    return create_engine(url.update_query_dict({'options': f'-csearch_path={schema}'}))


if _postgres_url:
    _initial_engine = new_postgres_engine()
    os.environ['DATABASE_URL'] = _initial_engine.url.render_as_string(hide_password=False)
    _initial_engine.dispose()
else:
    os.environ['DATABASE_URL'] = f'sqlite:///{_directory.name}/test.db'
from app import app, db, User

if _original_url is None:
    os.environ.pop('DATABASE_URL', None)
else:
    os.environ['DATABASE_URL'] = _original_url


@pytest.fixture(autouse=True)
def database():
    app.config['TESTING'] = True
    with app.app_context():
        if _postgres_url:
            db.session.remove()
            db.engines[None].dispose()
            db.engines[None] = new_postgres_engine()
        db.create_all()
        yield db
        db.session.remove()
        if not _postgres_url:
            db.drop_all()


@pytest.fixture
def legacy_postgres_engine():
    if not _postgres_url:
        pytest.skip('Set FAC67_TEST_DATABASE_URL for PostgreSQL migration verification')
    engine = new_postgres_engine()
    yield engine
    engine.dispose()


@pytest.fixture
def client():
    return app.test_client()


@pytest.fixture
def donor(client, database):
    user = User(email='donor@example.org', password_hash='unused', role='donor')
    database.session.add(user)
    database.session.commit()
    with client.session_transaction() as session:
        session['user_id'] = user.id
        session['role'] = 'donor'
    return user.id
