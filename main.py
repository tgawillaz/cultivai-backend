from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Replace in production
jwt = JWTManager(app)

# In-memory storage
data = {
    "products": {},
    "orders": {},
    "users": {
        "admin": {"password": "password", "role": "admin"},
        "user": {"password": "password", "role": "user"},
    }
}

@app.route('/api/login', methods=['POST'])
def login():
    credentials = request.get_json()
    username = credentials.get('username')
    password = credentials.get('password')
    user = data['users'].get(username)
    if user and user['password'] == password:
        token = create_access_token(identity={"username": username, "role": user['role']}, expires_delta=timedelta(hours=1))
        return jsonify(token=token)
    return jsonify(error="Invalid credentials"), 401

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify(message="Backend is healthy"), 200

@app.route('/api/product', methods=['POST'])
@jwt_required()
def create_product():
    user = get_jwt_identity()
    if user['role'] != 'admin':
        return jsonify(error="Admins only"), 403
    product = request.get_json()
    product_id = len(data['products']) + 1
    product['id'] = product_id
    product['created_by'] = user['username']
    data['products'][product_id] = product
    return jsonify(message="Product added successfully", product=product), 201

@app.route('/api/order', methods=['POST'])
@jwt_required()
def place_order():
    user = get_jwt_identity()
    body = request.get_json()
    order_id = len(data['orders']) + 1
    order = {
        "id": order_id,
        "user_id": 1,
        "items": body['items'],
        "total": body['total'],
        "shipping": body['shipping'],
        "payment_status": "Pending",
        "payment_confirmation": None,
        "created_at": datetime.utcnow().isoformat(),
        "placed_by": user['username'],
        "status_history": [{"status": "Pending", "timestamp": datetime.utcnow().isoformat()}]
    }
    data['orders'][order_id] = order
    return jsonify(message="Order placed successfully", order=order)

@app.route('/api/order/<int:order_id>', methods=['PUT'])
@jwt_required()
def edit_order(order_id):
    user = get_jwt_identity()
    order = data['orders'].get(order_id)
    if not order:
        return jsonify(error="Order not found"), 404
    if order['placed_by'] != user['username']:
        return jsonify(error="Unauthorized"), 403
    body = request.get_json()
    if order['payment_status'] != "Pending":
        return jsonify(error="Only pending orders can be edited"), 400
    order['items'] = body.get('items', order['items'])
    order['total'] = body.get('total', order['total'])
    order['shipping'] = body.get('shipping', order['shipping'])
    return jsonify(message="Order updated", order=order)

@app.route('/api/order/<int:order_id>', methods=['DELETE'])
@jwt_required()
def cancel_order(order_id):
    user = get_jwt_identity()
    order = data['orders'].get(order_id)
    if not order:
        return jsonify(error="Order not found"), 404
    if order['placed_by'] != user['username']:
        return jsonify(error="Unauthorized"), 403
    if order['payment_status'] != "Pending":
        return jsonify(error="Only pending orders can be canceled"), 400
    order['payment_status'] = "Canceled"
    order['status_history'].append({"status": "Canceled", "timestamp": datetime.utcnow().isoformat()})
    return jsonify(message="Order canceled", order=order)

@app.route('/api/payment', methods=['POST'])
@jwt_required()
def confirm_payment():
    body = request.get_json()
    order = data['orders'].get(body['order_id'])
    if not order:
        return jsonify(error="Order not found"), 404
    order['payment_confirmation'] = {
        "method": body['method'],
        "screenshot_url": body['screenshot_url'],
        "submitted_at": datetime.utcnow().isoformat(),
        "submitted_by": get_jwt_identity()['username']
    }
    order['payment_status'] = "Under Review"
    order['status_history'].append({"status": "Under Review", "timestamp": datetime.utcnow().isoformat()})
    return jsonify(message="Payment submitted", order=order)

@app.route('/api/payment/resubmit', methods=['POST'])
@jwt_required()
def resubmit_payment():
    body = request.get_json()
    order = data['orders'].get(body['order_id'])
    if not order:
        return jsonify(error="Order not found"), 404
    order['payment_confirmation'] = {
        "method": body['method'],
        "screenshot_url": body['screenshot_url'],
        "submitted_at": datetime.utcnow().isoformat(),
        "submitted_by": get_jwt_identity()['username']
    }
    order['payment_status'] = "Under Review"
    order['status_history'].append({"status": "Under Review", "timestamp": datetime.utcnow().isoformat()})
    return jsonify(message="Payment resubmission accepted", order=order)

@app.route('/api/order/<int:order_id>/status-history', methods=['GET'])
@jwt_required()
def status_history(order_id):
    order = data['orders'].get(order_id)
    if not order:
        return jsonify(error="Order not found"), 404
    return jsonify(order['status_history'])

@app.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    return jsonify(list(data['orders'].values()))

@app.route('/api/reset', methods=['GET'])
def reset():
    data['products'] = {}
    data['orders'] = {}
    return jsonify(message="All data reset successfully")

@app.route('/api/export', methods=['GET'])
def export():
    return jsonify({"products": list(data['products'].values()), "orders": list(data['orders'].values())})

if __name__ == '__main__':
    app.run(debug=True)
