from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.before_request
def log_request_info():
    print('Request Headers:', dict(request.headers))
    print('Request URL:', request.url)

@app.errorhandler(Exception)
def handle_error(error):
    print('Error:', str(error))
    return jsonify({'error': str(error)}), 500

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>CultivAi API 🌱</title>
      <style>
        body {
          font-family: 'Segoe UI', sans-serif;
          background: #111;
          color: #00ff9d;
          text-align: center;
          padding: 4rem;
        }
        h1 {
          font-size: 2.5rem;
          margin-bottom: 0.5rem;
        }
        p {
          font-size: 1.2rem;
        }
        code {
          background: #222;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          color: #fff;
        }
      </style>
    </head>
    <body>
      <h1>🌱 CultivAi Backend is Live</h1>
      <p>Use <code>/test/ping</code> for API health checks.</p>
      <p>More routes coming soon: <code>/api/feed</code>, <code>/api/recap</code>, <code>/tasks/cleanup</code>...</p>
      <p>Built with 💚 by Subcool Seeds</p>
    </body>
    </html>
    """

@app.route('/test/ping')
def ping():
    return jsonify({
        "status": "ok",
        "message": "CultivAi backend is live!"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()  # Get the incoming JSON data (e.g., user's message)
    
    # Placeholder logic for chat response, modify with your chatbot logic
    user_message = data.get('message', '')
    
    # Example response, you would replace this with actual chatbot interaction
    response = {
        "status": "ok",
        "message": f"Received your message: {user_message}"
    }
    
    return jsonify(response)

# Implementing /api/feed Route
@app.route('/api/feed', methods=['POST'])
def feed():
    data = request.get_json()  # Get the incoming JSON data (feed entry)

    # Example of processing the feed entry (adjust based on real application logic)
    feed_entry = data.get('feed_entry', 'No content provided')
    
    # Create a response with feed data
    response = {
        "status": "ok",
        "message": f"Feed entry received: {feed_entry}"
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
