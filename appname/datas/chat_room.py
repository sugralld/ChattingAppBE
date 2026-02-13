from appname.config import *
from datetime import datetime
import json
from appname import socketio
from appname.utils.crypto_utils import encrypt_text


def createOrGetChatRoom(user_id_first, user_id_second):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 0️⃣ Check if they are friends first
        cur.execute(
            """
            SELECT 1
            FROM user_friends
            WHERE 
                (user_id_first = %s AND user_id_second = %s)
                OR (user_id_first = %s AND user_id_second = %s)
            LIMIT 1;
            """,
            (user_id_first, user_id_second, user_id_second, user_id_first),
        )
        are_friends = cur.fetchone()

        if not are_friends:
            return {
                "success": False,
                "message": "You must be friends to start a chat",
                "status": "not_friends",
            }

        # 1️⃣ Check if chat room already exists (in any order)
        cur.execute(
            """
            SELECT room_id 
            FROM chat_room
            WHERE (user_id_first = %s AND user_id_second = %s)
               OR (user_id_first = %s AND user_id_second = %s)
            LIMIT 1
            """,
            (user_id_first, user_id_second, user_id_second, user_id_first),
        )
        existing = cur.fetchone()

        if existing:
            return {
                "success": True,
                "message": "Chat room already exists",
                "room_id": existing[0],
                "status": "exists",
            }

        # 2️⃣ Create new room_id (increment pattern R00001, R00002, etc.)
        cur.execute("SELECT room_id FROM chat_room ORDER BY room_id DESC LIMIT 1;")
        last_room = cur.fetchone()
        if last_room and last_room[0].startswith("R"):
            last_number = int(last_room[0][1:])
        else:
            last_number = 0
        new_room_id = f"R{last_number + 1:05d}"

        # 3️⃣ Insert new chat room
        cur.execute(
            """
            INSERT INTO chat_room (
                room_id, user_id_first, user_id_second, created_at
            )
            VALUES (%s, %s, %s, NOW());
            """,
            (new_room_id, user_id_first, user_id_second),
        )

        conn.commit()

        return {
            "success": True,
            "message": "New chat room created successfully",
            "room_id": new_room_id,
            "status": "created",
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}

    finally:
        cur.close()
        conn.close()


