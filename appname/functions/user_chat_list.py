from appname.datas.user_chat_list import *

def funcGetChatRoomList(user_id, limit, page, search=""):
    try:
        result = getChatRoomList(user_id, limit, page, search)
        if isinstance(result, dict) and "error" in result:
            return {"status": "error", "code": 404, "message": result["error"], "data": []}
        return {"status": "success", "code": 0, "message": "", "data": result}
    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": []}
