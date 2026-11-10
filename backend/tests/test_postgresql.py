"""Explicit backend verification when PostgreSQL integration is requested."""
import os

import pytest
from sqlalchemy import func, inspect, select

from app import app, db


@pytest.mark.skipif(not os.environ.get("FAC_TEST_POSTGRES_URL"),
                    reason="Set FAC_TEST_POSTGRES_URL to run PostgreSQL integration")
def test_postgresql_connection_and_isolation():
    with app.app_context():
        assert db.engine.dialect.name == "postgresql"
        assert db.engine.driver == "psycopg"
        assert db.session.scalar(select(func.current_database()))
        schema = db.engine.get_execution_options()["schema_translate_map"][None]
        assert schema.startswith("fac_test_")
        assert set(inspect(db.engine).get_table_names(schema=schema)) == {"user", "batch"}
