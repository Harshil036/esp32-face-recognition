import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="face_recognition_db"
    )

if __name__ == "__main__":
    try:
        conn = get_connection()
        print("MySQL connection successful ✅")
        conn.close()
    except Exception as e:
        print("MySQL connection failed ❌")
        print(e)
