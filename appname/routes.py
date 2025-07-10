from appname import app
from flask import request, jsonify
import requests

@app.route('/checkconnection', methods=['GET'])
def check_connection():
    try:
        result = requests.get('https://www.google.com', timeout=3)
        if result.status_code == 200:
            return {'status': 'success', 'message': 'Internet connection is available'}
        else:
            return {'status': 'error', 'message': f'Unexpected response: {result.status_code}'}
    except requests.exceptions.RequestException:
        return {'status': 'error', 'message': 'No internet connection'}

@app.route('/hello', methods=['GET'])
def hello_world():
    return {'status': 'success', 'message': 'Hello from Flask route!'}
