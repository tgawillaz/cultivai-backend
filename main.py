from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import jwt as pyjwt

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
INTERNAL_SECRET_KEY = "secret_key"

products = []
orders = []
product_id_counter = 1
order_id_counter = 1

USERS = {
    "user": {"password": "password", "role": "user"},
    "admin": {"password": "adminpass", "role": "admin"}
}

ALLOWED_PAYMENT_METHODS = ["CashApp", "Venmo", "PayPal"]

def authenticate(username, password):
    user = USERS.get(username)
    return user and user["password"] == password

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

@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logout successful — delete token client-side."})

@app.route('/api/product', methods=['POST'])
@admin_required
def add_product():
    global product_id_counter
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    product = {
        "id": product_id_counter,
        "name": data.get("name"),
        "description": data.get("description"),
        "price": data.get("price"),
        "image": data.get("image"),
        "stock": data.get("stock"),
        "created_by": current_user,
        "created_at": datetime.utcnow().isoformat()
    }
    products.append(product)
    product_id_counter += 1
    return jsonify({"message": "Product added successfully", "product": product}), 201

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/product/<int:id>', methods=['GET'])
def get_product(id):
    product = next((p for p in products if p["id"] == id), None)
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/product/<int:id>', methods=['POST'])
@admin_required
def update_product(id):
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    product = next((p for p in products if p["id"] == id), None)
    if product:
        product.update({
            "name": data.get("name"),
            "description": data.get("description"),
            "price": data.get("price"),
            "image": data.get("image"),
            "stock": data.get("stock"),
            "updated_by": current_user
        })
        return jsonify({"message": "Product updated successfully", "product": product}), 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/product/<int:id>', methods=['DELETE'])
@admin_required
def delete_product(id):
    global products
    original_len = len(products)
    products = [p for p in products if p["id"] != id]
    if len(products) < original_len:
        return jsonify({"message": f"Product {id} deleted successfully"}), 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/orders', methods=['GET'])
@admin_required
def get_all_orders():
    return jsonify(orders), 200

@app.route('/api/me/orders', methods=['GET'])
@jwt_required()
def get_my_orders():
    current_user = get_jwt_identity()["username"]
    my_orders = [o for o in orders if o["placed_by"] == current_user]
    return jsonify(my_orders), 200

@app.route('/api/order/<int:id>/status', methods=['PATCH'])
@admin_required
def update_order_status(id):
    data = request.get_json()
    new_status = data.get("status")
    order = next((o for o in orders if o["id"] == id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    timestamp = datetime.utcnow().isoformat()
    order["payment_status"] = new_status
    order.setdefault("status_history", []).append({"status": new_status, "timestamp": timestamp})
    print(f"[Webhook] Order {id} status changed to {new_status} at {timestamp}")
    return jsonify({"message": "Order status updated", "order": order}), 200

@app.route('/api/order', methods=['POST'])
@jwt_required()
def place_order():
    global order_id_counter
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    order = {
        "id": order_id_counter,
        "user_id": data.get("user_id"),
        "items": data.get("items"),
        "total": data.get("total"),
        "shipping": data.get("shipping"),
        "payment_status": "Pending",
        "payment_confirmation": None,
        "placed_by": current_user,
        "created_at": datetime.utcnow().isoformat(),
        "status_history": [
            {"status": "Pending", "timestamp": datetime.utcnow().isoformat()}
        ]
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Order placed successfully", "order": order}), 201

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
    return jsonify({"message": "Payment reviewed automatically", "order_id": order_id, "status": order["payment_status"]}), 200

@app.route('/api/reset', methods=['GET'])
@admin_required
def reset_data():
    global products, orders, product_id_counter, order_id_counter
    products = []
    orders = []
    product_id_counter = 1
    order_id_counter = 1
    return jsonify({"message": "All data reset successfully"}), 200

@app.route('/api/export', methods=['GET'])
@admin_required
def export_data():
    return jsonify({"products": products, "orders": orders}), 200

@app.route('/api/cron/cancel-stale-orders', methods=['GET'])
@admin_required
def cancel_stale_orders():
    now = datetime.utcnow()
    expired = 0
    for order in orders:
        if order["payment_status"] == "Pending":
            created_time = datetime.fromisoformat(order["created_at"])
            if now - created_time > timedelta(hours=1):
                order["payment_status"] = "Canceled"
                order["canceled_at"] = now.isoformat()
                order.setdefault("status_history", []).append({"status": "Canceled", "timestamp": now.isoformat()})
                expired += 1
    return jsonify({"message": f"{expired} stale orders canceled"}), 200

@app.route('/api/dev/create-backdated-order', methods=['GET'])
@admin_required
def create_backdated_order():
    global order_id_counter
    order = {
        "id": order_id_counter,
        "user_id": 1,
        "items": [{"product_id": 1, "quantity": 1}],
        "total": 42,
        "shipping": {
            "name": "Backdated Test",
            "email": "test@dev.com",
            "phone": "000-000-0000",
            "address": "Fake Lane 123"
        },
        "payment_status": "Pending",
        "payment_confirmation": None,
        "placed_by": "admin",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "status_history": [
            {"status": "Pending", "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()}
        ]
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Backdated test order created", "order": order}), 201

if __name__ == "__main__":
    app.run(debug=True)
