
import sqlite3

db = sqlite3.connect(
    "instance/kisanvision360.db"
)

tables = db.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables:")
print(tables)

db.close()
