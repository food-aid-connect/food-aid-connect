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
   python3 -m pip install -r requirements.txt
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
   python3 app.py
   ```

6. Open http://127.0.0.1:5000/ in your browser.

The home page displays "Food-aid Connect". The tables are created automatically on first start.