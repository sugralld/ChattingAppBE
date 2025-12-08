from appname.config import *


def getChatRoomList(user_id, limit, page, search=""):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        offset = (page - 1) * limit

        # 1) Find chat rooms where user is participant
        query = """
            SELECT room_id, user_id_first, user_id_second, created_at, last_message, last_message_at
            FROM chat_room
            WHERE user_id_first = %s OR user_id_second = %s
            ORDER BY COALESCE(last_message_at, created_at) DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (user_id, user_id, limit, offset))
        rooms = cur.fetchall()
        if not rooms:
            return {"error": "No chat rooms found"}

        result = []

        for r in rooms:
            (
                room_id,
                user_first,
                user_second,
                created_at,
                last_message,
                last_message_at,
            ) = r

            # Determine friend_id (the other user)
            friend_id = user_second if user_id == user_first else user_first

            # Fetch friend's data from user_detail
            if search:
                cur.execute(
                    """
                    SELECT user_id, username, profile_picture 
                    FROM user_detail 
                    WHERE user_id = %s AND username ILIKE %s
                """,
                    (friend_id, f"%{search}%"),
                )
            else:
                cur.execute(
                    """
                    SELECT user_id, username, profile_picture 
                    FROM user_detail 
                    WHERE user_id = %s
                """,
                    (friend_id,),
                )
            friend_data = cur.fetchone()
            if not friend_data:
                continue  # skip if search filter doesn't match

            friend_user_id, username, profile_picture = friend_data

            #  Use last_message and last_message_at directly from chat_room table
            result.append(
                {
                    "room_id": room_id,
                    "created_at": created_at,
                    "last_message": last_message,  # From chat_room table
                    "last_message_at": last_message_at,  # From chat_room table
                    "friend": {
                        "user_id": friend_user_id,
                        "username": username,
                        "profile_picture": profile_picture,
                    },
                }
            )

        return {"success": True, "user_id": user_id, "chat_rooms": result}

    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
