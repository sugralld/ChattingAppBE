from appname.config import *

# GET USER FRIENDS (raw DB logic)
def getUserFriends(user_id, limit=10, page=1):
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()

    # Query: find all rows where user_id matches either side,
    # then return the opposite side's id + username
    query = """
        SELECT 
            CASE 
                WHEN uf.user_id_first = %s THEN uf.user_id_second
                ELSE uf.user_id_first
            END AS friend_id,
            CASE 
                WHEN uf.user_id_first = %s THEN uf.username_second
                ELSE uf.username_first
            END AS friend_username,
            uf.created_at
        FROM user_friends uf
        WHERE uf.user_id_first = %s OR uf.user_id_second = %s
        ORDER BY uf.created_at DESC
        LIMIT %s OFFSET %s;
    """

    try:
        cur.execute(query, (user_id, user_id, user_id, user_id, limit, offset))
        rows = cur.fetchall()
        friends = []
        for row in rows:
            friends.append({
                "friend_id": row[0],
                "friend_username": row[1],
                "created_at": row[2],
            })
        return friends
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()

# GET USER FRIENDS BY USERNAME (raw DB logic)
def getUserFriendsByUsername(username, limit=10, page=1):
    offset = (page - 1) * limit
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT 
            CASE 
                WHEN uf.username_first = %s THEN uf.user_id_second
                ELSE uf.user_id_first
            END AS friend_id,
            CASE 
                WHEN uf.username_first = %s THEN uf.username_second
                ELSE uf.username_first
            END AS friend_username,
            uf.created_at
        FROM user_friends uf
        WHERE uf.username_first = %s OR uf.username_second = %s
        ORDER BY uf.created_at DESC
        LIMIT %s OFFSET %s;
    """

    try:
        cur.execute(query, (username, username, username, username, limit, offset))
        rows = cur.fetchall()
        friends = []
        for row in rows:
            friends.append({
                "friend_id": row[0],
                "friend_username": row[1],
                "created_at": row[2],
            })
        return friends
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
