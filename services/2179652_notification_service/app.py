from flask import Flask, request, jsonify
import os, random, time

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification_service")
PORT = int(os.getenv("PORT", "5107"))
FAIL_RATE = float(os.getenv("FAIL_RATE", "0.0"))

app = Flask(__name__)
store = set()

@app.route("/do", methods=["POST"])
def do_action():
    data = request.get_json() or {}
    time.sleep(0.1)
    if random.random() < FAIL_RATE:
        return jsonify({"status":"error", "msg": f"{SERVICE_NAME} simulated failure"}), 500
    order_id = data.get("order_id", "unknown")
    store.add(order_id)
    return jsonify({"status":"ok","service":SERVICE_NAME}), 200

@app.route("/compensate", methods=["POST"])
def compensate():
    data = request.get_json() or {}
    order_id = data.get("order_id", "")
    # idempotent: removing even if not present is OK
    store.discard(order_id)
    return jsonify({"status":"compensated","service":SERVICE_NAME}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":SERVICE_NAME}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
