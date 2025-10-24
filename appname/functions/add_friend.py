from appname.config import *
from datetime import datetime
import uuid

########################################
#        SEARCH FRIEND USERNAME        #
########################################
def searchFriendByUsername(user_id, keyword, limit=10, page=1):
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            ud.user_id,
            ud.username,
            ud.profile_picture,
            ud.blocked_user,
            ud.created_at,
            ud.updated_at,
            CASE 
                WHEN uf.user_id_first IS NOT NULL OR uf.user_id_second IS NOT NULL THEN 'connected'
                ELSE 'not connected'
            END AS status
        FROM user_detail ud
        LEFT JOIN user_friends uf 
            ON (
                (
                    uf.user_id_first = %s AND uf.user_id_second = ud.user_id
                    AND uf.username_first = (SELECT username FROM user_detail WHERE user_id = %s)
                    AND uf.username_second = ud.username
                )
                OR 
                (
                    uf.user_id_second = %s AND uf.user_id_first = ud.user_id
                    AND uf.username_second = (SELECT username FROM user_detail WHERE user_id = %s)
                    AND uf.username_first = ud.username
                )
            )
        WHERE ud.username LIKE %s
          AND ud.user_id != %s
        ORDER BY ud.created_at DESC
        LIMIT %s OFFSET %s;
    """

    try:
        cur.execute(query, (user_id, user_id, user_id, user_id, f"%{keyword}%", user_id, limit, offset))
        rows = cur.fetchall()
        results = []
        for row in rows:
            results.append({
                "user_id": row[0],
                "username": row[1],
                "profile_picture": row[2],
                "blocked_user": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "status": row[6]
            })
        return results
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()

########################################
#        SEND FRIEND REQUEST           #
########################################
def sendFriendRequest(sender_id, receiver_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if sender_id == receiver_id:
            return {"error": "You cannot send a friend request to yourself"}

        # Check if users exist
        cur.execute("SELECT user_id, username FROM user_detail WHERE user_id IN (%s, %s)", (sender_id, receiver_id))
        rows = cur.fetchall()
        if len(rows) < 2:
            return {"error": "One or both users not found"}

        usernames = {row[0]: row[1] for row in rows}
        sender_username = usernames.get(sender_id)
        receiver_username = usernames.get(receiver_id)

        # Check if already friends
        cur.execute("""
            SELECT 1 FROM user_friends
            WHERE (user_id_first = %s AND user_id_second = %s)
               OR (user_id_first = %s AND user_id_second = %s)
        """, (sender_id, receiver_id, receiver_id, sender_id))
        if cur.fetchone():
            return {"error": "Users are already friends"}

        # Check if a request already exists and is still pending
        cur.execute("""
            SELECT status FROM friend_request
            WHERE sender = %s AND receiver = %s
            ORDER BY sent_at DESC
            LIMIT 1
        """, (sender_id, receiver_id))
        row = cur.fetchone()
        if row and row[0] == "pending":
            return {"error": "Friend request already sent and still pending"}

        # Insert new friend request
        request_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO friend_request (
                request_id, sender, receiver, sent_at, status
            ) VALUES (%s, %s, %s, %s, %s)
        """, (request_id, sender_id, receiver_id, datetime.now(), "pending"))

        conn.commit()
        return {
            "success": True,
            "message": "Friend request sent successfully",
            "request_id": request_id,
            "sender": {"user_id": sender_id, "username": sender_username},
            "receiver": {"user_id": receiver_id, "username": receiver_username}
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


########################################
#        ACCEPT FRIEND REQUEST         #
########################################
def acceptFriendRequest(request_id, sender_id, receiver_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get usernames
        cur.execute("""
            SELECT user_id, username 
            FROM user_detail 
            WHERE user_id IN (%s, %s)
        """, (sender_id, receiver_id))
        rows = cur.fetchall()
        if len(rows) < 2:
            return {"error": "One or both users not found"}

        usernames = {row[0]: row[1] for row in rows}
        sender_username = usernames.get(sender_id)
        receiver_username = usernames.get(receiver_id)

        # Check if already friends
        cur.execute("""
            SELECT 1 FROM user_friends
            WHERE (user_id_first = %s AND user_id_second = %s)
               OR (user_id_first = %s AND user_id_second = %s)
        """, (sender_id, receiver_id, receiver_id, sender_id))
        if cur.fetchone():
            return {"error": "Users are already friends"}

        # Update friend_request to accepted
        cur.execute("""
            UPDATE friend_request 
            SET status = %s 
            WHERE request_id = %s AND sender = %s AND receiver = %s
        """, ("accepted", request_id, sender_id, receiver_id))
        if cur.rowcount == 0:
            return {"error": "Friend request not found or already processed"}

        # Insert into user_friends
        cur.execute("""
            INSERT INTO user_friends (
                user_id_first, username_first,
                user_id_second, username_second,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            sender_id, sender_username,
            receiver_id, receiver_username,
            datetime.now()
        ))

        # ✅ Delete the friend request record after success
        cur.execute("""
            DELETE FROM friend_request 
            WHERE request_id = %s
        """, (request_id,))

        conn.commit()
        return {
            "success": True,
            "message": "Friend request accepted and deleted successfully",
            "sender": {"user_id": sender_id, "username": sender_username},
            "receiver": {"user_id": receiver_id, "username": receiver_username}
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


########################################
#          FUNCTION WRAPPERS           #
########################################
def funcSearchFriendByUsername(user_id, keyword, limit=10, page=1):
    try:
        results = searchFriendByUsername(user_id, keyword, limit, page)
        if isinstance(results, dict) and "error" in results:
            return {"status": "error", "code": 404, "message": results["error"], "data": []}

        return {"status": "success", "code": 0, "message": "", "data": results}
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcSendFriendRequest(sender_id, receiver_id):
    try:
        result = sendFriendRequest(sender_id, receiver_id)
        if isinstance(result, dict) and "error" in result:
            return {"status": "error", "code": 400, "message": result["error"], "data": []}

        return {"status": "success", "code": 0, "message": result["message"], "data": [result]}
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcAcceptFriendRequest(request_id, sender_id, receiver_id):
    try:
        result = acceptFriendRequest(request_id, sender_id, receiver_id)
        if isinstance(result, dict) and "error" in result:
            return {"status": "error", "code": 400, "message": result["error"], "data": []}

        return {"status": "success", "code": 0, "message": result["message"], "data": [result]}
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}
