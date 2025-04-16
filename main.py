from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import jwt as pyjwt

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
INTERNAL_SECRET_KEY = "secret_key"

# In-memory storage
products = []
orders = []
product_id_counter = 1
order_id_counter = 1

# Dummy users
USERS = {
    "user": {"password": "password", "role": "user"},
    "admin": {"password": "adminpass", "role": "admin"}
}

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

@app.route("/")
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

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get("token")
    try:
        decoded = pyjwt.decode(token, INTERNAL_SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True, "user": decoded["user"]})
    except pyjwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401

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
        "shipping_address": data.get("shipping_address"),
        "payment_status": "Pending",
        "placed_by": current_user,
        "created_at": datetime.utcnow().isoformat()
    }
    orders.append(order)
    order_id_counter += 1
    return jsonify({"message": "Order placed successfully", "order": order}), 201

@app.route('/api/order/<int:id>', methods=['GET'])
def get_order(id):
    order = next((o for o in orders if o["id"] == id), None)
    if order:
        return jsonify(order)
    return jsonify({"error": "Order not found"}), 404

@app.route('/api/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    user_orders = [o for o in orders if o["user_id"] == user_id]
    return jsonify(user_orders)

@app.route('/api/order/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_order(id):
    global orders
    current_user = get_jwt_identity()
    order = next((o for o in orders if o["id"] == id), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if current_user["role"] != "admin" and order["placed_by"] != current_user["username"]:
        return jsonify({"error": "Unauthorized"}), 403

    orders.remove(order)
    return jsonify({"message": f"Order {id} deleted successfully"}), 200

@app.route('/api/payment', methods=['POST'])
@jwt_required()
def process_payment():
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    order_id = data.get("order_id")
    payment_status = data.get("payment_status")
    order = next((o for o in orders if o["id"] == order_id), None)
    if order:
        order["payment_status"] = payment_status
        order["payment_processed_by"] = current_user
        return jsonify({
            "message": "Payment processed successfully",
            "order_id": order_id,
            "payment_status": payment_status
        }), 200
    return jsonify({"error": "Order not found"}), 404

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
    return jsonify({
        "products": products,
        "orders": orders
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
