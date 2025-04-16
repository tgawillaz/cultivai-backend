from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Home route
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>CultivAi API 🌱</title>
    </head>
    <body>
      <h1>🌱 CultivAi Backend is Live</h1>
      <p>Use <code>/test/ping</code> for API health checks.</p>
      <p>More routes coming soon: <code>/api/feed</code>, <code>/api/recap</code>, <code>/tasks/cleanup</code>...</p>
      <p>Built with 💚 by Subcool Seeds</p>
    </body>
    </html>
    """

# Health check route
@app.route('/test/ping')
def ping():
    return jsonify({
        "status": "ok",
        "message": "CultivAi backend is live!"
    })

# Chat route
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()  # Get the incoming JSON data (e.g., user's message)
    
    user_message = data.get('message', '')
    
    # Placeholder response - replace with actual chat logic
    response = {
        "status": "ok",
        "message": f"Received your message: {user_message}"
    }
    
    return jsonify(response)

# Running the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
