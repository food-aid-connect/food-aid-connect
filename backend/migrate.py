"""FAC-67: add missing batch detail columns without replacing existing data."""
import argparse
import os

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Date, Numeric, String, Time, create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


DETAIL_COLUMNS = (
    ('category', String(80)),
    ('quantity_kg', Numeric(10, 3)),
    ('use_by_date', Date()),
    ('pickup_address', String(255)),
    ('pickup_start', Time()),
    ('pickup_end', Time()),
)


def upgrade(connection):
    """Apply the additive migration; callers own the transaction."""
    inspector = inspect(connection)
    if not inspector.has_table('batch'):
        raise ValueError('Batch table is missing. Initialize a fresh database with the app first.')
    columns = {column['name']: column for column in inspector.get_columns('batch')}
    # Check all existing detail columns before making any changes.
    for name, expected in DETAIL_COLUMNS:
        if name in columns:
            actual = columns[name]['type']
            if actual._type_affinity is not expected._type_affinity:
                raise ValueError(f'Existing batch.{name} has an incompatible type; review manually.')
            if isinstance(expected, Numeric) and (actual.precision, actual.scale) != (10, 3):
                raise ValueError(f'Existing batch.{name} has incompatible precision; review manually.')
            if isinstance(expected, String) and actual.length is not None and actual.length < expected.length:
                raise ValueError(f'Existing batch.{name} is too short; review manually.')
            if isinstance(expected, Time) and actual.timezone:
                raise ValueError(f'Existing batch.{name} uses timezone-aware time; review manually.')
            if not columns[name]['nullable']:
                raise ValueError(f'Existing batch.{name} is not nullable; review manually.')
    operations = Operations(MigrationContext.configure(connection))
    added = []
    for name, column_type in DETAIL_COLUMNS:
        if name not in columns:
            operations.add_column('batch', Column(name, column_type, nullable=True))
            added.append(name)
    return added


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        parser.error('DATABASE_URL must be explicitly configured; no SQLite fallback.')
    try:
        url = make_url(database_url)
        if url.drivername != 'postgresql+psycopg' or url.query:
            raise ValueError
    except (ArgumentError, ValueError, TypeError):
        parser.error('Use a postgresql+psycopg DATABASE_URL without query overrides.')
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            added = upgrade(connection)
    finally:
        engine.dispose()
    print('Added batch columns: ' + ', '.join(added) if added else 'Batch detail columns already present.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
