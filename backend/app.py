from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv
from api import api
from events import init_socket_events
from core import engine
from sqlalchemy import text

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"},
        # Include non-/api routes if you keep them:
        r"/health/db": {"origins": "*"},
        r"/messages": {"origins": "*"},
    },
)

# Configuration
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["DEBUG"] = os.getenv("DEBUG", "True").lower() == "true"

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    transports=['websocket', 'polling']
)

# Register API blueprints
app.register_blueprint(api, url_prefix="/api")

# Initialize socket events
init_socket_events(socketio)

@app.route("/")
def home():
    return jsonify(
        {
            "message": "HTN 2025 Real-time Chat Application",
            "status": "running",
            "version": "1.0.0",
        }
    )

@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "message": "Backend is running successfully"})

@app.route("/api/health/db")
def db_health():
    try:
        with engine.connect() as conn:
            n = conn.execute(text("select 1")).scalar()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "database": "disconnected", "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting HTN 2025 Backend on port {port}")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Not configured')}")
    socketio.run(app, host="0.0.0.0", port=port, debug=app.config["DEBUG"])