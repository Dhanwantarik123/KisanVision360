import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="kisanuser",
        password="123456",
        database="kisanvision360"
    )

    print("Connected Successfully!")

except mysql.connector.Error as err:
    print(err)
