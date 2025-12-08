from appname.config import *
from datetime import datetime
import json

from flask import request, jsonify
from flask_socketio import SocketIO, emit


def sendMessage(room_id, sender_id, message_obj):
    """
    New schema insert for text messages:
      - Insert into messages (UUID, sender_id, room_id, message_type='text')
      - Insert into text_messages with the same message_id
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Validate room
        cur.execute(
            "SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;",
            (room_id,),
        )
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}
        db_first, db_second = room[0], room[1]

        if sender_id not in (db_first, db_second):
            return {"error": "Sender not a participant of this room"}

        if not isinstance(message_obj, dict):
            return {"error": "Invalid message payload"}

        msg_type = message_obj.get("type")
        if msg_type != "text":
            return {"error": "Unsupported message type for this endpoint"}

        text_content = (message_obj.get("content") or "").strip()
        if not text_content:
            return {"error": "Empty text content"}

        # Insert into messages and text_messages
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
            (message_id, text_content),
        )

        # Update chat_room summary
        cur.execute(
            """
            UPDATE chat_room
               SET last_message = %s,
                   last_message_at = %s
             WHERE room_id = %s;
            """,
            (text_content, sent_at, room_id),
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


########################################
#  GET MESSAGES FOR ROOM CORE          #
########################################
def getMessagesForRoom(room_id, viewer_user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Validate room and membership
        cur.execute(
            "SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;",
            (room_id,),
        )
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}
        db_user_first, db_user_second = room[0], room[1]
        if viewer_user_id not in (db_user_first, db_user_second):
            return {"error": "Viewer not a participant of this room"}

        # Fetch unified messages
        cur.execute(
            """
            SELECT m.message_id,
                   m.room_id,
                   m.sender_id,
                   m.message_type,
                   m.sent_at,
                   tm.text_content,
                   mm.media_url,
                   vn.duration_sec,
                   vn.transcript_text
              FROM messages m
              LEFT JOIN text_messages tm ON tm.message_id = m.message_id
              LEFT JOIN voice_notes vn ON vn.message_id = m.message_id
              LEFT JOIN media_messages mm ON mm.message_id = m.message_id
             WHERE m.room_id = %s
             ORDER BY m.sent_at ASC, m.message_id ASC;
            """,
            (room_id,),
        )
        rows = cur.fetchall()

        messages = []
        for r in rows:
            (
                message_id,
                r_id,
                sender_id,
                message_type,
                sent_at,
                text_content,
                media_url,
                duration_sec,
                transcript_text,
            ) = r
            messages.append(
                {
                    "message_id": str(message_id),
                    "room_id": r_id,
                    "sender_id": sender_id,
                    "message_type": message_type,
                    "content": text_content if message_type == "text" else None,
                    "media_url": (
                        media_url if message_type in ("voice", "video") else None
                    ),
                    "duration_sec": (
                        int(duration_sec) if duration_sec is not None else None
                    ),
                    "transcript_text": transcript_text,
                    "sent_at": sent_at,
                }
            )

        return {"success": True, "room_id": room_id, "messages": messages}

    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()


def getSingleMessage(message_id, viewer_user_id):
    """
    Fetch a single message by message_id.
    Optimized for realtime updates - returns just one message.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Fetch the message with all related data
        cur.execute(
            """
            SELECT m.message_id,
                   m.room_id,
                   m.sender_id,
                   m.message_type,
                   m.sent_at,
                   tm.text_content,
                   mm.media_url,
                   vn.duration_sec,
                   vn.transcript_text
              FROM messages m
              LEFT JOIN text_messages tm ON tm.message_id = m.message_id
              LEFT JOIN voice_notes vn ON vn.message_id = m.message_id
              LEFT JOIN media_messages mm ON mm.message_id = m.message_id
             WHERE m.message_id = %s
             LIMIT 1;
            """,
            (message_id,),
        )
        row = cur.fetchone()

        if not row:
            return {"error": "Message not found"}

        (
            msg_id,
            room_id,
            sender_id,
            message_type,
            sent_at,
            text_content,
            media_url,
            duration_sec,
            transcript_text,
        ) = row

        # Verify viewer has access to this room
        cur.execute(
            "SELECT user_id_first, user_id_second FROM chat_room WHERE room_id = %s LIMIT 1;",
            (room_id,),
        )
        room = cur.fetchone()
        if not room:
            return {"error": "Room not found"}

        db_user_first, db_user_second = room[0], room[1]
        if viewer_user_id not in (db_user_first, db_user_second):
            return {"error": "Viewer not authorized to view this message"}

        message_data = {
            "message_id": str(msg_id),
            "room_id": room_id,
            "sender_id": sender_id,
            "message_type": message_type,
            "content": text_content if message_type == "text" else None,
            "media_url": media_url if message_type in ("voice", "video") else None,
            "duration_sec": int(duration_sec) if duration_sec is not None else None,
            "transcript_text": transcript_text,
            "sent_at": (
                sent_at.isoformat() if sent_at else None
            ),  # ✅ Convert to ISO string
        }

        return message_data

    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()
