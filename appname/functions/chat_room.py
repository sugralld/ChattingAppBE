from appname.config import *
from datetime import datetime
import json
from appname import socketio

from appname.datas.chat_room import *


def funcCreateOrGetChatRoom(user_id_first, user_id_second):
    try:
        result = createOrGetChatRoom(user_id_first, user_id_second)

        # error handling
        if isinstance(result, dict) and (
            "error" in result or result.get("success") is False
        ):
            return {
                "status": "error",
                "code": 403 if result.get("status") == "not_friends" else 404,
                "message": result.get("message", result.get("error")),
                "data": [],
            }

        # success handling
        return {
            "status": "success",
            "code": 0,
            "message": result["message"],
            "data": {
                "room_id": result.get("room_id"),
                "status": result.get("status"),  # created or exists
                "user_id_first": user_id_first,
                "user_id_second": user_id_second,
            },
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcSendMessage(room_id, sender_id, message_obj):
    try:
        result = sendMessage(room_id, sender_id, message_obj)
        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 404,
                "message": result["error"],
                "data": [],
            }

        message_id = result.get("message_id")

        if message_id:
            print(f"✅ Message created: {message_id}")

        return {
            "status": "success",
            "code": 0,
            "message": result.get("message"),
            "data": {"message_id": result.get("message_id")},
        }
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcDeleteMessage(message_id):
    try:
        result = deleteMessage(message_id)
        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 404,
                "message": result["error"],
                "data": [],
            }

        room_id = result.get("room_id")

        # 🔥 EMIT DELETE EVENT
        if message_id and room_id:
            try:
                socketio.emit(
                    "message_deleted",
                    {
                        "action": "DELETE",
                        "room_id": room_id,
                        "message_id": message_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    room=f"room_{room_id}",
                )
                print(f"✅ Socket.IO delete event emitted: {message_id}")
            except Exception as e:
                print(f"⚠️ Socket.IO emit error: {str(e)}")

        return {
            "status": "success",
            "code": 0,
            "message": result["message"],
            "data": {"room_id": result.get("room_id")},
        }
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcGetChatRoomList(user_id, limit=10, page=1, search=None):
    try:
        result = getChatRoomsForUser(user_id, limit, page, search)
        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 404,
                "message": result["error"],
                "data": [],
            }
        return {
            "status": "success",
            "code": 0,
            "message": "",
            "data": {"chat_rooms": result.get("chat_rooms", [])},
        }
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcGetSingleMessage(message_id, viewer_id):
    """Fetch a single message by ID - optimized for realtime updates"""
    try:
        from appname.datas.messages import getSingleMessage

        result = getSingleMessage(message_id, viewer_id)

        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 404,
                "message": result["error"],
                "data": {},
            }

        return {
            "status": "success",
            "code": 0,
            "message": "",
            "data": {"message": result},
        }
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": {}}
