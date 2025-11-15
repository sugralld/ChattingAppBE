# appname/functions/voice_notes.py
from appname.config import *
from datetime import datetime
import requests
import uuid


######################################
# INSERT VOICE NOTE (UPLOAD)
######################################
def insertVoiceNote(sender_id, room_id, media_url, file_size, duration_sec):
    conn = get_db_connection()
    cur = conn.cursor()
    print("Inserting voice note...")    

    try:
        message_id = str(uuid.uuid4())

        cur.execute(
            """
            INSERT INTO messages (message_id, sender_id, room_id, message_type)
            VALUES (%s, %s, %s, 'voice')
        """,
            (message_id, sender_id, room_id),
        )

        cur.execute(
            """
            INSERT INTO media_messages (message_id, media_url, file_size)
            VALUES (%s, %s, %s)
        """,
            (message_id, media_url, file_size),
        )

        cur.execute(
            """
            INSERT INTO voice_notes (message_id, duration_sec)
            VALUES (%s, %s)
        """,
            (message_id, duration_sec),
        )

        conn.commit()
        print("Voice note inserted with message_id:", message_id)

        return {
            "status": "success",
            "message": "Voice note inserted",
            "message_id": message_id,
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cur.close()
        conn.close()


########################################
#       GET VOICE NOTES PER ROOM       #
########################################
def getVoiceNotes(room_id, limit=20, page=1):
    conn = get_db_connection()
    cur = conn.cursor()

    offset = (page - 1) * limit

    try:
        query = """
            SELECT m.message_id, m.sender_id, m.sent_at,
                   mm.media_url, mm.file_size,
                   vn.duration_sec, vn.transcript_text
            FROM messages m
            JOIN media_messages mm ON m.message_id = mm.message_id
            JOIN voice_notes vn ON m.message_id = vn.message_id
            WHERE m.room_id = %s AND m.message_type = 'voice'
            ORDER BY sent_at DESC
            LIMIT %s OFFSET %s;
        """

        cur.execute(query, (room_id, limit, offset))
        rows = cur.fetchall()

        result = []
        for r in rows:
            result.append(
                {
                    "message_id": r[0],
                    "sender_id": r[1],
                    "sent_at": r[2],
                    "media_url": r[3],
                    "file_size": r[4],
                    "duration_sec": r[5],
                    "transcript_text": r[6],
                }
            )

        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cur.close()
        conn.close()


########################################
#           WRAPPER FUNCTIONS          #
########################################
def funcInsertVoiceNote(sender_id, receiver_id, voice_data_bytes, file_name):
    try:
        result = insertVoiceNote(sender_id, receiver_id, voice_data_bytes, file_name)

        if "error" in result:
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
            "data": [result],
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}


def funcGetVoiceNotes(sender_id, receiver_id, limit=10, page=1):
    try:
        result = getVoiceNotes(sender_id, receiver_id, limit, page)

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
            "message": "",
            "data": result,
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}
