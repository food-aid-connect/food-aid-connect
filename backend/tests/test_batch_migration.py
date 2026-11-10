"""Migration tests use only fresh isolated PostgreSQL schemas."""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, inspect, select

from migrate import DETAIL_COLUMNS, upgrade


def legacy_tables(connection):
    metadata = MetaData()
    users = Table('user', metadata,
                  Column('id', Integer, primary_key=True),
                  Column('email', String(120), nullable=False, unique=True),
                  Column('password_hash', String(256), nullable=False),
                  Column('role', String(20), nullable=False))
    batches = Table('batch', metadata,
                    Column('id', Integer, primary_key=True),
                    Column('title', String(120), nullable=False),
                    Column('quantity', String(100), nullable=False),
                    Column('pickup_date', String(20), nullable=False),
                    Column('status', String(20), nullable=False),
                    Column('donor_id', Integer, ForeignKey('user.id'), nullable=False),
                    Column('charity_id', Integer, ForeignKey('user.id')))
    metadata.create_all(connection)
    connection.execute(users.insert(), [
        {'id': 1, 'email': 'donor@legacy.org', 'password_hash': 'preserve-hash', 'role': 'donor'},
        {'id': 2, 'email': 'charity@legacy.org', 'password_hash': 'preserve-charity', 'role': 'charity'}])
    connection.execute(batches.insert(), [
        {'id': 1, 'title': 'Legacy bread', 'quantity': '10 loaves', 'pickup_date': '2026-11-12',
         'status': 'available', 'donor_id': 1, 'charity_id': None},
        {'id': 2, 'title': 'Reserved rice', 'quantity': '5 kg', 'pickup_date': '2026-11-12',
         'status': 'reserved', 'donor_id': 1, 'charity_id': 2}])
    return users, batches


def test_postgresql_migration_preserves_records_and_is_repeatable(legacy_postgres_engine):
    engine = legacy_postgres_engine
    with engine.begin() as connection:
        users, batches = legacy_tables(connection)
        before_users = connection.execute(select(users).order_by(users.c.id)).all()
        before_batches = connection.execute(select(batches).order_by(batches.c.id)).all()
        assert set(upgrade(connection)) == {name for name, _ in DETAIL_COLUMNS}
        assert upgrade(connection) == []
        assert connection.execute(select(users).order_by(users.c.id)).all() == before_users
        assert connection.execute(select(batches).order_by(batches.c.id)).all() == before_batches
        columns = {column['name']: column for column in inspect(connection).get_columns('batch')}
        for name, _ in DETAIL_COLUMNS:
            assert columns[name]['nullable']
        reflected = Table('batch', MetaData(), autoload_with=connection)
        for row in connection.execute(select(reflected)).mappings():
            assert all(row[name] is None for name, _ in DETAIL_COLUMNS)
    # Verify migrated legacy records through the real application/API.
    env = dict(os.environ, DATABASE_URL=engine.url.render_as_string(hide_password=False))
    code = '''
from app import app
client = app.test_client()
available = client.get('/api/batches?status=available')
reserved = client.get('/api/batches?status=reserved')
assert available.status_code == reserved.status_code == 200
assert available.json[0]['title'] == 'Legacy bread'
assert reserved.json[0]['charity_id'] == 2
assert available.json[0]['use_by_date'] is None
'''
    result = subprocess.run([sys.executable, '-c', code], env=env,
                            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 0, 'Migrated legacy data API verification failed (credentials suppressed)'


def test_incompatible_existing_column_is_not_modified(legacy_postgres_engine):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    engine = legacy_postgres_engine
    with engine.begin() as connection:
        legacy_tables(connection)
        Operations(MigrationContext.configure(connection)).add_column('batch', Column('quantity_kg', String(30)))
        with pytest.raises(ValueError, match='incompatible type'):
            upgrade(connection)
        assert 'category' not in {column['name'] for column in inspect(connection).get_columns('batch')}


def test_postgresql_migration_cli(legacy_postgres_engine):
    engine = legacy_postgres_engine
    with engine.begin() as connection:
        legacy_tables(connection)
    env = dict(os.environ,
               DATABASE_URL=engine.url.set(query={}).render_as_string(hide_password=False),
               PGOPTIONS=engine.url.query['options'])
    for expected in ('Added batch columns:', 'Batch detail columns already present.'):
        result = subprocess.run([sys.executable, 'migrate.py'], env=env,
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        assert result.returncode == 0, 'Migration CLI failed (credentials suppressed)'
        assert expected in result.stdout
    with engine.connect() as connection:
        table = Table('batch', MetaData(), autoload_with=connection)
        rows = connection.execute(select(table).order_by(table.c.id)).mappings().all()
        assert [row['title'] for row in rows] == ['Legacy bread', 'Reserved rice']
        assert rows[1]['charity_id'] == 2
        assert all(row['quantity_kg'] is None for row in rows)
