from datetime import datetime
import numpy as np
import time
import cv2
import face_recognition
import pickle
import mysql.connector

# ==============================
# DATABASE
# ==============================
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="face_recognition_db"
    )

# ==============================
# SYSTEM STATE
# ==============================
recognition_running = False

def get_active_event():
    try:
        with open("current_event.txt", "r") as f:
            return int(f.read().strip())
    except:
        return None


# ==============================
# LOAD KNOWN FACES
# ==============================
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

# ==============================
# ATTENDANCE CONTROL
# ==============================
attendance_done = set()

def mark_attendance(name):
    event_id = get_active_event()
    if not event_id:
        return

    key = f"{event_id}_{name}"
    if key in attendance_done:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, team FROM persons WHERE name=%s",
        (name,)
    )
    result = cursor.fetchone()

    if result:
        person_id, team = result
        now_time = datetime.now().time()

        try:
            cursor.execute("""
                INSERT INTO attendance
                (event_id, person_id, name, team, time)
                VALUES (%s,%s,%s,%s,%s)
            """, (event_id, person_id, name, team, now_time))

            conn.commit()
            attendance_done.add(key)
            print(f"✅ Attendance marked for {name}")

        except Exception as e:
            print("DB Error:", e)

    cursor.close()
    conn.close()


# ==============================
# CAMERA SETUP
# ==============================
video = cv2.VideoCapture(0)

# ⭐ IMPORTANT — single resize factor
SCALE = 0.6

process_this_frame = True
face_locations = []
face_names = []


# ==============================
# FRAME GENERATOR
# ==============================
def generate_frames():
    global recognition_running, process_this_frame
    global face_locations, face_names

    while True:

        # -------------------------
        # IDLE MODE (camera OFF view)
        # -------------------------
        if not recognition_running:

            blank = np.ones((480, 640, 3), dtype=np.uint8) * 230

            cv2.putText(
                blank,
                "Recognition Stopped",
                (140, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            ret, buffer = cv2.imencode('.jpg', blank)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            time.sleep(0.2)
            continue

        # -------------------------
        # READ CAMERA
        # -------------------------
        success, frame = video.read()
        if not success:
            break

        small = cv2.resize(frame, (0, 0), fx=SCALE, fy=SCALE)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        # -------------------------
        # PROCESS EVERY 2ND FRAME
        # -------------------------
        if process_this_frame:

            face_locations = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, face_locations)

            face_names = []

            for encoding in encodings:

                matches = face_recognition.compare_faces(
                    known_encodings,
                    encoding,
                    tolerance=0.5
                )

                name = "Unknown"

                if True in matches:
                    index = matches.index(True)
                    name = known_names[index]
                    mark_attendance(name)

                face_names.append(name)

        process_this_frame = not process_this_frame

        # -------------------------
        # DRAW RECTANGLES (FIXED)
        # -------------------------
        for (top, right, bottom, left), name in zip(face_locations, face_names):

            # correct scaling back
            top = int(top / SCALE)
            right = int(right / SCALE)
            bottom = int(bottom / SCALE)
            left = int(left / SCALE)

            cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)

            cv2.putText(
                frame,
                name,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0,255,0),
                2
            )

        # -------------------------
        # SEND FRAME TO BROWSER
        # -------------------------
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
