from flask import Flask, request, jsonify
import requests, os, time

app = Flask(__name__)

SERVICES = [
    {"name":"cart","url": os.getenv("CART_URL","http://cart_service:5101")},
    {"name":"payment","url": os.getenv("PAYMENT_URL","http://payment_service:5102")},
    {"name":"inventory","url": os.getenv("INVENTORY_URL","http://inventory_service:5103")},
    {"name":"order","url": os.getenv("ORDER_URL","http://order_service:5104")},
    {"name":"shipping","url": os.getenv("SHIPPING_URL","http://shipping_service:5105")},
    {"name":"billing","url": os.getenv("BILLING_URL","http://billing_service:5106")},
    {"name":"notification","url": os.getenv("NOTIF_URL","http://notification_service:5107")}, 
    {"name":"loyalty","url": os.getenv("LOYALTY_URL","http://loyalty_service:5108")}
]

TIMEOUT = 5

def call_do(svc, payload):
    return requests.post(svc["url"] + "/do", json=payload, timeout=TIMEOUT)

def call_compensate(svc, payload):
    return requests.post(svc["url"] + "/compensate", json=payload, timeout=TIMEOUT)

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json() or {}
    order_id = data.get("order_id") or f"order-{int(time.time())}"
    payload = {"order_id": order_id, "user": data.get("user"), "items": data.get("items", [])}

    completed = []
    for svc in SERVICES:
        print(f"[SAGA] Calling {svc['name']} at {svc['url']}/do")
        try:
            r = call_do(svc, payload)
            print(f"[SAGA] {svc['name']} returned {r.status_code}")
            if r.status_code != 200:
                raise Exception(f"{svc['name']} returned {r.status_code}: {r.text}")
            completed.append(svc)
        except Exception as e:
            print(f"[SAGA] {svc['name']} failed → {e}")
            print(f"[SAGA] Rolling back previous steps...")
            errs = str(e)
            for comp in reversed(completed):
                try:
                    print(f"[SAGA] Compensating {comp['name']} at {comp['url']}/compensate")
                    call_compensate(comp, payload)
                except Exception as ce:
                    print(f"[SAGA] Compensate failed for {comp['name']} → {ce}")
                    #print("Compensate failed for", comp["name"], ce)
            return jsonify({"status":"failed","msg": f"Failed at {svc['name']}", "error": errs}), 500

    return jsonify({"status":"success","order_id": order_id}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","service":"orchestrator"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))