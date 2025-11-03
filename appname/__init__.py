# appname/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS globally
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Import routes after initializing app & socketio
from appname import routes
