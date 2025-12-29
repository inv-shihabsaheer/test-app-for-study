import os
import socket
import logging
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

APP_NAME = os.getenv("APP_NAME", "myapp")
APP_ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
HOSTNAME = socket.gethostname()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

@app.route("/")
def home():
    return jsonify({
        "message": "GitHub → Jenkins → Helm → GKE",
        "app": APP_NAME,
        "env": APP_ENV,
        "version": APP_VERSION,
        "pod": HOSTNAME,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@app.route("/api/echo", methods=["POST"])
def echo():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON"}), 400
    return jsonify({"received": payload, "pod": HOSTNAME})

@app.route("/healthz")
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/readyz")
def ready():
    return jsonify({"status": "ready"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
