# (add the os import + FLASK_DEBUG env var logic)

# Stage and commit the changes
git add server/app.py
git commit -m "Make Flask debug configurable via FLASK_DEBUG env var"

# Push to GitHub (retry HTTPS if SSH fails)
git push -u origin feature/flask-debug-env
# or if SSH keeps failing, switch to HTTPS:
git remote set-url origin https://github.com/EclipseWhetstone1/PenetrativeDocumentation.git
git push -u origin feature/flask-debug-env# (add the os import + FLASK_DEBUG env var logic)

# Stage and commit the changes
git add server/app.py
git commit -m "Make Flask debug configurable via FLASK_DEBUG env var"

# Push to GitHub (retry HTTPS if SSH fails)
git push -u origin feature/flask-debug-env
# or if SSH keeps failing, switch to HTTPS:
git remote set-url origin https://github.com/EclipseWhetstone1/PenetrativeDocumentation.git
git push -u origin feature/flask-debug-env
from flask import Flask, request, jsonify
import logging
import json

app = Flask(__name__)

logging.basicConfig(
    filename="reports.log",
    level=logging.INFO,
    format="%(message)s"
)

def validate_payload(data):
    required = ["machine_id", "timestamp", "event", "data"]
    return all(key in data for key in required)

@app.route("/api/report", methods=["POST"])
def report():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if not validate_payload(data):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    logging.info(json.dumps(data))
    return jsonify({"status": "ok", "received_event": data["event"]}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
