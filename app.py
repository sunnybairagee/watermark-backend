from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Backend is running successfully"

@app.route("/remove-watermark", methods=["POST"])
def remove_watermark():
    data = request.get_json()
    return jsonify({
        "Status": "Ok",
        "Coordinates": data
    })
    # return jsonify({
    #     "status": "ok",
    #     "message": "Test watermark removal successful"
    # })
