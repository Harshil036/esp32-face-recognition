from flask import Flask, request, jsonify
import mysql.connector
import face_recognition
import pickle
import numpy as np

app = Flask(__name__)

# ---- CONFIG ----
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456789",
    "database": "face_recognition_db"
}

SYSTEM_MODE = "IDLE"  # IDLE | RECOGNITION | ENROLLMENT
CURRENT_EVENT_ID = None


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)




@app.route("/set_mode", methods=["POST"])
def set_mode():
    global SYSTEM_MODE
    mode = request.json.get("mode")

    if mode not in ["IDLE", "RECOGNITION", "ENROLLMENT"]:
        return jsonify({"error": "Invalid mode"}), 400

    SYSTEM_MODE = mode
    return jsonify({"status": "ok", "mode": SYSTEM_MODE})





@app.route("/enroll", methods=["POST"])
def enroll():
    name = request.form.get("name")
    team = request.form.get("team")
    image_file = request.files.get("image")

    if not name or not team or not image_file:
        return jsonify({"error": "Missing data"}), 400

    image = face_recognition.load_image_file(image_file)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        return jsonify({"error": "No face detected"}), 400

    encoding_blob = pickle.dumps(encodings[0])

    conn = get_connection()
    cursor = conn.cursor()

    # Check if person exists
    cursor.execute("SELECT id FROM persons WHERE name=%s", (name,))
    row = cursor.fetchone()

    if row:
        person_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO persons (name, team) VALUES (%s, %s)",
            (name, team)
        )
        person_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO face_encodings (person_id, encoding) VALUES (%s, %s)",
        (person_id, encoding_blob)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "Face enrolled", "name": name, "team": team})






@app.route("/recognize", methods=["POST"])
def recognize():
    global SYSTEM_MODE, CURRENT_EVENT_ID

    if SYSTEM_MODE != "RECOGNITION":
        return jsonify({"error": "System not in recognition mode"}), 403

    image_file = request.files.get("image")
    if not image_file:
        return jsonify({"error": "No image"}), 400

    image = face_recognition.load_image_file(image_file)
    unknown_encodings = face_recognition.face_encodings(image)

    if not unknown_encodings:
        return jsonify({"result": "No face detected"})

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.name, f.encoding
        FROM persons p
        JOIN face_encodings f ON p.id = f.person_id
    """)

    known_ids = []
    known_names = []
    known_encodings = []

    for pid, name, enc in cursor.fetchall():
        known_ids.append(pid)
        known_names.append(name)
        known_encodings.append(pickle.loads(enc))

    results = []

    for unknown in unknown_encodings:
        distances = face_recognition.face_distance(known_encodings, unknown)
        best = np.argmin(distances)

        if distances[best] < 0.5:
            person_id = known_ids[best]
            name = known_names[best]

            if CURRENT_EVENT_ID:
                cursor.execute("""
                    INSERT IGNORE INTO attendance (event_id, person_id)
                    VALUES (%s, %s)
                """, (CURRENT_EVENT_ID, person_id))
                conn.commit()

            results.append({"name": name})
        else:
            results.append({"name": "Unknown"})

    cursor.close()
    conn.close()

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
