from flask import Flask, jsonify, request, make_response
from flask_cors import CORS

# Import any blueprints or services you're using (optional)
# from api.moderation import moderation_api
# from api.feed import recap_api
# from api.comments import comments_api
# from api.recap import recap_routes
# from services.recap_webhooks import run_webhook_worker
# from threading import Thread

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Optionally register blueprints (if you're using them)
# app.register_blueprint(moderation_api)
# app.register_blueprint(recap_api)
# app.register_blueprint(comments_api)
# app.register_blueprint(recap_routes)

# Optionally run background services (like webhook queues)
# Thread(target=run_webhook_worker).start()

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

@app.route('/api/feed', methods=['POST'])
def post_feed():
    data = request.get_json()  # Get the incoming JSON data
    
    # Example feed data, you would add actual feed logic here
    feed_item = {
        "feed_id": data.get("feed_id", "No ID provided"),
        "title": data.get("title", "No title provided"),
        "content": data.get("content", "No content provided")
    }
    
    # Return a JSON response with the received feed data
    return jsonify({
        "status": "ok",
        "message": "Feed item received",
        "data": feed_item
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
