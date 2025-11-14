from appname.config import *
from appname.datas.user_friends import *

########################################
#          FUNCTION WRAPPER            #
########################################

def funcGetUserFriends(user_id, limit=10, page=1):
    try:
        results = getUserFriends(user_id, limit, page)

        if isinstance(results, dict) and "error" in results:
            return {
                "status": "error",
                "code": 404,
                "message": results["error"],
                "data": []
            }

        formatted_data = []
        for row in results:
            formatted_data.append({
                "friend_id": row.get("friend_id"),
                "friend_username": row.get("friend_username"),
                "created_at": row.get("created_at"),
            })

        return {
            "status": "success",
            "code": 0,
            "message": "",
            "data": formatted_data
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }

def funcGetUserFriendsByUsername(username, limit=10, page=1):
    try:
        results = getUserFriendsByUsername(username, limit, page)

        if isinstance(results, dict) and "error" in results:
            return {
                "status": "error",
                "code": 404,
                "message": results["error"],
                "data": []
            }

        formatted_data = []
        for row in results:
            formatted_data.append({
                "friend_id": row.get("friend_id"),
                "friend_username": row.get("friend_username"),
                "created_at": row.get("created_at"),
            })

        return {
            "status": "success",
            "code": 0,
            "message": "",
            "data": formatted_data
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }