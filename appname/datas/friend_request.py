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


########################################
#            FUNCTION WRAPPER           #
########################################


def funcGetFriendRequests(receiver, limit=10, page=1):
    try:
        results = getFriendRequests(receiver, limit, page)

        if isinstance(results, dict) and "error" in results:
            return {
                "status": "error",
                "code": 404,
                "message": results["error"],
                "data": [],
            }

        formatted_data = []
        for row in results:
            formatted_data.append(
                {
                    "request_id": row.get("request_id"),
                    "sender_id": row.get("sender"),
                    "sender_username": row.get("sender_username"),
                    "receiver": row.get("receiver"),
                    "sent_at": row.get("sent_at"),
                    "status": row.get("status"),
                }
            )

        return {"status": "success", "code": 0, "message": "", "data": formatted_data}

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcRejectFriendRequest(request_id):
    try:
        result = rejectFriendRequest(request_id)

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


def funcAcceptFriendRequest(request_id):
    try:
        result = acceptFriendRequest(request_id)

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
            "data": {"sender": result["sender"], "receiver": result["receiver"]},
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}
