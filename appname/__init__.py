# appname/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

# Load environment variables from a local .env file (does not override real env by default).
# Use an explicit path so this works even if the server is started from a different CWD.
try:
	from pathlib import Path

	from dotenv import load_dotenv

	dotenv_path = Path(__file__).resolve().parent.parent / ".env"
	load_dotenv(dotenv_path=dotenv_path)
except Exception:
	# dotenv is optional at runtime; app still works with OS-level env vars.
	pass

app = Flask(__name__)

# Enable CORS globally
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Import routes after initializing app & socketio
from appname import routes
