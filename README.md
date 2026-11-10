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

## Local macOS PostgreSQL setup

On this development machine, PostgreSQL 17 is managed by Homebrew. The
application database is `foodaid`; integration tests use `foodaid_test`.
The local `fac_local` login role has no superuser, role creation, or database
creation privileges. Generated credentials are in the Git-ignored root `.env`
file, readable only by its owner. Do not commit or share this file.

From the repository root, start the application with:

```bash
/opt/homebrew/bin/brew services start postgresql@17
source .env
.venv/bin/python backend/app.py
```

The local `.env` exports both `DATABASE_URL` and `FAC_TEST_POSTGRES_URL` using
the `postgresql+psycopg` driver. The application reads `DATABASE_URL` from the
environment; it does not load `.env` itself. Homebrew's default local
authentication configuration is unchanged.

## Run tests

From the repository root, using the existing virtual environment:

```bash
.venv/bin/python -m pytest -q
```

By default, tests use a temporary SQLite database regardless of `DATABASE_URL`.
To run the full suite against PostgreSQL, set `FAC_TEST_POSTGRES_URL` to a
`postgresql+psycopg://` connection URL for a local test database, then run the
same command. Keep credentials in your shell environment, not in tracked files.
The PostgreSQL test role needs permission to create schemas in that database.

On this development machine, `source .env` before running pytest selects
PostgreSQL. Use `env -u FAC_TEST_POSTGRES_URL .venv/bin/python -m pytest -q` to
explicitly select the temporary SQLite database instead.

PostgreSQL tests create randomly named `fac_test_...` schemas and use fresh
tables for each test, including concurrent reservations. Existing application
tables are not used or reset. Test schemas are retained to avoid deleting data.
An additional PostgreSQL connection/isolation check is skipped in SQLite runs.
