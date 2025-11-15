from appname.config import *
from datetime import datetime


# GET FRIEND REQUEST LIST
def getFriendRequests(receiver, limit=10, page=1):
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            fr.request_id,
            fr.sender,
            u.username AS sender_username,
            fr.receiver,
            fr.sent_at,
            fr.status
        FROM friend_request fr
        JOIN user_detail u ON fr.sender = u.user_id
        WHERE fr.receiver = %s
        ORDER BY fr.sent_at DESC
        LIMIT %s OFFSET %s;
    """

    try:
        cur.execute(query, (receiver, limit, offset))
        rows = cur.fetchall()
        requests = []
        for row in rows:
            requests.append(
                {
                    "request_id": row[0],
                    "sender": row[1],
                    "sender_username": row[2],
                    "receiver": row[3],
                    "sent_at": row[4],
                    "status": row[5],  # pending / accepted / rejected
                }
            )
        return requests
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# REJECT FRIEND REQUEST (DELETE)
def rejectFriendRequest(request_id):
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        DELETE FROM friend_request
        WHERE request_id = %s
    """

    try:
        cur.execute(query, (request_id,))
        conn.commit()

        if cur.rowcount == 0:
            return {"error": f"No friend request found with id {request_id}"}

        return {"success": True, "message": "Friend request rejected successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# ACCEPT FRIEND REQUEST (DELETE + INSERT TO user_friends)
def acceptFriendRequest(request_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Get request details
        cur.execute(
            """
            SELECT request_id, sender, receiver, sent_at, status
            FROM friend_request
            WHERE request_id = %s
        """,
            (request_id,),
        )
        row = cur.fetchone()

        if not row:
            return {"error": f"No friend request found with id {request_id}"}

        sender = row[1]
        receiver = row[2]

        # 2. Delete the friend request
        cur.execute(
            """
            DELETE FROM friend_request WHERE request_id = %s
        """,
            (request_id,),
        )

        # 3. Insert into user_friends (sender -> user_id_first, receiver -> user_id_second)
        cur.execute(
            """
            INSERT INTO user_friends (
                user_id_first, username_first,
                user_id_second, username_second,
                created_at
            )
            SELECT 
                uf1.user_id, uf1.username,
                uf2.user_id, uf2.username,
                %s
            FROM users uf1, users uf2
            WHERE uf1.user_id = %s AND uf2.user_id = %s
        """,
            (datetime.now(), sender, receiver),
        )

        conn.commit()

        return {
            "success": True,
            "message": "Friend request accepted and added to user_friends",
            "sender": sender,
            "receiver": receiver,
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}

    finally:
        cur.close()
        conn.close()
