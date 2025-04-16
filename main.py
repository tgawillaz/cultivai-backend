from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import jwt as pyjwt

app = Flask(__name__)
CORS(app)

# Config
app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)
INTERNAL_SECRET_KEY = "secret_key"  # legacy /verify-token

# Dummy users with roles
USERS = {
    "user": {"password": "password", "role": "user"},
    "admin": {"password": "adminpass", "role": "admin"}
}

# Auth helpers
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

# -------------------
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

# -------------------
@app.route('/api/product', methods=['POST'])
@admin_required
def add_product():
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    product = {
        'name': data.get('name'),
        'description': data.get('description'),
        'price': data.get('price'),
        'image': data.get('image'),
        'stock': data.get('stock'),
        'created_by': current_user
    }
    return jsonify({"message": "Product added successfully", "product": product}), 201

@app.route('/api/products', methods=['GET'])
def get_products():
    products = [
        {"id": 1, "name": "Product 1", "price": 25.0, "image": "product1.jpg"},
        {"id": 2, "name": "Product 2", "price": 40.0, "image": "product2.jpg"}
    ]
    return jsonify(products)

@app.route('/api/product/<int:id>', methods=['GET'])
def get_product(id):
    product = {"id": id, "name": "Product 1", "price": 25.0, "description": "Product description", "image": "product1.jpg"}
    return jsonify(product)

@app.route('/api/product/<int:id>', methods=['POST'])
@admin_required
def update_product(id):
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    updated_product = {
        'name': data.get('name'),
        'description': data.get('description'),
        'price': data.get('price'),
        'image': data.get('image'),
        'stock': data.get('stock'),
        'updated_by': current_user
    }
    return jsonify({"message": "Product updated successfully", "product": updated_product}), 200

# -------------------
@app.route('/api/order', methods=['POST'])
@jwt_required()
def place_order():
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    order = {
        'user_id': data.get('user_id'),
        'items': data.get('items'),
        'total': data.get('total'),
        'shipping_address': data.get('shipping_address'),
        'payment_status': 'Pending',
        'placed_by': current_user
    }
    return jsonify({"message": "Order placed successfully", "order": order}), 201

@app.route('/api/order/<int:id>', methods=['GET'])
def get_order(id):
    order = {"id": id, "user_id": 1, "items": [{"product_id": 1, "quantity": 2}], "total": 50.0, "shipping_address": "123 Street", "payment_status": "Pending"}
    return jsonify(order)

@app.route('/api/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    orders = [
        {"order_id": 1, "status": "Shipped", "total": 100.0},
        {"order_id": 2, "status": "Pending", "total": 50.0}
    ]
    return jsonify(orders)

@app.route('/api/payment', methods=['POST'])
@jwt_required()
def process_payment():
    current_user = get_jwt_identity()["username"]
    data = request.get_json()
    order_id = data.get('order_id')
    payment_status = data.get('payment_status')
    return jsonify({
        "message": "Payment processed successfully",
        "order_id": order_id,
        "payment_status": payment_status,
        "processed_by": current_user
    }), 200

# -------------------
if __name__ == "__main__":
    app.run(debug=True)
