import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="kisanuser",
    password="123456",
    database="kisanvision360"
)

cursor = db.cursor()
