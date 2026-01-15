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
