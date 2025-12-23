from appname.config import *
import bcrypt
import re

from appname.datas.user_details import *
from appname.functions.user_register import validate_email, validate_password
from appname.utils.email_utils import send_email
import random
import os
import bcrypt

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
                    "dob": row.get("dob"),
                    "profile_picture": row.get("profile_picture"),
                    "blocked_user": row.get("blocked_user"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
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


def funcEditProfile(user_id, data):
    try:
        # Validate presence
        if not user_id:
            return {"status": "error", "code": 400, "message": "Missing required parameter: user_id", "data": []}

        username = data.get("username") if data else None
        user_email = data.get("user_email") if data else None
        dob = data.get("dob") if data else None

        if user_email and not validate_email(user_email):
            return {"status": "error", "code": 400, "message": "Format email tidak valid", "data": []}

        result = updateUserProfile(user_id, username, user_email, dob)

        if isinstance(result, dict) and "error" in result:
            return {"status": "error", "code": 404, "message": result["error"], "data": []}

        # If no changes
        if result.get("message") == "No changes detected":
            return {"status": "success", "code": 0, "message": "No changes detected", "data": []}

        return {"status": "success", "code": 0, "message": result.get("message", "Profile updated"), "data": []}

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}



def funcSendVerificationEmail(user_id=None, user_email=None, current_password=None):
    try:
        # basic checks
        if not user_email:
            return {"status": "error", "code": 400, "message": "Missing required parameter: user_email", "data": []}

        # Lookup user by email only — do not require or validate current_password or user_id
        auth = getUserAuthInfoByEmail(user_email)
        if isinstance(auth, dict) and "error" in auth:
            return {"status": "error", "code": 404, "message": auth["error"], "data": []}

        lookup_user_id = auth.get("user_id")

        # generate 4-digit code
        code = str(random.randint(1000, 9999))
        # store code
        setres = setVerificationCode(lookup_user_id, code)
        if isinstance(setres, dict) and "error" in setres:
            return {"status": "error", "code": 500, "message": setres["error"], "data": []}

        # prepare email (Indonesian)
        subject = "[ChattingApp] Kode Verifikasi"
        body = (
            f"Kode verifikasi Anda adalah: {code}. "
            "Silakan masukkan kode ini untuk memverifikasi tindakan Anda. "
            "Jika Anda tidak merasa meminta kode ini, abaikan email ini."
        )
        html_body = (
            "<p>Halo,</p>"
            f"<p>Kode verifikasi Anda adalah <strong>{code}</strong>.</p>"
            "<p>Silakan masukkan kode ini untuk memverifikasi tindakan Anda.</p>"
            "<p>Jika Anda tidak merasa meminta kode ini, Anda dapat mengabaikan email ini.</p>"
            "<p>Terima kasih,<br/>Tim ChattingApp</p>"
        )

        # send email and log result
        send_result = send_email(user_email, subject, body, html=html_body)
        print(f"[user_details] send_result: {send_result}")

        if not send_result.get("success"):
            return {"status": "error", "code": 500, "message": f"Failed to send email: {send_result.get('error')}", "data": []}

        # If running in dev mode, include code in response for easier testing
        if send_result.get("dev"):
            return {"status": "success", "code": 0, "message": "Verification email (dev mode) - code not sent, returned for testing", "data": [{"verification_code": code}, {"send_result": send_result}]}

        return {"status": "success", "code": 0, "message": "Verification email sent", "data": [{"verification_code_set": True, "send_result": send_result}]}

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcVerifyAndChangePassword(user_id, verification_code, new_password, user_email=None):
    try:
        if not verification_code or not new_password:
            return {"status": "error", "code": 400, "message": "Missing required parameters: verification_code, new_password", "data": []}

        # Determine user context
        if user_id:
            auth = getUserAuthInfo(user_id)
            if isinstance(auth, dict) and "error" in auth:
                return {"status": "error", "code": 404, "message": auth["error"], "data": []}
        else:
            if not user_email:
                return {"status": "error", "code": 400, "message": "Missing user identifier: provide user_id or user_email", "data": []}
            auth = getUserAuthInfoByEmail(user_email)
            if isinstance(auth, dict) and "error" in auth:
                return {"status": "error", "code": 404, "message": auth["error"], "data": []}
            user_id = auth.get("user_id")

        stored_code = auth.get("verification_code")
        if not stored_code:
            return {"status": "error", "code": 400, "message": "No verification code set for user", "data": []}

        if str(stored_code) != str(verification_code):
            return {"status": "error", "code": 400, "message": "Invalid verification code", "data": []}

        # validate new password
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return {"status": "error", "code": 400, "message": msg, "data": []}

        # hash and update
        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        updater = updatePasswordHash(user_id, new_hash)
        if isinstance(updater, dict) and "error" in updater:
            return {"status": "error", "code": 500, "message": updater["error"], "data": []}

        return {"status": "success", "code": 0, "message": "Password updated successfully", "data": []}

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
