import sqlite3
import os


# =========================
# DATABASE PATH
# =========================

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


# =========================
# DATABASE CONNECTION
# =========================

db = sqlite3.connect(
    DB_PATH,
    check_same_thread=False
)


# =========================
# SQLITE CURSOR
# =========================

class SQLiteCursor:

    def __init__(self, connection):

        self.cursor = connection.cursor()


    def execute(self, query, params=()):

        query = query.replace("%s", "?")

        return self.cursor.execute(
            query,
            params
        )


    def fetchone(self):

        return self.cursor.fetchone()


    def fetchall(self):

        return self.cursor.fetchall()


    @property
    def lastrowid(self):

        return self.cursor.lastrowid


# =========================
# CURSOR
# =========================

cursor = SQLiteCursor(db)


def get_db():

    return cursor


# =========================
# TRANSACTIONS TABLE
# =========================

def create_transactions_table():

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            farmer_id INTEGER,

            description TEXT,

            amount REAL NOT NULL DEFAULT 0,

            type TEXT NOT NULL,

            date TEXT

        )
    """)

    db.commit()


# =========================
# CREATE TABLE
# =========================

create_transactions_table()