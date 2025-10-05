from appname.config import *
import bcrypt
import re


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
            profile_picture,
            blocked_user,
            created_at,
            updated_at
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
            updated_at
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
        number = int(last_id[0][1:]) + 1
        new_user_id = f"U{number:05d}"
    else:
        new_user_id = "U00001"

    query = """
        INSERT INTO user_detail (
            user_id,
            user_email,
            username,
            password_hash,  -- FIXED HERE
            profile_picture,
            blocked_user,
            created_at,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW());
    """
    try:
        cur.execute(
            query,
            (
                new_user_id,
                data["user_email"],
                data["username"],
                data["password"],  # NOTE: you can hash it here if needed
                data.get("profile_picture"),
                data.get("blocked_user", False),
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

    query = """
        UPDATE user_detail
        SET 
            user_email = %s,
            username = %s,
            password_hash = %s,  -- FIXED HERE
            profile_picture = %s,
            blocked_user = %s,
            updated_at = NOW()
        WHERE user_id = %s;
    """
    try:
        cur.execute(
            query,
            (
                data["user_email"],
                data["username"],
                data["password"],  # Again, hash it if needed
                data.get("profile_picture"),
                data.get("blocked_user", False),
                user_id,
            ),
        )
        conn.commit()
        if cur.rowcount == 0:
            return {"error": f"User with ID {user_id} not found"}
        return {"message": "User updated successfully"}
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


########################################
#               FUNCTION               #
########################################


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
