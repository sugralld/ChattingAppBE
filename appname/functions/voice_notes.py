# appname/functions/voice_notes.py
from appname.config import *

from appname.datas.voice_notes import *

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
