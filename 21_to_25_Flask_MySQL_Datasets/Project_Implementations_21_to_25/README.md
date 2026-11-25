# Flask + MySQL Project Bundle (Questions 21–25)

Each folder is an independent starter application. Each app uses Flask, MySQL and CSV seed datasets.

## Setup (Windows / VS Code)
1. Install Python 3.10+ and MySQL Server.
2. Create a virtual environment:
   `py -m venv .venv`
   `.venv\Scripts\activate`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Create a MySQL database and import the schema:
   `mysql -u root -p < schema.sql`
5. Set environment variables (PowerShell):
   `$env:DB_HOST='localhost'; $env:DB_USER='root'; $env:DB_PASSWORD='your_mysql_password'; $env:DB_NAME='project_database_name'`
6. Import CSV seed data:
   `python import_dataset.py`
7. Start:
   `python app.py`
8. Open `http://127.0.0.1:5000`

## Demo accounts
For each app, demo credentials are included in its `data/users.csv`. These are for local testing only. Change passwords and add password hashing before deployment.

## Important
- CSV datasets are sample/demo data, not real personal or medical records.
- The blood-bank inventory is illustrative. Always verify stock and compatibility with a licensed hospital/blood bank.
- The waste route and mechanic map links are starter features. Production routing needs a configured maps API key and validation.
- Never deploy with the demo passwords or Flask development server.
