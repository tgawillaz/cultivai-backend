from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import jwt as pyjwt
import os

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
INTERNAL_SECRET_KEY = "secret_key"

products = []
orders = []
product_id_counter = 1
order_id_counter = 1
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

USERS = {
    "user": {"password": "password", "role": "user"},
    "admin": {"password": "adminpass", "role": "admin"}
}

ALLOWED_PAYMENT_METHODS = ["CashApp", "Venmo", "PayPal"]

def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@app.route("/api/health")
def health():
    return jsonify({"status": "CultivAi backend is live"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = USERS.get(username)
    if user and user["password"] == password:
        access_token = create_access_token(identity={"username": username, "role": user["role"]})
        return jsonify({"token": access_token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/product', methods=['POST'])
@admin_required
def create_product():
    global product_id_counter
    data = request.get_json()
    product = {
        "id": product_id_counter,
        "name": data["name"],
        "description": data["description"],
        "price": data["price"],
        "image": data["image"],
        "stock": data["stock"],
        "created_by": get_jwt_identity()["username"]
    }
    products.append(product)
    product_id_counter += 1
    return jsonify({"message": "Product added successfully", "product": product}), 201

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/order', methods=['POST'])
@jwt_required()
def create_order():
    global order_id_counter
    data = request.get_json()
    order = {
        "id": order_id_counter,
        "user_id": data["user_id"],
        "items": data["items"],
        "total": data["total"],
        "shipping": data["shipping"],
        "payment_status": "Pending",
        "payment_confirmation": None,
        "created_at": datetime.utcnow().isoformat(),
        "status_history": [
            {"status": "Pending", "timestamp": datetime.utcnow().isoformat()}
        ],
        "placed_by": get_jwt_identity()["username"]
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Order placed successfully", "order": order}), 201

@app.route('/api/me/orders', methods=['GET'])
@jwt_required()
def get_my_orders():
    user = get_jwt_identity()["username"]
    user_orders = [o for o in orders if o["placed_by"] == user]
    return jsonify(user_orders)

@app.route('/api/order/<int:order_id>/status-history', methods=['GET'])
@jwt_required()
def get_status_history(order_id):
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order.get("status_history", []))

@app.route('/api/orders', methods=['GET'])
@admin_required
def get_all_orders():
    status_filter = request.args.get("status")
    if status_filter:
        filtered = [o for o in orders if o["payment_status"] == status_filter]
        return jsonify(filtered)
    return jsonify(orders)

@app.route('/api/payment-confirmation', methods=['POST'])
@jwt_required()
def confirm_payment():
    data = request.get_json()
    current_user = get_jwt_identity()["username"]
    order_id = data.get("order_id")
    screenshot_url = data.get("screenshot_url")
    method = data.get("payment_method")
    if method not in ALLOWED_PAYMENT_METHODS:
        return jsonify({"error": f"Invalid payment method. Must be one of: {ALLOWED_PAYMENT_METHODS}"}), 400
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if order["placed_by"] != current_user and get_jwt_identity()["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    order["payment_confirmation"] = {
        "screenshot_url": screenshot_url,
        "method": method,
        "submitted_at": datetime.utcnow().isoformat()
    }
    order["payment_status"] = "Under Review"
    order.setdefault("status_history", []).append({"status": "Under Review", "timestamp": datetime.utcnow().isoformat()})
    print(f"[Alert] Payment submitted for Order {order_id} via {method}")
    return jsonify({"message": "Payment confirmation submitted", "order": order}), 200

@app.route('/api/payment-resubmit', methods=['POST'])
@jwt_required()
def resubmit_payment():
    data = request.get_json()
    current_user = get_jwt_identity()["username"]
    order_id = data.get("order_id")
    method = data.get("payment_method")
    screenshot_url = data.get("screenshot_url")
    if method not in ALLOWED_PAYMENT_METHODS:
        return jsonify({"error": f"Invalid payment method. Must be one of: {ALLOWED_PAYMENT_METHODS}"}), 400
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if order["placed_by"] != current_user and get_jwt_identity()["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    if order["payment_status"] != "Rejected":
        return jsonify({"error": "Only rejected payments can be resubmitted"}), 400
    order["payment_confirmation"] = {
        "screenshot_url": screenshot_url,
        "method": method,
        "submitted_at": datetime.utcnow().isoformat()
    }
    order["payment_status"] = "Under Review"
    order.setdefault("status_history", []).append({"status": "Under Review", "timestamp": datetime.utcnow().isoformat()})
    print(f"[Alert] Payment resubmitted for Order {order_id} via {method}")
    return jsonify({"message": "Payment resubmission accepted", "order": order}), 200

@app.route('/api/ai/review-payment', methods=['POST'])
@admin_required
def review_payment_screenshot():
    data = request.get_json()
    order_id = data.get("order_id")
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if not order.get("payment_confirmation") or not order["payment_confirmation"].get("screenshot_url"):
        return jsonify({"error": "No screenshot submitted"}), 400
    amount = order.get("total", 0)
    approved = amount < 100
    order["payment_status"] = "Paid" if approved else "Rejected"
    order["reviewed_by"] = "CultivAi"
    order["reviewed_at"] = datetime.utcnow().isoformat()
    order.setdefault("status_history", []).append({"status": order["payment_status"], "timestamp": order["reviewed_at"]})
    print(f"[Alert] Payment for Order {order_id} auto-reviewed: {order['payment_status']}")
    return jsonify({"message": "Payment reviewed automatically", "order_id": order_id, "status": order["payment_status"]}), 200

@app.route('/api/order/<int:order_id>/receipt', methods=['GET'])
@jwt_required()
def order_receipt(order_id):
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"receipt": order}), 200

@app.route('/api/order/<int:order_id>/status', methods=['PATCH'])
@admin_required
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if new_status not in ["Pending", "Paid", "Rejected", "Under Review", "Canceled"]:
        return jsonify({"error": "Invalid status"}), 400
    order["payment_status"] = new_status
    order.setdefault("status_history", []).append({
        "status": new_status,
        "timestamp": datetime.utcnow().isoformat()
    })
    print(f"[Alert] Order {order_id} manually updated to: {new_status}")
    return jsonify({"message": f"Order {order_id} updated", "order": order}), 200

@app.route('/api/webhook/order-status', methods=['POST'])
@admin_required
def webhook_status():
    data = request.get_json()
    print(f"[Webhook] Order Status Changed: {data}")
    return jsonify({"message": "Webhook received"}), 200

@app.route('/api/dev/create-backdated-order', methods=['POST'])
@admin_required
def create_stale_order():
    global order_id_counter
    data = request.get_json()
    created_time = datetime.utcnow() - timedelta(hours=2)
    order = {
        "id": order_id_counter,
        "user_id": data["user_id"],
        "items": data["items"],
        "total": data["total"],
        "shipping": data["shipping"],
        "payment_status": "Pending",
        "payment_confirmation": None,
        "created_at": created_time.isoformat(),
        "status_history": [
            {"status": "Pending", "timestamp": created_time.isoformat()}
        ],
        "placed_by": get_jwt_identity()["username"]
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Backdated order created", "order": order}), 201

@app.route('/api/reset', methods=['GET'])
@admin_required
def reset_data():
    global products, orders, product_id_counter, order_id_counter
    products = []
    orders = []
    product_id_counter = 1
    order_id_counter = 1
    return jsonify({"message": "All data reset successfully"})

@app.route('/api/export', methods=['GET'])
@admin_required
def export_data():
    return jsonify({"products": products, "orders": orders})

if __name__ == '__main__':
    app.run(debug=True)
