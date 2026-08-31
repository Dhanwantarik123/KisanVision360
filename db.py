import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "instance"
)

DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "kisanvision360.db"
)

# Compatibility name
DB_PATH = DATABASE_PATH

os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)


def get_db():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def init_db():

    conn = get_db()

    sql_file = os.path.join(
        BASE_DIR,
        "database.sql"
    )

    if os.path.exists(sql_file):

        with open(
            sql_file,
            "r",
            encoding="utf-8"
        ) as file:

            sql_script = file.read()

        conn.executescript(
            sql_script
        )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            description TEXT,
            amount REAL NOT NULL DEFAULT 0,
            type TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def close_db(exception=None):
    pass


# Initialize database
try:
    init_db()
    print("DATABASE READY:", DATABASE_PATH)

except Exception as e:
    print("DATABASE ERROR:", repr(e))