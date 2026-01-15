import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "Backend is running successfully"

@app.route("/test-upload-folder", methods=["GET"])
def test_upload_folder():
    return {
        "status": "ok",
        "upload_folder": app.config["UPLOAD_FOLDER"],
        "exists": os.path.exists(app.config["UPLOAD_FOLDER"])
    }

# ---------- Helper: file type detect ----------
def detect_file_type(filename):
    image_ext = ["jpg", "jpeg", "png", "webp"]
    video_ext = ["mp4", "mov", "avi", "mkv", "webm"]

    ext = filename.lower().split(".")[-1]

    if ext in image_ext:
        return "image"
    elif ext in video_ext:
        return "video"
    else:
        return "unknown"

# ---------- API ----------
@app.route("/remove-watermark", methods=["POST"])
def receive_coordinates():
    data = request.get_json()

    # ---- frontend se expected ----
    file_name = data.get("file_name")
    coordinates = data.get("coordinates")  # list of boxes

    if not file_name or not coordinates:
        return jsonify({
            "status": "error",
            "message": "file_name or coordinates missing"
        }), 400

    file_type = detect_file_type(file_name)

    # ---- response for alert box ----
    return jsonify({
        "status": "success",
        "file_name": file_name,
        "file_type": file_type,
        "total_boxes": len(coordinates),
        "coordinates_received": coordinates
    })

# @app.route("/remove-watermark", methods=["POST"])
# def remove_watermark():
#     data = request.get_json()
#     return jsonify({
#         "Status": "Ok",
#         "Coordinates": data
#     })
    # return jsonify({
    #     "status": "ok",
    #     "message": "Test watermark removal successful"
    # })
