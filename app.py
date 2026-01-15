from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running successfully"

@app.route("/remove-watermark", methods=["POST"])
def remove_watermark():
    return jsonify({
        "status": "ok",
        "message": "Test watermark removal successful"
    })
