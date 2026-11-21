# Food Aid Connect

Web platform connecting food donors, charities, and volunteers to redistribute surplus food.

## Get the source

```bash
git clone https://github.com/food-aid-connect/food-aid-connect.git
cd food-aid-connect
```

Run the following commands from the repository root. Replace `YOUR_DB_USER`
and `YOUR_URL_ENCODED_PASSWORD` with your PostgreSQL connection details.
Never commit database credentials.

## Setup: macOS and Windows

Install Python and PostgreSQL 17. On macOS, use `brew install postgresql@17`
and `brew services start postgresql@17`. On Windows, use the installers and
start PostgreSQL through Windows Services. Add PostgreSQL's CLI tools to PATH.
Run these commands from the repository root:

| Step | macOS (Terminal) | Windows (PowerShell) |
|---|---|---|
| Create database (once) | `createdb --username=YOUR_DB_USER foodaid` | `createdb --username=YOUR_DB_USER foodaid` |
| Create virtual environment | `python3 -m venv .venv` | `py -3 -m venv .venv` |
| Activate environment | `source .venv/bin/activate` | `.\.venv\Scripts\Activate.ps1` |
| Install dependencies | `python -m pip install -r backend/requirements.txt` | `python -m pip install -r backend/requirements.txt` |
| Select database | `export DATABASE_URL='postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid'` | `$env:DATABASE_URL = 'postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid'` |
| Start application | `python backend/app.py` | `python backend/app.py` |

After activation, use `python` for all commands below. Set environment variables
in the shell; no `.env` loading is required.

## Application and API

Open http://127.0.0.1:5000/ for the application.
API documentation (Swagger): http://127.0.0.1:5000/docs

The application reads `DATABASE_URL` from the environment and creates missing
tables on startup. If the variable is unset, it falls back to a local SQLite
file. Browse available batches at `/batches`; logged-in charities can reserve
them. `GET /api/batches` supports `status=available` (the default) and
`status=reserved`. `POST /api/batches/<batch_id>/reserve` atomically reserves
an available batch for one charity.

## Full batch descriptions (FAC-67)

`POST /batches/new` accepts form-encoded data. `title`, `quantity`,
`pickup_date`, `quantity_kg`, and `use_by_date` are required. The weight must
be between 0.001 and 9999999.999 kg. Use-by must be today or later; pickup
must be a real date no later than use-by. Invalid submissions return HTTP 400
with HTML error messages. Dates use the application server's local calendar.

Category is an optional dropdown, validated on the server: Bread and bakery,
Fruit and vegetables, Canned and dry goods, Dairy, Prepared meals, or Other.
Collection address and local pickup start/end times are optional. If both
times are supplied, end must be after start; timezone offsets are rejected.

The six detail columns remain nullable for legacy records and demo seed data.
`GET /api/batches` returns those fields, including nulls for older records,
ISO date/time strings, and numeric `quantity_kg`. Available/reserved filtering
and reservation behavior are preserved. `/docs` and `/openapi.json` describe
the required creation fields and allowed category values.

### Recreate tables for local development

`db.create_all()` creates missing tables but does not update existing columns.
For an outdated local development database, stop the app, back up any data you
need, and verify that `DATABASE_URL` points to your disposable local database.
**Resetting tables deletes all existing users, batches, and reservations.**
Never run this against a shared or production database. There is no automatic
schema upgrade or data-preserving migration command.

With the environment activated, use the setup table above to explicitly select
the intended local database, then run from the repository root:

| Step | macOS (Terminal) | Windows (PowerShell) |
|---|---|---|
| Enter backend | `cd backend` | `cd backend` |
| Recreate application tables (deletes data) | `python -c "from app import app, db; ctx = app.app_context(); ctx.push(); db.drop_all(); db.create_all(); ctx.pop()"` | `python -c "from app import app, db; ctx = app.app_context(); ctx.push(); db.drop_all(); db.create_all(); ctx.pop()"` |
| Return to repository root | `cd ..` | `cd ..` |
| Start application | `python backend/app.py` | `python backend/app.py` |

A fresh empty database needs no reset: startup creates the tables automatically.

## Frontend Setup

The frontend is built with Vue 3, TypeScript, Vite, and Vue Router.

To install dependencies and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173/ in your browser.

The Vite development server proxies `/api` requests to the Flask backend at `http://127.0.0.1:5000`. Make sure the Flask backend is running when accessing API endpoints.

## Tests

Use the activated virtual environment from either setup above.

### SQLite

Tests use a temporary SQLite database regardless of `DATABASE_URL` when
`FAC_TEST_POSTGRES_URL` is unset.

| Step | macOS (Terminal) | Windows (PowerShell) |
|---|---|---|
| Clear PostgreSQL test selection | `unset FAC_TEST_POSTGRES_URL` | `Remove-Item Env:FAC_TEST_POSTGRES_URL -ErrorAction SilentlyContinue` |
| Run suite | `python -m pytest backend/tests -q` | `python -m pytest backend/tests -q` |

The PostgreSQL-only connection check is skipped in this mode.

### PostgreSQL

Create a separate test database if needed:

```bash
createdb --username=YOUR_DB_USER foodaid_test
```

| Step | macOS (Terminal) | Windows (PowerShell) |
|---|---|---|
| Select test database | `export FAC_TEST_POSTGRES_URL='postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid_test'` | `$env:FAC_TEST_POSTGRES_URL = 'postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid_test'` |
| Run suite | `python -m pytest backend/tests -q` | `python -m pytest backend/tests -q` |

The test database user needs permission to create schemas. Tests create
randomly named `fac_test_...` schemas with fresh tables for every test,
including concurrent reservation attempts. Application tables are not used
or reset. Test schemas are retained rather than deleted.

GitHub Actions runs both SQLite and PostgreSQL suites. Its PostgreSQL service
and credentials are disposable and used only within the CI job.

## Demo data (FAC-56 / FAC-64)

**Use a separate, disposable `foodaid_demo` database.** `--reset-demo` deletes
its existing application data and creates 2 donors, 2 charities, and 5 batches
(4 available, 1 reserved). The script refuses `foodaid`, remote databases, and
production settings, and never resets data on import or without the flag.

With the virtual environment activated and PostgreSQL running, create
`foodaid_demo` if it does not exist and select it explicitly:

| Step | macOS (Terminal) | Windows (PowerShell) |
|---|---|---|
| Create demo database (once) | `createdb --username=YOUR_DB_USER foodaid_demo` | `createdb --username=YOUR_DB_USER foodaid_demo` |
| Select demo database | `export DATABASE_URL='postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid_demo'` | `$env:DATABASE_URL = 'postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid_demo'` |
| Load demo data (deletes existing demo data) | `python backend/seed.py --reset-demo` | `python backend/seed.py --reset-demo` |
| Start application | `python backend/app.py` | `python backend/app.py` |

Keep the same demo `DATABASE_URL` when starting the app. All demo accounts use
password **`demo123`**, stored as securely salted hashes:

| Email | Role |
|---|---|
| donor.bakery@example.org | donor |
| donor.market@example.org | donor |
| charity.community@example.org | charity |
| charity.shelter@example.org | charity |

Log in as either demo charity and open `/batches`: you should see **4 available
batches**.

Seed tests run with the suite above. To include destructive seed-CLI integration
tests, configure `FAC_SEED_TEST_DATABASE_URL` for another disposable local
database named `foodaid_seed_test` (not `foodaid_demo` or `foodaid_test`). CI
creates this separate database and runs those checks alongside the PostgreSQL
reservation tests.
