import cv2
import face_recognition
import pickle
import mysql.connector
import numpy as np

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="face_recognition_db"
    )

# Load encodings from DB
def load_known_faces():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT persons.name, face_encodings.encoding
        FROM face_encodings
        JOIN persons ON persons.id = face_encodings.person_id
    """)

    names = []
    encodings = []

    for name, encoding in cursor.fetchall():
        names.append(name)
        encodings.append(pickle.loads(encoding))

    cursor.close()
    conn.close()

    return names, encodings


known_names, known_encodings = load_known_faces()

# Start webcam
video = cv2.VideoCapture(0, cv2.CAP_DSHOW)


last_name = "Unknown"
stable_count = 0

process_this_frame = True

faces = []
encodings = []

while True:
    ret, frame = video.read()
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if process_this_frame:
        faces = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, faces)

    process_this_frame = not process_this_frame

    for (top, right, bottom, left), face_encoding in zip(faces, encodings):

        name = "Unknown"

        if len(known_encodings) > 0:
            distances = face_recognition.face_distance(
                known_encodings, face_encoding
            )
            best_index = np.argmin(distances)

            if distances[best_index] < 0.6:
                detected_name = known_names[best_index]

                if detected_name == last_name:
                    stable_count += 1
                else:
                    stable_count = 0

                last_name = detected_name

                if stable_count > 3:
                    name = detected_name
            else:
                stable_count = 0
                last_name = "Unknown"

        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.putText(frame, name, (left, top-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) == 27:  # ESC key
        break

video.release()
cv2.destroyAllWindows()
