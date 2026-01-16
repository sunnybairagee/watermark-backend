from flask_cors import CORS
from flask import Flask, request, jsonify, make_response, send_from_directory
from PIL import Image, ImageFilter
import json
import threading
import time
import os
import subprocess
import uuid
from werkzeug.middleware.proxy_fix import ProxyFix

JOBS_FILE = "jobs.json"
jobs_lock = threading.Lock()


def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    try:
        with open(JOBS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f)


# 🔥 app start hote hi jobs load kar lo
jobs = load_jobs()

app = Flask(__name__)
CORS(app, resources={r"/": {"origins": ""}})
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

PROCESSED_DIR = "processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)


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


# Mobile Processing Code ==============================

def get_video_duration_ms(video_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    duration_sec = float(result.stdout.decode().strip())
    return int(duration_sec * 1000)

def process_image_mobile(job_id, input_path, box, output_path):
    try:
        with jobs_lock:
            jobs[job_id]["progress"] = 10
            save_jobs(jobs)

        img = Image.open(input_path)
        x, y, w, h = box["x"], box["y"], box["w"], box["h"]

        with jobs_lock:
            jobs[job_id]["progress"] = 40
            save_jobs(jobs)

        region = img.crop((x, y, x + w, y + h))
        blurred = region.filter(ImageFilter.GaussianBlur(15))
        img.paste(blurred, (x, y))

        with jobs_lock:
            jobs[job_id]["progress"] = 80
            save_jobs(jobs)

        img.save(output_path, "JPEG")

        with jobs_lock:
            jobs[job_id]["progress"] = 100
            jobs[job_id]["status"] = "done"
            jobs[job_id]["output_file"] = os.path.basename(output_path)
            save_jobs(jobs)

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = str(e)
            save_jobs(jobs)

def process_video_mobile(job_id, file_path, box, output_path):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 0
        save_jobs(jobs)

        total_duration = get_video_duration_ms(file_path)
        save_jobs(jobs)

        x, y, w, h = box["x"], box["y"], box["w"], box["h"]
        save_jobs(jobs)

        cmd = [
            "ffmpeg", "-y",
            "-i", file_path,
            "-filter_complex",
            f"[0:v]split=2[base][tmp];"
            f"[tmp]crop={w}:{h}:{x}:{y},boxblur=10:2[blur];"
            f"[base][blur]overlay={x}:{y}",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-progress", "pipe:1",
            output_path
        ]
        save_jobs(jobs)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        save_jobs(jobs)

        for line in process.stdout:
            line = line.strip()
    
            if line.startswith("out_time_ms="):
                try:
                    out_ms = int(line.split("=")[1])
        
                    if total_duration > 0:
                        percent = min(int(out_ms * 100 / total_duration), 99)
        
                        with jobs_lock:
                            jobs[job_id]["progress"] = percent
                            save_jobs(jobs)
        
                except Exception:
                    pass  # ignore bad ffmpeg lines

        process.wait()
        save_jobs(jobs)

        if not os.path.exists(output_path):
            raise Exception("Output file not created")

        jobs[job_id]["progress"] = 100
        save_jobs(jobs)
        jobs[job_id]["status"] = "done"
        jobs[job_id]["output_file"] = os.path.basename(output_path)
        save_jobs(jobs)

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)

@app.route("/process-mobile", methods=["POST", "OPTIONS"])
def process_mobile():
    if request.method == "OPTIONS":
        return make_response("", 200)

    data = request.get_json()
    file_name = data.get("file_name")
    file_type = data.get("file_type")
    coordinates = data.get("coordinates")

    if not file_name or not coordinates:
        return jsonify({"error": "Invalid data"}), 400

    # 🔥 Mobile = single box only
    box = coordinates[0]

    input_path = os.path.join(UPLOAD_DIR, file_name)
    if file_type == "image":
        output_name = f"blurred_{uuid.uuid4().hex}.jpg"
    else:
        output_name = f"mobile_blur_{uuid.uuid4().hex}.mp4"
    # output_name = f"mobile_blur_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(PROCESSED_DIR, output_name)

    job_id = uuid.uuid4().hex

    with jobs_lock:
        jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "output_file": None,
            "created_at": time.time()
        }
        save_jobs(jobs)

    if file_type == "image":
        thread = threading.Thread(
            target=process_image_mobile,
            args=(job_id, input_path, box, output_path)
        )
    else:
        thread = threading.Thread(
            target=process_video_mobile,
            args=(job_id, input_path, box, output_path)
        )
    
    thread.start()

    return jsonify({
        "status": "started",
        "job_id": job_id
    }), 200

@app.route("/progress/<job_id>")
def get_progress(job_id):
    jobs = load_jobs()
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Invalid job id"}), 404
    return jsonify(job)

def cleanup_jobs(max_age=3600):  # 1 hour
    now = time.time()
    jobs = load_jobs()
    changed = False

    for jid in list(jobs.keys()):
        if now - jobs[jid].get("created_at", now) > max_age:
            del jobs[jid]
            changed = True

    if changed:
        save_jobs(jobs)

# Mobile Processing Code ==============================



@app.route("/process", methods=["POST", "OPTIONS"])
def process_coordinates():

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

    file_path = os.path.join(UPLOAD_DIR, file_name)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # 🔥 IMAGE BLUR LOGIC
    if file_type == "image":
        img = Image.open(file_path).convert("RGB")

        for box in coordinates:
            x = box["x"]
            y = box["y"]
            w = box["w"]
            h = box["h"]

            region = img.crop((x, y, x + w, y + h))
            blurred = region.filter(ImageFilter.GaussianBlur(radius=12))
            img.paste(blurred, (x, y))

        output_name = "blurred_" + file_name
        output_path = os.path.join(PROCESSED_DIR, output_name)
        img.save(output_path)

        return jsonify({
            "status": "processed",
            "file_type": "image",
            "output_file": output_name,
            "download_url": request.url_root + "download/" + output_name
        }), 200

    # inside /process route, image block ke baad
    if file_type == "video":
        input_video = os.path.join(UPLOAD_DIR, file_name)
        output_name = f"blurred_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(PROCESSED_DIR, output_name)
    
        filters = []
    
        # Base video
        filters.append("[0:v]setpts=PTS-STARTPTS[base]")
    
        last = "base"
    
        for i, box in enumerate(coordinates):
            x = box["x"]
            y = box["y"]
            w = box["w"]
            h = box["h"]
    
            # ALWAYS crop from original video
            filters.append(
                f"[0:v]crop={w}:{h}:{x}:{y},boxblur=10:2[blur{i}]"
            )
    
            # Overlay on last output
            filters.append(
                f"[{last}][blur{i}]overlay={x}:{y}[v{i}]"
            )
    
            last = f"v{i}"
    
        filter_complex = ";".join(filters)
    
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-filter_complex", filter_complex,
            "-map", f"[{last}]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            output_path
        ]
    
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
        if not os.path.exists(output_path):
            return jsonify({
                "status": "error",
                "message": "FFmpeg failed",
                "ffmpeg_error": result.stderr.decode()
            }), 500
    
        return jsonify({
            "status": "processed",
            "file_type": "video",
            "output_file": output_name,
            "download_url": request.url_root + "download/" + output_name
        }), 200

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(
        PROCESSED_DIR,
        filename,
        as_attachment=True
    )

cleanup_jobs()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
