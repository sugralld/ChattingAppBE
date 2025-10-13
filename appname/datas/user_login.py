from appname.config import *
import bcrypt


def loginUser(identifier, password):
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            user_id,
            user_email,
            username,
            profile_picture,
            blocked_user,
            created_at,
            updated_at,
            password_hash
        FROM user_detail
        WHERE user_email = %s OR username = %s
        LIMIT 1;
    """

    try:
        cur.execute(query, (identifier, identifier))
        row = cur.fetchone()

        if row:
            stored_password = row[7]
            # Check if password is hashed (bcrypt) or plain text
            if stored_password.startswith("$2b$"):
                # Hashed password - use bcrypt
                if not bcrypt.checkpw(
                    password.encode("utf-8"), stored_password.encode("utf-8")
                ):
                    return {"error": "Password salah"}
            else:
                # Plain text password (for backward compatibility)
                if stored_password != password:
                    return {"error": "Password salah"}

            return {
                "user_id": row[0],
                "user_email": row[1],
                "username": row[2],
                "profile_picture": row[3],
                "blocked_user": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }
        else:
            return {"error": "Pengguna tidak ditemukan"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# ==========================
#     FUNCTION WRAPPER
# ==========================


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
