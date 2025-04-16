from flask import Flask, request, jsonify
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
SECRET_KEY = "secret_key"  # Replace with env var later

# Dummy auth function
def authenticate(username, password):
    return username == "user" and password == "password"

# -------------------
# 🩺 Health Check
@app.route("/")
@app.route("/api/health")
def health():
    return jsonify({"status": "CultivAi backend is live"})

# -------------------
# 🔐 Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if authenticate(username, password):
        token = jwt.encode(
            {'user': username, 'exp': datetime.utcnow() + timedelta(hours=1)},
            SECRET_KEY,
            algorithm='HS256'
        )
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

# -------------------
# 🔐 Verify Token
@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get("token")

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True, "user": decoded["user"]})
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401

# -------------------
# 🔓 Dummy Logout (frontend handles it)
@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logout successful — delete token client-side."})

# -------------------
# 🛍️ Create product
@app.route('/api/product', methods=['POST'])
def add_product():
    data = request.get_json()
    product = {
        'name': data.get('name'),
        'description': data.get('description'),
        'price': data.get('price'),
        'image': data.get('image'),
        'stock': data.get('stock')
    }
    return jsonify({"message": "Product added successfully", "product": product}), 201

# 🔍 Get all products
@app.route('/api/products', methods=['GET'])
def get_products():
    products = [
        {"id": 1, "name": "Product 1", "price": 25.0, "image": "product1.jpg"},
        {"id": 2, "name": "Product 2", "price": 40.0, "image": "product2.jpg"}
    ]
    return jsonify(products)

# 🔍 Get one product
@app.route('/api/product/<int:id>', methods=['GET'])
def get_product(id):
    product = {"id": id, "name": "Product 1", "price": 25.0, "description": "Product description", "image": "product1.jpg"}
    return jsonify(product)

# 🛠️ Update product
@app.route('/api/product/<int:id>', methods=['POST'])
def update_product(id):
    data = request.get_json()
    updated_product = {
        'name': data.get('name'),
        'description': data.get('description'),
        'price': data.get('price'),
        'image': data.get('image'),
        'stock': data.get('stock')
    }
    return jsonify({"message": "Product updated successfully", "product": updated_product}), 200

# 📦 Create order
@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.get_json()
    order = {
        'user_id': data.get('user_id'),
        'items': data.get('items'),
        'total': data.get('total'),
        'shipping_address': data.get('shipping_address'),
        'payment_status': 'Pending'
    }
    return jsonify({"message": "Order placed successfully", "order": order}), 201

# 🔍 Get one order
@app.route('/api/order/<int:id>', methods=['GET'])
def get_order(id):
    order = {"id": id, "user_id": 1, "items": [{"product_id": 1, "quantity": 2}], "total": 50.0, "shipping_address": "123 Street", "payment_status": "Pending"}
    return jsonify(order)

# 🧾 Get user’s orders
@app.route('/api/orders/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    orders = [
        {"order_id": 1, "status": "Shipped", "total": 100.0},
        {"order_id": 2, "status": "Pending", "total": 50.0}
    ]
    return jsonify(orders)

# 💳 Payment update
@app.route('/api/payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    payment_status = data.get('payment_status')
    return jsonify({"message": "Payment processed successfully", "order_id": order_id, "payment_status": payment_status}), 200

# -------------------
# 🏁 Run the app locally
if __name__ == "__main__":
    app.run(debug=True)
