from flask import Flask, jsonify, request, make_response
import os

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


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

    # Preflight request
    if request.method == "OPTIONS":
        return make_response("", 200)

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
