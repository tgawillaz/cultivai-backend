from flask import Flask, request, jsonify
from supabase import create_client, Client
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Supabase credentials
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-or-service-role-key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- PRODUCT ROUTES --------------------

@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        response = supabase.table("products").select("*").order("created_at", desc=True).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/product", methods=["POST"])
def add_product():
    data = request.json
    try:
        result = supabase.table("products").insert({
            "name": data["name"],
            "price": data["price"],
            "stock": data["stock"],
            "image": data["image"],
            "description": data.get("description", ""),
            "created_by": data.get("created_by", "admin")
        }).execute()
        return jsonify({"message": "Product added successfully", "product": result.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- ORDER ROUTES --------------------

@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.json
    try:
        result = supabase.table("orders").insert({
            "product_id": data["product_id"],
            "quantity": data["quantity"],
            "customer_name": data.get("customer_name", "Guest"),
            "status_history": [{"status": "pending"}]
        }).execute()
        return jsonify({"message": "Order placed", "order": result.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/order/<int:order_id>/status-history", methods=["GET"])
def get_status_history(order_id):
    try:
        result = supabase.table("orders").select("status_history").eq("id", order_id).single().execute()
        return jsonify(result.data["status_history"]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- MAIN --------------------

if __name__ == "__main__":
    app.run(debug=True)
