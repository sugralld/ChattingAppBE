from appname.config import *
from datetime import datetime
import json
from appname import socketio

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
    Save a message to the database with message_id like M00001, M00002.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1) Check room exists
        cur.execute("SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;", (room_id,))
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}
        db_first, db_second = room[0], room[1]

        if sender_id != db_first and sender_id != db_second:
            return {"error": "Sender not a participant of this room"}

        now = datetime.utcnow()

        # 2) Generate new message_id - FIXED for text message_id
        cur.execute("""
            SELECT message_id FROM message
            ORDER BY message_id DESC
            LIMIT 1;
        """)
        last = cur.fetchone()
        if last:
            # Extract numeric part from text like "M00001"
            last_num = int(last[0][1:])  # Remove "M" and convert to int
            new_msg_id = f"M{last_num + 1:05d}"
        else:
            new_msg_id = "M00001"

        # 3) Insert into message table
        if sender_id == db_first:
            cur.execute("""
                INSERT INTO message (
                    message_id, room_id, message_first, message_second, user_id_first, user_id_second, sent_at_first
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (new_msg_id, room_id, json.dumps(message_obj), None, db_first, db_second, now))
        else:
            cur.execute("""
                INSERT INTO message (
                    message_id, room_id, message_first, message_second, user_id_first, user_id_second, sent_at_second
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (new_msg_id, room_id, None, json.dumps(message_obj), db_first, db_second, now))

        # 4) Update chat_room last_message and last_message_at
        if isinstance(message_obj, dict):
            last_message_text = message_obj.get("text", str(message_obj))
        else:
            last_message_text = str(message_obj)
            
        cur.execute("""
            UPDATE chat_room
            SET last_message = %s, last_message_at = %s
            WHERE room_id = %s;
        """, (last_message_text, now, room_id))

        conn.commit()
        return {"success": True, "message": "Message sent", "message_id": new_msg_id}

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
        # 1) find room_id for this message
        cur.execute("SELECT room_id FROM message WHERE message_id = %s LIMIT 1;", (message_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Message not found"}
        room_id = row[0]

        # 2) delete the message
        cur.execute("DELETE FROM message WHERE message_id = %s;", (message_id,))

        # 3) recalc last_message for the room (pick latest sent_at among remaining messages)
        cur.execute("""
            SELECT message_first, message_second, sent_at_first, sent_at_second
            FROM message
            WHERE room_id = %s
            ORDER BY COALESCE(sent_at_first, sent_at_second) DESC, message_id DESC
            LIMIT 1;
        """, (room_id,))
        last = cur.fetchone()
        if last:
            m_first, m_second, t_first, t_second = last
            if t_first is None and t_second is None:
                last_text = None
                last_time = None
            else:
                if (t_first or datetime.min) >= (t_second or datetime.min):
                    # first is latest
                    last_text = (m_first.get("text") if isinstance(m_first, dict) else (json.loads(m_first).get("text") if m_first else None)) if m_first else None
                    last_time = t_first
                else:
                    last_text = (m_second.get("text") if isinstance(m_second, dict) else (json.loads(m_second).get("text") if m_second else None)) if m_second else None
                    last_time = t_second
        else:
            last_text = None
            last_time = None

        cur.execute("""
            UPDATE chat_room
            SET last_message = %s, last_message_at = %s
            WHERE room_id = %s;
        """, (last_text, last_time, room_id))

        conn.commit()
        return {"success": True, "message": "Message deleted", "room_id": room_id}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
