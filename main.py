from flask import Flask, request, jsonify
from supabase import create_client, Client
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Supabase credentials from environment variables (more secure!)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- HEALTH CHECK --------------------
@app.route("/")
def health():
    return jsonify({"status": "CultivAi backend is live!"})

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

# -------------------- TEST DB --------------------
@app.route("/test-db")
def test_db():
    try:
        data = supabase.table("your_table_name").select("*").limit(1).execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
