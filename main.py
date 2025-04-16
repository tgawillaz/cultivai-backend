from flask import Flask, jsonify, request, make_response
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
    
    user_message = data.get('message', '')
    
    response = {
        "status": "ok",
        "message": f"Received your message: {user_message}"
    }
    
    return jsonify(response)

@app.route('/api/feed', methods=['POST'])
def feed():
    data = request.get_json()  # Get the incoming JSON data for the feed

    # Placeholder: You can process the feed data and save it
    feed_data = data.get('feed', 'No feed data provided')
    
    response = {
        "status": "ok",
        "message": "Feed data received",
        "data": feed_data
    }
    
    return jsonify(response)

@app.route('/api/recap', methods=['POST'])
def recap():
    data = request.get_json()  # Get the incoming JSON data for the recap

    recap_data = data.get('recap', 'No recap data provided')
    
    response = {
        "status": "ok",
        "message": "Recap data received",
        "data": recap_data
    }
    
    return jsonify(response)

@app.route('/tasks/cleanup', methods=['POST'])
def cleanup():
    # Example cleanup logic
    cleanup_success = True  # Assuming cleanup was successful

    if cleanup_success:
        response = {
            "status": "ok",
            "message": "Cleanup task completed successfully"
        }
    else:
        response = {
            "status": "error",
            "message": "Failed to perform cleanup"
        }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
