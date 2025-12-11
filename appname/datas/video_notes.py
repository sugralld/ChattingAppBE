import uuid
from datetime import datetime
from appname.config import *

# ======================================
# Temporary Upload (NO DB insert)
# ======================================
def storeTempVideoNote(media_url, file_size, resolution, frame_rate):
    return {
        "status": "success",
        "message": "Video uploaded",
        "media_url": media_url,
        "file_size": file_size,
        "resolution": resolution,
        "frame_rate": frame_rate,
    }

# ======================================
# Actual SEND to DB
# ======================================
def insertVideoNote(sender_id, room_id, media_url, file_size, resolution, frame_rate):
    conn = get_db_connection()
    cur = conn.cursor()
    print("Sending video note...")

    try:
        message_id = str(uuid.uuid4())

        # Insert into messages
        cur.execute(
            """
            INSERT INTO messages (message_id, sender_id, room_id, message_type)
            VALUES (%s, %s, %s, 'video');
        """,
            (message_id, sender_id, room_id),
        )

        # Insert into media_messages
        cur.execute(
            """
            INSERT INTO media_messages (message_id, media_url, file_size)
            VALUES (%s, %s, %s)
        """,
            (message_id, media_url, file_size),
        )

        # Insert into video_notes
        cur.execute(
            """
            INSERT INTO video_notes (message_id, resolution, frame_rate)
            VALUES (%s, %s, %s)
        """,
            (message_id, resolution, frame_rate),
        )

        # Update chat room summary
        cur.execute(
            """
            UPDATE chat_room
               SET last_message = %s,
                   last_message_at = (SELECT sent_at FROM messages WHERE message_id = %s)
             WHERE room_id = %s;
            """,
            ("[Video]", message_id, room_id),
        )

        conn.commit()

        return {
            "status": "success",
            "message": "Video note sent",
            "message_id": message_id,
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cur.close()
        conn.close()


# ===============================
# UPDATE Video Notes translate_yn
# ===============================
def updateVideoNoteTranslateStatus(message_id, translate_yn='Y'):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
                        UPDATE video_notes
                             SET translate_yn = %s
                         WHERE message_id::text = %s;
            """,
            (translate_yn, message_id),
        )

        conn.commit()

        return {
            "status": "success",
            "message": "Video note translation status updated",
        }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}

    finally:
        cur.close()
        conn.close()


def updateVideoNoteTranslateYN(message_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if message_id exists in translate_video (compare as text to avoid uuid cast errors)
        cur.execute("SELECT message_id FROM translate_video WHERE message_id::text = %s LIMIT 1", (message_id,))
        exists = cur.fetchone()
        translate_yn = 'Y' if exists else 'N'

        # Update video_notes.translate_yn
        cur.execute(
            "UPDATE video_notes SET translate_yn = %s WHERE message_id::text = %s",
            (translate_yn, message_id),
        )
        conn.commit()
        return {"status": "success", "translate_yn": translate_yn}

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
        conn.close()


# ===============================
# GET Video Notes (No Change)
# ===============================
def getVideoNotes(room_id, limit=20, page=1):
    conn = get_db_connection()
    cur = conn.cursor()

    offset = (page - 1) * limit

    try:
        query = """
            SELECT  m.message_id, m.sender_id, m.sent_at,
                    mm.media_url, mm.file_size,
                    vn.resolution, vn.frame_rate, vn.translate_yn
              FROM messages m
        JOIN media_messages mm ON m.message_id = mm.message_id
        JOIN video_notes vn     ON m.message_id = vn.message_id
             WHERE m.room_id = %s AND m.message_type = 'video'
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
                    "resolution": r[5],
                    "frame_rate": r[6],
                    "translate_yn": r[7],
                }
            )

        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        cur.close()
        conn.close()
