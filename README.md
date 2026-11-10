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

## macOS setup

Install Python and PostgreSQL 17. With Homebrew, PostgreSQL can be installed
and started with:

```bash
brew install postgresql@17
brew services start postgresql@17
```

Ensure PostgreSQL's CLI tools are on your PATH, then create the application
database if it does not already exist:

```bash
createdb --username=YOUR_DB_USER foodaid
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
export DATABASE_URL='postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid'
python backend/app.py
```

## Windows setup (PowerShell)

Install Python and PostgreSQL 17 using their Windows installers. Start the
PostgreSQL service through Windows Services. Ensure Python and PostgreSQL's
CLI tools are on your PATH, then create the application database if it does
not already exist:

```powershell
createdb --username=YOUR_DB_USER foodaid
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
$env:DATABASE_URL = 'postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid'
python backend/app.py
```

## Application and API

Open http://127.0.0.1:5000/ for the application.
API documentation (Swagger): http://127.0.0.1:5000/docs

The application reads `DATABASE_URL` from the environment and creates missing
tables on startup. If the variable is unset, it falls back to a local SQLite
file. Browse available batches at `/batches`; logged-in charities can reserve
them. `GET /api/batches` supports `status=available` (the default) and
`status=reserved`. `POST /api/batches/<batch_id>/reserve` atomically reserves
an available batch for one charity.

## Tests

Use the activated virtual environment from either setup above.

### SQLite

Tests use a temporary SQLite database regardless of `DATABASE_URL` when
`FAC_TEST_POSTGRES_URL` is unset.

macOS:

```bash
unset FAC_TEST_POSTGRES_URL
python -m pytest backend/tests -q
```

Windows PowerShell:

```powershell
Remove-Item Env:FAC_TEST_POSTGRES_URL -ErrorAction SilentlyContinue
python -m pytest backend/tests -q
```

The PostgreSQL-only connection check is skipped in this mode.

### PostgreSQL

Create a separate test database if needed:

```bash
createdb --username=YOUR_DB_USER foodaid_test
```

macOS:

```bash
export FAC_TEST_POSTGRES_URL='postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid_test'
python -m pytest backend/tests -q
```

Windows PowerShell:

```powershell
$env:FAC_TEST_POSTGRES_URL = 'postgresql+psycopg://YOUR_DB_USER:YOUR_URL_ENCODED_PASSWORD@localhost:5432/foodaid_test'
python -m pytest backend/tests -q
```

The test database user needs permission to create schemas. Tests create
randomly named `fac_test_...` schemas with fresh tables for every test,
including concurrent reservation attempts. Application tables are not used
or reset. Test schemas are retained rather than deleted.

GitHub Actions runs both SQLite and PostgreSQL suites. Its PostgreSQL service
and credentials are disposable and used only within the CI job.
