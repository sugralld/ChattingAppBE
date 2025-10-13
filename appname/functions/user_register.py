from appname.config import *
import bcrypt
import re


def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password minimal 8 karakter"
    if not re.search(r"[A-Za-z]", password):
        return False, "Password harus mengandung huruf"
    if not re.search(r"\d", password):
        return False, "Password harus mengandung angka"
    return True, "Password valid"


def check_user_exists(email, username):
    """Check if user already exists"""
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT user_id FROM user_detail 
        WHERE user_email = %s OR username = %s
        LIMIT 1;
    """

    try:
        cur.execute(query, (email, username))
        result = cur.fetchone()
        return result is not None
    except Exception as e:
        raise Exception(f"Error checking user: {e}")
    finally:
        cur.close()
        conn.close()


def registerUser(data):
    """Register new user with validation and password hashing"""
    try:
        # Extract data
        email = data.get("user_email", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        profile_picture = data.get("profile_picture", "")

        # Validation
        if not email or not username or not password:
            return {"error": "Email, username, dan password wajib diisi"}

        if not validate_email(email):
            return {"error": "Format email tidak valid"}

        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return {"error": password_message}

        if len(username) < 3:
            return {"error": "Username minimal 3 karakter"}

        # Check if user exists
        if check_user_exists(email, username):
            return {"error": "Email atau username sudah terdaftar"}

        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Generate new user ID
        conn = get_db_connection()
        cur = conn.cursor()

        id_query = "SELECT user_id FROM user_detail ORDER BY created_at DESC LIMIT 1;"
        cur.execute(id_query)
        last_id = cur.fetchone()
        if last_id:
            number = int(last_id[0][1:]) + 1
            new_user_id = f"U{number:05d}"
        else:
            new_user_id = "U00001"

        # Insert user
        query = """
            INSERT INTO user_detail (
                user_id,
                user_email,
                username,
                password_hash,
                profile_picture,
                blocked_user,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW());
        """

        cur.execute(
            query, (new_user_id, email, username, password_hash, profile_picture, False)
        )
        conn.commit()

        return {
            "message": "Registrasi berhasil",
            "user_id": new_user_id,
            "user_email": email,
            "username": username,
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def funcRegisterUser(data):
    """Function wrapper for user registration"""
    try:
        result = registerUser(data)

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
            "data": [
                {
                    "user_id": result["user_id"],
                    "user_email": result["user_email"],
                    "username": result["username"],
                }
            ],
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}
