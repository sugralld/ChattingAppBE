from appname import app, socketio
import socket
import appname.socket_handlers

if __name__ == "__main__":
    # Get local machine IP for network access
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("✅ Server running with Flask-SocketIO ...")
    print("--------------------------------------------------")
    print(f"🌐 Local:    http://127.0.0.1:8080")
    print(f"📶 Network:  http://{local_ip}:8080")
    print("--------------------------------------------------")

    # Run server
    socketio.run(app, debug=True, host="0.0.0.0", port=8080)
