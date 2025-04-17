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

@app.route("/api/stats/dashboard", methods=["GET"])
@admin_required
def dashboard_stats():
    total_orders = len(orders)
    total_revenue = sum(o["total"] for o in orders if o["payment_status"] == "Paid")
    status_counts = {"Paid": 0, "Pending": 0, "Rejected": 0, "Under Review": 0, "Canceled": 0}
    for o in orders:
        status = o["payment_status"]
        if status in status_counts:
            status_counts[status] += 1
    product_sales = {}
    for o in orders:
        for item in o["items"]:
            pid = item["product_id"]
            qty = item["quantity"]
            product_sales[pid] = product_sales.get(pid, 0) + qty
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
    return jsonify({
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "status_counts": status_counts,
        "top_products": top_products
    })

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = USERS.get(username)
    if user and user["password"] == password:
        token = create_access_token(identity={"username": username, "role": user["role"]})
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/product", methods=["POST"])
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

@app.route("/api/products", methods=["GET"])
def list_products():
    return jsonify(products)

@app.route("/api/order", methods=["POST"])
@jwt_required()
def place_order():
    global order_id_counter
    data = request.get_json()
    items = data["items"]
    for item in items:
        product = next((p for p in products if p["id"] == item["product_id"]), None)
        if not product:
            return jsonify({"error": f"Product ID {item['product_id']} not found"}), 404
        if product["stock"] < item["quantity"]:
            return jsonify({"error": f"Insufficient stock for product ID {item['product_id']}"}), 400
    for item in items:
        product = next(p for p in products if p["id"] == item["product_id"])
        product["stock"] -= item["quantity"]
    order = {
        "id": order_id_counter,
        "user_id": data["user_id"],
        "items": items,
        "total": data["total"],
        "shipping": data["shipping"],
        "payment_status": "Pending",
        "payment_confirmation": None,
        "created_at": datetime.utcnow().isoformat(),
        "status_history": [{"status": "Pending", "timestamp": datetime.utcnow().isoformat()}],
        "placed_by": get_jwt_identity()["username"]
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Order placed successfully", "order": order}), 201

@app.route("/api/me/orders", methods=["GET"])
@jwt_required()
def get_my_orders():
    current_user = get_jwt_identity()["username"]
    user_orders = [o for o in orders if o["placed_by"] == current_user]
    return jsonify(user_orders)

@app.route("/api/payment-confirmation", methods=["POST"])
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
    return jsonify({"message": "Payment confirmation submitted", "order": order}), 200

@app.route("/api/ai/review-payment", methods=["POST"])
@admin_required
def review_payment():
    data = request.get_json()
    order_id = data.get("order_id")
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    if not order.get("payment_confirmation") or not order["payment_confirmation"].get("screenshot_url"):
        return jsonify({"error": "No screenshot submitted"}), 400
    approved = order["total"] < 100
    new_status = "Paid" if approved else "Rejected"
    order["payment_status"] = new_status
    order["reviewed_by"] = "CultivAi"
    order["reviewed_at"] = datetime.utcnow().isoformat()
    order.setdefault("status_history", []).append({"status": new_status, "timestamp": order["reviewed_at"]})
    return jsonify({"message": "Payment reviewed", "order_id": order_id, "status": new_status})

@app.route("/api/reset", methods=["GET"])
@admin_required
def reset_all_data():
    global products, orders, product_id_counter, order_id_counter
    products.clear()
    orders.clear()
    product_id_counter = 1
    order_id_counter = 1
    return jsonify({"message": "All data reset successfully"})

@app.route("/api/export", methods=["GET"])
@admin_required
def export_all():
    return jsonify({"products": products, "orders": orders})

@app.route("/api/order/<int:order_id>/status", methods=["PATCH"])
@admin_required
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    order["payment_status"] = new_status
    order.setdefault("status_history", []).append({"status": new_status, "timestamp": datetime.utcnow().isoformat()})
    return jsonify({"message": f"Order {order_id} updated to {new_status}"})

@app.route("/api/dev/create-backdated-order", methods=["POST"])
@admin_required
def backdate_order():
    global order_id_counter
    data = request.get_json()
    backdate_minutes = int(data.get("minutes", 61))
    created_time = datetime.utcnow() - timedelta(minutes=backdate_minutes)
    order = {
        "id": order_id_counter,
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
        "total": 42,
        "shipping": {
            "address": "Fake Lane 123",
            "email": "test@dev.com",
            "name": "Backdated Test",
            "phone": "000-000-0000"
        },
        "payment_status": "Pending",
        "payment_confirmation": None,
        "created_at": created_time.isoformat(),
        "status_history": [{"status": "Pending", "timestamp": created_time.isoformat()}],
        "placed_by": "admin"
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Backdated order created", "order": order})

if __name__ == "__main__":
    app.run(debug=True)
