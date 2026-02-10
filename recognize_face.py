import face_recognition
import mysql.connector
import pickle
import sys
import numpy as np

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="face_recognition_db"
    )

def load_known_faces():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.name, f.encoding
        FROM persons p
        JOIN face_encodings f ON p.id = f.person_id
    """)

    names = []
    encodings = []

    for name, encoding_blob in cursor.fetchall():
        names.append(name)
        encodings.append(pickle.loads(encoding_blob))

    cursor.close()
    conn.close()

    return names, encodings


def recognize(image_path):
    known_names, known_encodings = load_known_faces()

    if not known_encodings:
        print("No faces in database ❌")
        return

    image = face_recognition.load_image_file(image_path)
    unknown_encodings = face_recognition.face_encodings(image)

    if not unknown_encodings:
        print("No face detected ❌")
        return

    for i, unknown in enumerate(unknown_encodings, start=1):
        distances = face_recognition.face_distance(known_encodings, unknown)
        best_index = np.argmin(distances)

        print(f"Face {i} → Distance: {distances[best_index]:.3f}")

        if distances[best_index] < 0.5:
            print(f"Face {i}: Recognized as {known_names[best_index]} ✅")
        else:
            print(f"Face {i}: Unknown ❌")


if __name__ == "__main__":
    image_path = sys.argv[1]
    recognize(image_path)
