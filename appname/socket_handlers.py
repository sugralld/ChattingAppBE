from appname import socketio
from flask import request
from appname.functions.chat_room import *
import sys, os
import json

# add functions folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), "functions"))

from appname.functions.messages import sendMessage

# Online users: { user_id: session_id }
online_users = {}

@socketio.on("connect")
def handle_connect():
    print(f"🔗 Connected SID: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    for user_id, sid in list(online_users.items()):
        if sid == request.sid:
            del online_users[user_id]
            print(f"❌ User {user_id} disconnected")

@socketio.on("register_user")
def handle_register_user(data):
    """
    data = { "user_id": "U0001" }
    """
    user_id = str(data.get("user_id"))
    online_users[user_id] = request.sid
    print(f"🟢 User {user_id} is online, SID: {request.sid}")

@socketio.on("send_message")
def handle_send_message(data):
    """
    data = {
        "sender_id": "U0001",
        "receiver_id": "U0002",
        "message": {"text": "Hi!"}
    }
    """
    sender = str(data.get("sender_id"))
    receiver = str(data.get("receiver_id"))
    message_obj = data.get("message")

    if not sender or not receiver or not message_obj:
        socketio.emit("error", {"message": "Missing sender, receiver or message"}, room=request.sid)
        return

    # 1️⃣ Get or create chat room
    room_data = funcCreateOrGetChatRoom(sender, receiver)
    room_id = room_data.get("room_id")

    # 2️⃣ Save message
    result = sendMessage(room_id, sender, message_obj)

    if "error" in result:
        socketio.emit("error", {"message": result["error"]})
        return

    # 3️⃣ Emit to sender
    if sender in online_users:
        socketio.emit("new_message", {
            "room_id": room_id,
            "message": message_obj,
            "sender_id": sender,
            "message_id": result.get("message_id")
        }, room=online_users[sender])

    # 4️⃣ Emit to receiver if online
    if receiver in online_users:
        socketio.emit("new_message", {
            "room_id": room_id,
            "message": message_obj,
            "sender_id": sender,
            "message_id": result.get("message_id")
        }, room=online_users[receiver])