def sendMessage(room_id, sender_id, message_obj):
    """
    Insert a message using the new normalized schema:
      - messages (message metadata)
      - text_messages (for text content)

    Only supports type == 'text' here; media uploads use dedicated endpoints.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1) Validate room and participant
        cur.execute(
            "SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;",
            (room_id,),
        )
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}
        db_first, db_second = room[0], room[1]

        if sender_id != db_first and sender_id != db_second:
            return {"error": "Sender not a participant of this room"}

        # 2) Determine type and content
        if not isinstance(message_obj, dict):
            return {"error": "Invalid message payload"}

        msg_type = message_obj.get("type")
        if msg_type != "text":
            # For voice/video, use dedicated upload endpoints
            return {"error": "Unsupported message type for this endpoint"}

        text_content = message_obj.get("content", "").strip()
        if not text_content:
            return {"error": "Empty text content"}

        encrypted_text = encrypt_text(text_content)

        # 3) Insert into messages and text_messages
        # messages.message_id is UUID in new schema
        cur.execute(
            """
            INSERT INTO messages (sender_id, room_id, message_type)
            VALUES (%s, %s, 'text')
            RETURNING message_id, sent_at;
            """,
            (sender_id, room_id),
        )
        row = cur.fetchone()
        message_id, sent_at = row[0], row[1]

        cur.execute(
            """
            INSERT INTO text_messages (message_id, text_content)
            VALUES (%s, %s)
            """,
            (message_id, encrypted_text),
        )

        # 4) Update chat_room summary
        cur.execute(
            """
            UPDATE chat_room
               SET last_message = %s,
                   last_message_at = %s
             WHERE room_id = %s;
            """,
            (encrypted_text, sent_at, room_id),
        )

        conn.commit()
        return {
            "success": True,
            "message": "Message sent",
            "message_id": str(message_id),
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


# CORE: delete a message and recalc chat_room last_message
def deleteMessage(message_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1) find room_id for this message in new schema
        cur.execute(
            "SELECT room_id FROM messages WHERE message_id = %s LIMIT 1;",
            (message_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": "Message not found"}
        room_id = row[0]

        # 2) delete the message (cascades delete children like text_messages/voice_notes)
        cur.execute("DELETE FROM messages WHERE message_id = %s;", (message_id,))

        # 3) recalc last message summary for room from remaining messages
        cur.execute(
            """
            SELECT m.message_id, m.message_type, m.sent_at,
                   tm.text_content,
                   mm.media_url
              FROM messages m
              LEFT JOIN text_messages tm ON tm.message_id = m.message_id
              LEFT JOIN media_messages mm ON mm.message_id = m.message_id
             WHERE m.room_id = %s
             ORDER BY m.sent_at DESC
             LIMIT 1;
            """,
            (room_id,),
        )
        last = cur.fetchone()
        if last:
            _, msg_type, last_time, text_content, media_url = last
            if msg_type == "text":
                last_text = text_content or ""
            elif msg_type == "voice":
                last_text = "[Voice]"
            elif msg_type == "video":
                last_text = "[Video]"
            else:
                last_text = "[Message]"
        else:
            last_text = None
            last_time = None

        cur.execute(
            """
            UPDATE chat_room
               SET last_message = %s,
                   last_message_at = %s
             WHERE room_id = %s;
            """,
            (last_text, last_time, room_id),
        )

        conn.commit()
        return {"success": True, "message": "Message deleted", "room_id": room_id}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def getChatRoomsForUser(user_id, limit=10, page=1, search=None):
    """Return list of chat rooms for a user with optional search on friend username."""
    conn = get_db_connection()
    cur = conn.cursor()
    offset = (page - 1) * limit
    try:
        base_sql = """
            SELECT c.room_id, c.user_id_first, c.user_id_second,
                   c.last_message, c.last_message_at,
                   u1.user_id AS u1_id, u1.username AS u1_username, u1.profile_picture AS u1_pic,
                   u2.user_id AS u2_id, u2.username AS u2_username, u2.profile_picture AS u2_pic
            FROM chat_room c
            JOIN user_detail u1 ON c.user_id_first = u1.user_id
            JOIN user_detail u2 ON c.user_id_second = u2.user_id
            WHERE (c.user_id_first = %s OR c.user_id_second = %s)
        """
        params = [user_id, user_id]
        if search:
            # search applies to the other participant's username
            base_sql += " AND ( (c.user_id_first = %s AND u2.username ILIKE %s) OR (c.user_id_second = %s AND u1.username ILIKE %s) )"
            params.extend([user_id, f"%{search}%", user_id, f"%{search}%"])
        base_sql += " ORDER BY c.last_message_at DESC NULLS LAST, c.room_id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cur.execute(base_sql, params)
        rows = cur.fetchall()
        results = []
        for r in rows:
            (
                room_id,
                u_first,
                u_second,
                last_msg,
                last_at,
                u1_id,
                u1_username,
                u1_pic,
                u2_id,
                u2_username,
                u2_pic,
            ) = r
            if user_id == u_first:
                friend_id, friend_username, friend_pic = u2_id, u2_username, u2_pic
            else:
                friend_id, friend_username, friend_pic = u1_id, u1_username, u1_pic
            # format time consistent for Android parser
            if last_at:
                try:
                    last_at_fmt = last_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
                except Exception:
                    last_at_fmt = str(last_at)
            else:
                last_at_fmt = ""
            results.append(
                {
                    "room_id": room_id,
                    "last_message": last_msg or "",
                    "last_message_at": last_at_fmt,
                    "friend": {
                        "user_id": friend_id,
                        "username": friend_username,
                        "profile_picture": friend_pic or "",
                    },
                }
            )
        return {"success": True, "chat_rooms": results}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
