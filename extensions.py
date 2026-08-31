from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class SQLiteCursor:

    def __init__(self, connection):
        self.connection = connection
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

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()