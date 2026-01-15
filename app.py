from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/": {"origins": ""}})

UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


@app.route("/")
def home():
    return "Backend running OK"


# 🔥 MAIN ENDPOINT (frontend yahin hit karega)
@app.route("/process", methods=["POST", "OPTIONS"])
def process_coordinates():

    # 🔥 Preflight request handle
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    file_name = data.get("file_name")
    file_type = data.get("file_type")
    coordinates = data.get("coordinates")

    if not file_name or not file_type or not coordinates:
        return jsonify({"error": "Missing fields"}), 400

    print("FILE:", file_name)
    print("TYPE:", file_type)
    print("COORDS:", coordinates)

    return jsonify({
        "status": "received",
        "file_name": file_name,
        "file_type": file_type,
        "boxes_count": len(coordinates)
    }), 200
