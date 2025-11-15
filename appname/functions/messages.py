from appname.config import *
from datetime import datetime
import json

from flask import request, jsonify
from flask_socketio import SocketIO, emit 
from appname.datas.messages import *

def funcGetMessagesForRoom(room_id, viewer_user_id):
    try:
        result = getMessagesForRoom(room_id, viewer_user_id)
        if isinstance(result, dict) and "error" in result:
            return {"status": "error", "code": 404, "message": result["error"], "data": []}
        return {"status": "success", "code": 0, "message": "", "data": result}
    except Exception as e:
        return {"status":"error","code":500,"message":str(e),"data":[]}
