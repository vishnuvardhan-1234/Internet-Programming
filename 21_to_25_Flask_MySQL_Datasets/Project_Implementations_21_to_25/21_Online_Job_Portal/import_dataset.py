import csv, os, json
import mysql.connector
from pathlib import Path

DB = os.getenv("DB_NAME", "21onlinejobportal")
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST","localhost"),
    user=os.getenv("DB_USER","root"),
    password=os.getenv("DB_PASSWORD",""),
    database=DB
)
cur = conn.cursor()
data_dir = Path(__file__).parent / "data"

# Import users using Werkzeug-compatible password hashing.
from werkzeug.security import generate_password_hash
users_file = data_dir / "users.csv"
if users_file.exists():
    with users_file.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cur.execute("""INSERT IGNORE INTO users(name,email,role,password_hash)
                           VALUES(%s,%s,%s,%s)""",
                        (row["name"], row["email"], row["role"],
                         generate_password_hash(row["password"])))

# Import every domain CSV into the common records table.
for file in data_dir.glob("*.csv"):
    if file.name == "users.csv":
        continue
    with file.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vals = list(row.values())
            title = row.get("title") or row.get("business_name") or row.get("place_name") or row.get("hotel_name") or row.get("food_name") or row.get("bin_code") or row.get("name") or row.get("origin") or "Dataset record"
            location = row.get("location") or row.get("city") or row.get("area") or row.get("origin") or ""
            category = row.get("category") or row.get("service") or row.get("mode") or row.get("blood_group") or ""
            description = row.get("description") or json.dumps(row, ensure_ascii=False)
            contact = row.get("contact") or row.get("phone") or ""
            owner = row.get("director_email") or ""
            status = row.get("status") or row.get("approved") or row.get("available") or "active"
            cur.execute("""INSERT INTO records(record_type,title,category,location,description,contact,owner_email,status,extra_json)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (file.stem, title, category, location, description, contact, owner, status,
                         json.dumps(row, ensure_ascii=False)))
conn.commit()
cur.close()
conn.close()
print("CSV datasets imported successfully.")
