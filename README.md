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

## Demo seed data (FAC-56 / FAC-64)

**Warning: `--reset-demo` deletes all existing application tables and data in
its target database**, then creates fresh tables and demo records. Use only a
disposable local database. Never point this script at application or production
data. It always refuses the existing `foodaid` database, even with the reset flag.
Importing `seed` or running it without `--reset-demo` does not reset anything.

Start PostgreSQL (on Apple Silicon with Homebrew) and create a separate database
using your local PostgreSQL role:

```bash
/opt/homebrew/bin/brew services start postgresql@17
/opt/homebrew/opt/postgresql@17/bin/createdb -h localhost -U <local-admin-role> \
  --owner=<application-role> foodaid_demo
```

If `foodaid_demo` already exists, keep it; do not recreate it. Its owner must
have permission to create and drop its application tables. Install the backend
dependencies into your virtual environment as described above. Configure
`DATABASE_URL` in your shell or your Git-ignored `.env` using this format:

```text
postgresql+psycopg://<application-role>:<URL-encoded-password>@localhost:5432/foodaid_demo
```

Keep credentials out of tracked files. If using the local `.env`, load it with
`source .env` from the repository root, then select `foodaid_demo` explicitly.
To reuse the credentials in an existing `DATABASE_URL` without printing them:

```bash
export DATABASE_URL="$(.venv/bin/python -c 'import os; from sqlalchemy.engine import make_url; print(make_url(os.environ["DATABASE_URL"]).set(database="foodaid_demo").render_as_string(hide_password=False))')"
cd backend
../.venv/bin/python seed.py --reset-demo
```

The script requires an explicit `postgresql+psycopg` URL with a loopback host
(`localhost`, `127.0.0.1`, or `::1`) and database name `foodaid_demo` or
`foodaid_seed_test` (optionally suffixed with `_` and a 32-character hex UUID).
URL query parameters are refused to prevent connection overrides. It also
refuses `prod`/`production` in `APP_ENV`, `FLASK_ENV`, `ENVIRONMENT`, or `ENV`.
No SQLite fallback is allowed for the seed command. No schema migration is
performed: this is a destructive demo reset, not an upgrade tool.

All four demo accounts use password **`demo123`**, stored as independently
salted secure password hashes:

| Email | Role |
|---|---|
| donor.bakery@example.org | donor |
| donor.market@example.org | donor |
| charity.community@example.org | charity |
| charity.shelter@example.org | charity |

The script creates five batches with pickup dates tomorrow: four available
and one reserved by the community charity. To verify from `backend/`, using
the same demo `DATABASE_URL`:

```bash
../.venv/bin/python -c 'from app import app, Batch; ctx = app.app_context(); ctx.push(); print("Available batches:", Batch.query.filter_by(status="available").count()); ctx.pop()'
```

Expected output: `Available batches: 4`. FAC-46's `GET /api/batches` endpoint
is not yet on `main` (PR #11 is open). Its acceptance check is skipped until
that endpoint is merged; it is not implemented by this seed change.

### Seed tests

From the repository root:

```bash
.venv/bin/python -m pytest -q
```

Default tests use an isolated temporary SQLite database, regardless of your
application `DATABASE_URL`. For PostgreSQL integration, create another disposable
database named `foodaid_seed_test`, owned by your test role. Set
`FAC_SEED_TEST_DATABASE_URL` to its `postgresql+psycopg://` URL and run the same
command. Integration tests **reset that database** with the seed command,
validate counts, relationships, hashed passwords, login, repeated resets, and
preservation without the reset flag. They never reset `foodaid`. PostgreSQL
checks are explicitly skipped when this variable is absent; the available-batch
API acceptance checks are skipped while FAC-46 is unavailable.
