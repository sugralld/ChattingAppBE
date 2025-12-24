from appname.config import *
from datetime import datetime

from appname.datas.friend_request import *

def funcGetFriendRequests(receiver, limit=10, page=1):
    try:
        results = getFriendRequests(receiver, limit, page)

        if isinstance(results, dict) and "error" in results:
            return {
                "status": "error",
                "code": 404,
                "message": results["error"],
                "data": [],
            }

        formatted_data = []
        for row in results:
            formatted_data.append(
                {
                    "request_id": row.get("request_id"),
                    "sender_id": row.get("sender"),
                    "sender_username": row.get("sender_username"),
                    "receiver": row.get("receiver"),
                    "sent_at": row.get("sent_at"),
                    "status": row.get("status"),
                }
            )

        return {
            "status": "success",
            "count": len(formatted_data),
            "code": 0,
            "message": "",
            "data": formatted_data,
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcRejectFriendRequest(request_id):
    try:
        result = rejectFriendRequest(request_id)

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
            "message": result["message"],
            "data": [],
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}

