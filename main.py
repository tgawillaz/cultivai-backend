from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

products = []
orders = []

@app.route("/api/product", methods=["POST"])
def create_product():
    data = request.get_json()
    product = {
        "id": len(products) + 1,
        "name": data.get("name"),
        "price": data.get("price"),
        "stock": data.get("stock"),
        "image": data.get("image"),
        "description": data.get("description"),
        "created_by": data.get("created_by", "admin")
    }
    products.append(product)
    return jsonify({"message": "Product added successfully", "product": product}), 201

@app.route("/api/product", methods=["GET"])
def get_all_products():
    return jsonify(products), 200

@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.get_json()
    order = {
        "id": len(orders) + 1,
        "product_id": data.get("product_id"),
        "quantity": data.get("quantity"),
        "customer_name": data.get("customer_name"),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "status_history": [
            {"status": "pending", "timestamp": datetime.utcnow().isoformat()}
        ]
    }
    orders.append(order)
    return jsonify(order), 200

@app.route("/api/order/<int:order_id>/status-history", methods=["GET"])
def get_order_status_history(order_id):
    for order in orders:
        if order["id"] == order_id:
            return jsonify(order["status_history"]), 200
    return jsonify({"error": "Order not found"}), 404

@app.route("/api/reset", methods=["GET"])
def reset_data():
    products.clear()
    orders.clear()
    return jsonify({"message": "All data has been reset."}), 200

@app.route("/api/export", methods=["GET"])
def export_data():
    return jsonify({"products": products, "orders": orders}), 200

@app.route("/api/login", methods=["POST"])
def login():
    return jsonify({
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
