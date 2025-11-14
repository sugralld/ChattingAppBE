from appname.config import *
import bcrypt

from appname.datas.user_login import *

def funcLoginUser(data):
    try:
        identifier = data.get("identifier")
        password = data.get("password")

        if not identifier or not password:
            return {
                "status": "error",
                "code": 400,
                "message": "Field 'identifier' dan 'password' wajib diisi",
                "data": [],
            }

        result = loginUser(identifier, password)

        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 401,
                "message": result["error"],
                "data": [],
            }

        return {
            "status": "success",
            "code": 0,
            "message": "Login berhasil",
            "data": [result],
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}
