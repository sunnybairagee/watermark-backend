app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running successfully"

@app.route("/remove-watermark", methods=["POST"])
def remove_watermark():
    return jsonify({
        "status": "ok",
        "message": "Test watermark removal successful"
    })

if __name__ == "__main__":
    app.run()
