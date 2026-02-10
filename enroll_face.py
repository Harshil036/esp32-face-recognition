import face_recognition
import mysql.connector
import pickle
import sys

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="face_recognition_db"
    )

def enroll_person(name, image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        print("No face found ❌")
        return

    encoding = pickle.dumps(encodings[0])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO persons (name) VALUES (%s)", (name,))
    person_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO face_encodings (person_id, encoding) VALUES (%s, %s)",
        (person_id, encoding)
    )

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Face enrolled successfully for {name} ✅")

if __name__ == "__main__":
    # Example usage
    # python enroll_face.py Alice alice.jpg
    name = sys.argv[1]
    image_path = sys.argv[2]
    enroll_person(name, image_path)
