from appname.config import *
from datetime import datetime
import json

from flask import request, jsonify
from flask_socketio import SocketIO, emit 

def sendMessage(room_id, sender_id, message_obj):
    """
    Save a message to the database.
    Returns {"success": True, "message_id": ...} or {"error": "..."}.
    Generates message_id like M00001, M00002, etc.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1) check room exists
        cur.execute("SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;", (room_id,))
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}
        db_first, db_second = room[0], room[1]

        if sender_id != db_first and sender_id != db_second:
            return {"error": "Sender not a participant of this room"}

        now = datetime.utcnow()

        # 2) generate custom message_id
        cur.execute("SELECT message_id FROM message ORDER BY message_id DESC LIMIT 1;")
        last = cur.fetchone()
        if last and last[0].startswith("M"):
            last_num = int(last[0][1:])
            new_msg_id = f"M{last_num + 1:05d}"  # M00001, M00002...
        else:
            new_msg_id = "M00001"

        # 3) insert message depending on sender
        if sender_id == db_first:
            cur.execute("""
                INSERT INTO message (message_id, room_id, message_first, message_second, user_id_first, user_id_second, sent_at_first)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (new_msg_id, room_id, json.dumps(message_obj), None, db_first, db_second, now))
        else:
            cur.execute("""
                INSERT INTO message (message_id, room_id, message_first, message_second, user_id_first, user_id_second, sent_at_second)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (new_msg_id, room_id, None, json.dumps(message_obj), db_first, db_second, now))

        conn.commit()
        # ✅ Return the formatted Mxxxxx ID
        return {"success": True, "message": "Message sent", "message_id": new_msg_id}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


########################################
#  GET MESSAGES FOR ROOM CORE          #
########################################
def getMessagesForRoom(room_id, viewer_user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1) check room exists
        cur.execute("SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;", (room_id,))
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}

        db_user_first, db_user_second = room[0], room[1]

        # 2) fetch messages for room ordered by time (earliest -> latest)
        cur.execute("""
            SELECT message_id, room_id, message_first, message_second, user_id_first, user_id_second,
                   sent_at_first, sent_at_second
            FROM message
            WHERE room_id = %s
            ORDER BY COALESCE(sent_at_first, sent_at_second) ASC, message_id ASC;
        """, (room_id,))
        rows = cur.fetchall()

        # 3) Decide if viewer is in same orientation or reversed
        reversed_view = False
        if viewer_user_id == db_user_second and viewer_user_id != db_user_first:
            reversed_view = True
        elif viewer_user_id != db_user_first and viewer_user_id != db_user_second:
            return {"error": "Viewer not a participant of this room"}

        # 4) Build message list with reversal applied only to output (no DB changes)
        messages = []
        for r in rows:
            message_id, room_id, m_first, m_second, u_first, u_second, t_first, t_second = r
            if not reversed_view:
                messages.append({
                    "message_id": message_id,
                    "room_id": room_id,
                    "message_first": m_first,
                    "message_second": m_second,
                    "user_id_first": u_first,
                    "user_id_second": u_second,
                    "sent_at_first": t_first,
                    "sent_at_second": t_second,
                    "sent_at": t_first if t_first is not None else t_second,
                    "sender": u_first if t_first is not None else u_second,
                })
            else:
                messages.append({
                    "message_id": message_id,
                    "room_id": room_id,
                    "message_first": m_second,
                    "message_second": m_first,
                    "user_id_first": u_second,
                    "user_id_second": u_first,
                    "sent_at_first": t_second,
                    "sent_at_second": t_first,
                    "sent_at": t_second if t_second is not None else t_first,
                    "sender": u_second if t_second is not None else u_first,
                })

        return {"success": True, "room_id": room_id, "viewer_reversed": reversed_view, "messages": messages}

    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()