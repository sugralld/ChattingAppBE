from appname.datas.video_notes import *

def funcUploadVideoNote(media_url, file_size, resolution, frame_rate):
    return storeTempVideoNote(media_url, file_size, resolution, frame_rate)


def funcSendVideoNote(sender_id, room_id, media_url, file_size, resolution, frame_rate):
    try:
        result = insertVideoNote(sender_id, room_id, media_url, file_size, resolution, frame_rate)

        if isinstance(result, dict) and result.get("status") == "error":
            return {
                "status": "error",
                "code": 400,
                "message": result.get("message"),
                "data": [],
            }

        success_data = {
            "message_id": result.get("message_id"),
            "media_url": media_url,
            "file_size": file_size,
            "resolution": resolution,
            "frame_rate": frame_rate,
        }

        return {
            "status": "success",
            "code": 0,
            "message": "Video note sent",
            "data": [success_data],
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": [],
        }


def funcGetVideoNotes(room_id, limit=20, page=1):
    try:
        result = getVideoNotes(room_id, limit, page)

        if isinstance(result, dict) and "error" in result:
            return {
                "status": "error",
                "code": 400,
                "message": result.get("error"),
                "data": [],
            }

        return {
            "status": "success",
            "code": 0,
            "message": "Video notes retrieved",
            "data": result,
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": [],
        }


def funcUpdateVideoNoteTranslateStatus(message_id, translate_yn='Y'):
    try:
        result = updateVideoNoteTranslateStatus(message_id, translate_yn)

        if result.get("status") == "error":
            return {
                "status": "error",
                "code": 400,
                "message": result.get("message"),
                "data": [],
            }

        return {
            "status": "success",
            "code": 0,
            "message": "Video note translation status updated",
            "data": [],
        }

    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": [],
        }
