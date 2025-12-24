from appname.config import *

# GET USER DETAIL
def getUserDetail(limit=10, page=1):
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            user_id,
            user_email,
            username,
            dob,
            profile_picture,
            blocked_user,
            created_at,
            updated_at,
            dob,
            bio
        FROM user_detail
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s;
    """

    try:
        cur.execute(query, (limit, offset))
        rows = cur.fetchall()
        users = []
        for row in rows:
            users.append(
                {
                    "user_id": row[0],
                    "user_email": row[1],
                    "username": row[2],
                    "profile_picture": row[3],
                    "blocked_user": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "dob": row[7],
                    "bio": row[8],
                }
            )
        return users
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# GET USER DETAIL BY ID
def getUserDetailByID(user_id):
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
            dob,
            bio
        FROM user_detail
        WHERE user_id = %s;
    """

    try:
        cur.execute(query, (user_id,))
        row = cur.fetchone()
        if row:
            return {
                "user_id": row[0],
                "user_email": row[1],
                "username": row[2],
                "profile_picture": row[3],
                "blocked_user": row[4],
                "created_at": row[5],
                "updated_at": row[6],
                "dob": row[7],
                "bio": row[8],
            }
        else:
            return {"error": f"User with ID {user_id} not found"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# INSERT USER DETAIL
def insertUserDetail(data):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get latest user_id and increment it
    id_query = "SELECT user_id FROM user_detail ORDER BY created_at DESC LIMIT 1;"
    cur.execute(id_query)
    last_id = cur.fetchone()
    if last_id:
        try:
            # Extract number from format "U00001"
            number = int(last_id[0][1:]) + 1
            new_user_id = f"U{number:05d}"
        except ValueError:
            # Fallback if ID format is different
            import uuid
            new_user_id = str(uuid.uuid4())[:8]
    else:
        new_user_id = "U00001"

    query = """
        INSERT INTO user_detail (
            user_id,
            user_email,
            username,
            password_hash,
            profile_picture,
            blocked_user,
            dob,
            bio,
            created_at,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
    """
    try:
        cur.execute(
            query,
            (
                new_user_id,
                data.get("user_email"),
                data.get("username"),
                data.get("password"),
                data.get("profile_picture"),
                data.get("blocked_user", False),
                data.get("dob"),
                data.get("bio"),
            ),
        )
        conn.commit()
        return {"message": "User inserted successfully", "user_id": new_user_id}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# UPDATE USER DETAIL
def updateUserDetail(user_id, data):
    conn = get_db_connection()
    cur = conn.cursor()

    # Dynamic update query builder
    fields = []
    values = []

    if "user_email" in data:
        fields.append("user_email = %s")
        values.append(data["user_email"])
    if "username" in data:
        fields.append("username = %s")
        values.append(data["username"])
    if "password" in data:
        fields.append("password_hash = %s")
        values.append(data["password"])
    if "profile_picture" in data:
        fields.append("profile_picture = %s")
        values.append(data["profile_picture"])
    if "blocked_user" in data:
        fields.append("blocked_user = %s")
        values.append(data["blocked_user"])
    if "dob" in data:
        fields.append("dob = %s")
        values.append(data["dob"])
    if "bio" in data:
        fields.append("bio = %s")
        values.append(data["bio"])

    if not fields:
        return {"message": "No fields to update"}

    fields.append("updated_at = NOW()")
    
    query = f"UPDATE user_detail SET {', '.join(fields)} WHERE user_id = %s;"
    values.append(user_id)

    try:
        cur.execute(query, tuple(values))
        conn.commit()
        if cur.rowcount == 0:
            return {"error": f"User with ID {user_id} not found"}
        return {"message": "User updated successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# Update only profile fields (username, user_email, dob) - only when changed
def updateUserProfile(user_id, username=None, user_email=None, dob=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch current values
        cur.execute(
            "SELECT username, user_email, dob FROM user_detail WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"User with ID {user_id} not found"}

        current_username, current_email, current_dob = row

        updates = []
        params = []

        if username is not None and username != current_username:
            updates.append("username = %s")
            params.append(username)
        if user_email is not None and user_email != current_email:
            updates.append("user_email = %s")
            params.append(user_email)
        if dob is not None and dob != current_dob:
            updates.append("dob = %s")
            params.append(dob)

        if not updates:
            return {"message": "No changes detected"}

        query = f"UPDATE user_detail SET {', '.join(updates)}, updated_at = NOW() WHERE user_id = %s;"
        params.append(user_id)
        cur.execute(query, tuple(params))
        conn.commit()
        return {"message": "Profile updated successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# Authentication related helpers
def getUserAuthInfo(user_id):
    """Return user_email and password_hash and verification_code for a given user_id"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT user_email, password_hash, verification_code FROM user_detail WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"User with ID {user_id} not found"}
        return {"user_email": row[0], "password_hash": row[1], "verification_code": row[2]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def getUserAuthInfoByEmail(user_email):
    """Return user_id, password_hash and verification_code for a given user_email"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT user_id, password_hash, verification_code FROM user_detail WHERE user_email = %s",
            (user_email,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"User with email {user_email} not found"}
        return {"user_id": row[0], "password_hash": row[1], "verification_code": row[2]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def setVerificationCode(user_id, code):
    """Store verification code for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE user_detail SET verification_code = %s, updated_at = NOW() WHERE user_id = %s",
            (code, user_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"error": f"User with ID {user_id} not found"}
        return {"message": "Verification code set"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def getVerificationCode(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT verification_code FROM user_detail WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"User with ID {user_id} not found"}
        return {"verification_code": row[0]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def updatePasswordHash(user_id, new_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE user_detail SET password_hash = %s, verification_code = NULL, updated_at = NOW() WHERE user_id = %s",
            (new_hash, user_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"error": f"User with ID {user_id} not found"}
        return {"message": "Password updated"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# DELETE USER DETAIL
def deleteUserDetail(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    query = "DELETE FROM user_detail WHERE user_id = %s;"
    try:
        cur.execute(query, (user_id,))
        conn.commit()
        if cur.rowcount == 0:
            return {"error": f"User with ID {user_id} not found"}
        return {"message": "User deleted successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()