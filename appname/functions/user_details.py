from appname.config import *
import bcrypt
import re

from appname.datas.user_details import *

def funcGetUserDetail(limit=10, page=1):
    try:
        # Call the actual data retrieval logic
        results = getUserDetail(limit, page)

        # If the result is a dict with 'error', treat as failure
        if isinstance(results, dict) and "error" in results:
            return {
                "status": "error",
                "code": 404,
                "message": results["error"],
                "data": [],
            }

        # Format the result if it's a list of user dicts
        formatted_data = []
        for row in results:
            formatted_data.append(
                {
                    "user_id": row.get("user_id"),
                    "user_email": row.get("user_email"),
                    "username": row.get("username"),
                    "profile_picture": row.get("profile_picture"),
                    "blocked_user": row.get("blocked_user"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                    "dob": row.get("dob"),
                    "bio": row.get("bio"),
                }
            )

        return {"status": "success", "code": 0, "message": "", "data": formatted_data}

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcGetUserDetailByID(user_id):
    try:
        # Call the actual data retrieval logic
        result = getUserDetailByID(user_id)

        # If the result is a dict with 'error', treat as failure
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
            "data": [result],  # Wrap single object in list for consistency
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcInsertUserDetail(data):
    try:
        result = insertUserDetail(data)

        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 400,
                "message": result["error"],
                "data": [],
            }

        return {
            "status": "success",
            "code": 0,
            "message": result["message"],
            "data": [{"user_id": result["user_id"]}],
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcUpdateUserDetail(user_id, data):
    try:
        result = updateUserDetail(user_id, data)

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


def funcDeleteUserDetail(user_id):
    try:
        result = deleteUserDetail(user_id)

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
