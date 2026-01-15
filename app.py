from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


@app.route("/")
def home():
    return "Backend running OK"


# 🔥 MAIN ENDPOINT (frontend yahin hit karega)
@app.route("/process", methods=["POST"])
def process_coordinates():
    data = request.get_json()

    # 1️⃣ Basic validation
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    file_name = data.get("file_name")
    file_type = data.get("file_type")
    coordinates = data.get("coordinates")

    if not file_name or not file_type or not coordinates:
        return jsonify({"error": "Missing fields"}), 400

    if not isinstance(coordinates, list):
        return jsonify({"error": "Coordinates must be list"}), 400

    # 2️⃣ Debug print (Render logs)
    print("FILE:", file_name)
    print("TYPE:", file_type)
    print("COORDS:", coordinates)

    # 3️⃣ Check file exists (important)
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        return jsonify({
            "error": "File not found on server",
            "expected_path": file_path
        }), 404

    # 4️⃣ TEMP: processing placeholder
    # (yahin baad me OpenCV / FFmpeg logic aayega)

    return jsonify({
        "status": "received",
        "file_name": file_name,
        "file_type": file_type,
        "boxes_count": len(coordinates),
        "message": "Coordinates received successfully"
    })
