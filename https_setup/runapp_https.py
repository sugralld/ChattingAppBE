# runapp_https.py - contoh untuk menjalankan Flask dengan HTTPS
from appname import app
from flask_cors import CORS

# Enable CORS for all routes
CORS(app)

if __name__ == "__main__":
    # For development with self-signed certificate
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        ssl_context="adhoc",  # Generates self-signed certificate
    )

    # Alternative with custom certificate files:
    # app.run(
    #     host="0.0.0.0",
    #     port=5000,
    #     debug=True,
    #     ssl_context=('cert.pem', 'key.pem')
    # )
