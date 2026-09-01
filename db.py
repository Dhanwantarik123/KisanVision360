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

# Create instance folder
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


def add_missing_user_columns(conn):

    cursor = conn.cursor()

    # Check existing users columns
    cursor.execute(
        "PRAGMA table_info(users)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    # Add fullname if missing
    if "fullname" not in columns:

        cursor.execute(
            "ALTER TABLE users ADD COLUMN fullname TEXT"
        )

        print("DATABASE: fullname column added")

    # Add mobile if missing
    if "mobile" not in columns:

        cursor.execute(
            "ALTER TABLE users ADD COLUMN mobile TEXT"
        )

        print("DATABASE: mobile column added")


def init_db():

    conn = get_db()

    try:

        # =========================================
        # RUN database.sql
        # =========================================

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

        # =========================================
        # FIX USERS TABLE
        # =========================================

        add_missing_user_columns(conn)

        # =========================================
        # TRANSACTIONS TABLE
        # =========================================

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

        print(
            "DATABASE READY:",
            DATABASE_PATH
        )

    except Exception as e:

        conn.rollback()

        print(
            "DATABASE INIT ERROR:",
            repr(e)
        )

        raise

    finally:

        conn.close()


def close_db(exception=None):
    pass


# =========================================
# INITIALIZE DATABASE
# =========================================

try:

    init_db()

except Exception as e:

    print(
        "DATABASE ERROR:",
        repr(e)
    )