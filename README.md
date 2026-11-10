# food-aid-connect
Web platform connecting food donors, charities and volunteers to redistribute surplus food - Software Engineering project

## Run the Flask Application

1. Clone the repository:
   ```bash
   git clone https://github.com/food-aid-connect/food-aid-connect.git
   cd food-aid-connect
   ```

2. Install PostgreSQL and create an empty database named `foodaid`.

3. Install the dependencies:
   ```bash
   python3 -m pip install -r backend/requirements.txt
   ```

4. Set the database connection URL (never commit your password).
   - PowerShell:
     ```powershell
     $env:DATABASE_URL = "postgresql+psycopg://postgres:<password>@localhost:5432/foodaid"
     ```
   - macOS / Linux:
     ```bash
     export DATABASE_URL="postgresql+psycopg://postgres:<password>@localhost:5432/foodaid"
     ```
   If `DATABASE_URL` is not set, the app falls back to a local SQLite file.

5. Start the Flask application:
   ```bash
   cd backend
   python3 app.py
   ```

6. Open http://127.0.0.1:5000/ in your browser.

The home page displays "Food-aid Connect". The tables are created automatically on first start.

API documentation (Swagger): http://127.0.0.1:5000/docs

## Full batch descriptions (FAC-67)

Batches now support six additional optional fields. Keeping them nullable
preserves legacy records, existing forms, and the pending FAC-56 seed script:

| Field | PostgreSQL type | Meaning |
|---|---|---|
| `category` | `VARCHAR(80)` | Food category |
| `quantity_kg` | `NUMERIC(10,3)` | Positive weight, up to 9999999.999 kg |
| `use_by_date` | `DATE` | Use-by date, today or later when submitted |
| `pickup_address` | `VARCHAR(255)` | Collection address |
| `pickup_start` | `TIME WITHOUT TIME ZONE` | Local pickup start on `pickup_date` |
| `pickup_end` | `TIME WITHOUT TIME ZONE` | Local pickup end on `pickup_date` |

The existing `/batches/new` form accepts these fields. Invalid details,
including a past use-by date, return HTTP 400 with an HTML error message.
Today/future dates are accepted; dates use the application server's local
calendar. If both pickup times are provided, the end must be after the start
on the same day. The original title, quantity, and pickup date remain required;
omitting the new fields remains supported.

`GET /api/batches` includes all six fields (null for older batches), with dates
and times serialized as ISO strings and `quantity_kg` as a JSON number. Existing
available/reserved filtering is unchanged. `/docs` documents both the form
input and batch response. No new batch-creation API URL is introduced.

### Migrate an existing PostgreSQL database

`db.create_all()` creates missing tables; **it does not add columns to existing
tables**. Before running this version against an existing database:

```bash
# From the repository root; .env must export the intended DATABASE_URL.
.venv/bin/python -m pip install -r backend/requirements.txt
source .env
.venv/bin/python backend/migrate.py
.venv/bin/python backend/app.py
```

`DATABASE_URL` must explicitly use `postgresql+psycopg`; the migration refuses
SQLite fallback and URL query overrides. Review the selected target before
running. The command does not import the app or run `create_all()`.

There was no migration framework in this project. `backend/migrate.py` is a
minimal additive migration runner using Alembic's SQLAlchemy operations. It
inspects the existing `batch` table, adds only missing nullable columns in one
PostgreSQL transaction, and leaves records, IDs, relationships, and existing
columns unchanged. Re-running it is safe and reports no changes. Incompatible
pre-existing detail columns cause it to stop for manual review rather than
changing their types or deleting data. It never drops tables or databases.
Run one migration process at a time. No destructive downgrade is provided.

For a fresh empty database, the app's existing initialization creates all model
tables with the six fields; no separate migration is needed. Applying this
migration to existing `foodaid` is an explicit deployment step, not something
that runs on application import.

### Tests

```bash
# Entire suite against isolated temporary SQLite; migration checks skip.
.venv/bin/python -m pytest -q
```

For the full suite on PostgreSQL, create a separate disposable local database
named `foodaid_fac67_test_<unique-suffix>`, owned by your test role. Set
`FAC67_TEST_DATABASE_URL` to its `postgresql+psycopg://` URL without query
parameters, then run the same command. The role needs schema-creation
permissions. Tests create fresh, uniquely named schemas for each test and
retain them; application tables are never reset. PostgreSQL migration tests
create legacy records in isolated schemas, run the migration repeatedly
(including the real CLI), verify data preservation, and query migrated records
through the API. Credentials belong in the shell or ignored `.env`, never in
tracked files.
