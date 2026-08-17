
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FOLDER = os.path.join(
    BASE_DIR,
    "instance"
)

os.makedirs(
    DB_FOLDER,
    exist_ok=True
)

DB_PATH = os.path.join(
    DB_FOLDER,
    "kisanvision360.db"
)

SQL_PATH = os.path.join(
    BASE_DIR,
    "database.sql"
)

db = sqlite3.connect(DB_PATH)

with open(SQL_PATH, "r", encoding="utf-8") as file:
    sql = file.read()

db.executescript(sql)

db.commit()
db.close()

print("Database created successfully.")
