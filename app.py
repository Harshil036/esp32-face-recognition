from flask import Flask, render_template, request, jsonify, Response
import mysql.connector
import face_recognition
import pickle
import camera_stream
from camera_stream import generate_frames, get_active_event

app = Flask(__name__)

# ---------- DATABASE ----------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456789",
    "database": "face_recognition_db"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ---------- PAGES ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/enroll_page")
def enroll_page():
    return render_template("enroll.html")


# ---------- VIDEO STREAM ----------
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------- START RECOGNITION ----------
@app.route('/start_recognition', methods=["POST"])
def start_recognition():

    if not get_active_event():
        return jsonify({"error": "Create event first!"})

    camera_stream.recognition_running = True
    return jsonify({"status": "Recognition Started"})


# ---------- STOP RECOGNITION ----------
@app.route("/stop_recognition", methods=["POST"])
def stop_recognition():

    import camera_stream
    camera_stream.recognition_running = False

    return jsonify({"status": "stopped"})




# ---------- CREATE EVENT ----------
@app.route('/create_event', methods=['POST'])
def create_event():

    data = request.get_json()
    event_name = data.get("event_name")

    if not event_name:
        return jsonify({"error": "Event name required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (event_name, event_date)
        VALUES (%s, NOW())
    """, (event_name,))

    event_id = cursor.lastrowid

    # Save active event
    with open("current_event.txt", "w") as f:
        f.write(str(event_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Event Created"})


# ---------- ENROLL FACE ----------
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

    cursor.execute("SELECT id FROM persons WHERE name=%s", (name,))
    row = cursor.fetchone()

    if row:
        person_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO persons (name, team) VALUES (%s,%s)",
            (name, team)
        )
        person_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO face_encodings (person_id, encoding) VALUES (%s,%s)",
        (person_id, encoding_blob)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": "Face Enrolled"})


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
