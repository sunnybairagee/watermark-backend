from flask import Flask, request, jsonify, make_response
import os

app = Flask(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 🔥 GLOBAL CORS (MOST IMPORTANT)
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
def home():
    return "Backend running OK"

from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp",
    "mp4", "mov", "webm"
}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload-file", methods=["POST", "OPTIONS"])
def upload_file():

    # preflight
    if request.method == "OPTIONS":
        return make_response("", 200)

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)

    file.save(save_path)

    return jsonify({
        "status": "uploaded",
        "file_name": filename,
        "file_path": save_path
    }), 200


@app.route("/process", methods=["POST", "OPTIONS"])
def process_coordinates():

    # 🔥 PRE-FLIGHT HANDLER
    if request.method == "OPTIONS":
        return make_response("", 200)

    data = request.get_json(silent=True)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
