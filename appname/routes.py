import time
from unittest import result
from flask import request, jsonify
from appname import app, socketio

# IMPORT FUNCTION
from appname.config import get_db_connection
from appname.functions.user_details import *
from appname.functions.chat_room import *
from appname.functions.user_register import *
from appname.functions.add_friend import *
from appname.functions.messages import *
from appname.functions.voice_notes import *
from appname.functions.storage import *
from appname.utils.storage_utils import *
from appname.utils.whisper_utils import *
from appname.utils.crypto_utils import encrypt_text, encryption_status

from appname.functions.user_login import *
from appname.functions.user_friends import *
from appname.functions.friend_request import *
from appname.functions.user_chat_list import *
from appname.functions.translate_video_to_text import *
from appname.functions.video_notes import *


@app.route("/chattingapp/crypto/status", methods=["GET"])
def crypto_status_route():
    # Returns key presence/validity only; never returns the key itself.
    try:
        return jsonify({"status": "success", "data": encryption_status()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# GET USER DETAIL
@app.route("/chattingapp/getuserdetails", methods=["GET"])
def get_users_route():
    try:
        # Get query parameters with default values
        limit = int(request.args.get("limit", 10))
        page = int(request.args.get("page", 1))

        # Call the data handler
        result = funcGetUserDetail(limit, page)

        # Return the result with appropriate status code
        status_code = 200 if result["status"] == "success" else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# GET USER DETAIL BY ID
@app.route("/chattingapp/getuserdetailsbyid", methods=["GET"])
def get_user_by_id_route():
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return (
                jsonify({"status": "error", "message": "Missing user_id parameter"}),
                400,
            )

        result = funcGetUserDetailByID(user_id)

        status_code = 200 if result["status"] == "success" else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# INSERT USER DETAIL
@app.route("/chattingapp/insertuserdetails", methods=["POST"])
def insert_user_route():
    try:
        data = request.get_json()
        result = funcInsertUserDetail(data)

        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# UPDATE USER DETAIL
@app.route("/chattingapp/updateuserdetails", methods=["PUT"])
def update_user_route():
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return (
                jsonify({"status": "error", "message": "Missing user_id parameter"}),
                400,
            )

        data = request.get_json()
        result = funcUpdateUserDetail(user_id, data)

        status_code = 200 if result["status"] == "success" else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# EDIT PROFILE (username, user_email, dob)
@app.route("/chattingapp/editprofile", methods=["POST"])
def edit_profile_route():
    try:
        data = request.get_json()
        user_id = data.get("user_id") if data else None
        if not user_id:
            return (
                jsonify({"status": "error", "code": 400, "message": "Missing required parameter: user_id", "data": []}),
                400,
            )

        # Only these fields are editable via this endpoint
        username = data.get("username") if data else None
        user_email = data.get("user_email") if data else None
        dob = data.get("dob") if data else None

        if not any([username, user_email, dob]):
            return (
                jsonify({"status": "error", "code": 400, "message": "Nothing to update: provide username, user_email or dob", "data": []}),
                400,
            )

        payload = {"username": username, "user_email": user_email, "dob": dob}

        result = funcEditProfile(user_id, payload)
        status_code = 200 if result.get("status") == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# SEND VERIFICATION EMAIL (only user_email required)
@app.route("/chattingapp/sendemail", methods=["POST"])
def send_email_route():
    try:
        data = request.get_json()
        user_email = data.get("user_email") if data else None

        if not user_email:
            return (
                jsonify({"status": "error", "code": 400, "message": "Missing required parameter: user_email", "data": []}),
                400,
            )

        # Call handler with email only
        res = funcSendVerificationEmail(user_email=user_email)
        status_code = 200 if res.get("status") == "success" else 400
        return jsonify(res), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# VERIFY CODE AND CHANGE PASSWORD (user_id optional; user_email allowed)
@app.route("/chattingapp/verificatepassword", methods=["POST"])
def verificate_password_route():
    try:
        data = request.get_json()
        user_id = data.get("user_id") if data else None
        user_email = data.get("user_email") if data else None
        verification_code = data.get("verification_code") if data else None
        new_password = data.get("new_password") if data else None

        if not verification_code or not new_password or (not user_id and not user_email):
            return (
                jsonify({"status": "error", "code": 400, "message": "Missing required parameters: verification_code, new_password, and either user_id or user_email must be provided", "data": []}),
                400,
            )

        res = funcVerifyAndChangePassword(user_id, verification_code, new_password, user_email=user_email)
        status_code = 200 if res.get("status") == "success" else 400
        return jsonify(res), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# DELETE USER DETAIL
@app.route("/chattingapp/deleteuserdetails", methods=["DELETE"])
def delete_user_route():
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return (
                jsonify({"status": "error", "message": "Missing user_id parameter"}),
                400,
            )

        result = funcDeleteUserDetail(user_id)

        status_code = 200 if result["status"] == "success" else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# LOGIN USER
@app.route("/chattingapp/loginuser", methods=["POST"])
def login_user_route():
    try:
        data = request.get_json()
        result = funcLoginUser(data)

        status_code = 200 if result["status"] == "success" else 401
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# REGISTER USER
@app.route("/chattingapp/registeruser", methods=["POST"])
def register_user_route():
    try:
        data = request.get_json()
        print("📩 Received data:", data)
        email = data.get("user_email", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        profile_picture = data.get("profile_picture", "")
        dob = data.get("dob", "")

        # Validation
        if not email or not username or not password or not dob:
            print("❌ Missing required field")
            return jsonify({"error": "Email, username, password, dan dob wajib diisi"}), 400

        if not validate_email(email):
            print("❌ Invalid email format")
            return jsonify({"error": "Format email tidak valid"}), 400

        # Basic DOB format check YYYY-MM-DD
        import datetime
        try:
            datetime.datetime.strptime(dob, "%Y-%m-%d")
        except Exception:
            print("❌ Invalid dob format")
            return jsonify({"error": "Format dob tidak valid. Gunakan YYYY-MM-DD"}), 400

        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            print("❌ Password invalid:", password_message)
            return jsonify({"error": password_message}), 400

        if len(username) < 3:
            print("❌ Username too short")
            return jsonify({"error": "Username minimal 3 karakter"}), 400

        # Check existing user
        print("✅ Validation passed, checking existing user...")
        if check_user_exists(email, username):
            print("❌ User already exists")
            return jsonify({"error": "Email atau username sudah terdaftar"}), 400

        # Pass data through to registration handler (it now expects dob)
        result = funcRegisterUser(data)

        status_code = 201 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================  FRIENDLISTS  ==================#
# GET USER FRIENDS by user_id
@app.route("/chattingapp/getuserfriends", methods=["GET"])
def get_user_friends_route():
    try:
        # Get query parameters
        user_id = request.args.get("user_id")
        if not user_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: user_id",
                        "data": [],
                    }
                ),
                400,
            )

        limit = int(request.args.get("limit", 10))
        page = int(request.args.get("page", 1))

        # Call the handler
        result = funcGetUserFriends(user_id, limit, page)

        # Return response
        status_code = 200 if result["status"] == "success" else 500
        print("📤 Sending response:", result)

        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# GET USER FRIENDS by username
@app.route("/chattingapp/getuserfriendsbyusername", methods=["GET"])
def get_user_friends_by_username_route():
    try:
        # Get query parameters
        username = request.args.get("username")
        if not username:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: username",
                        "data": [],
                    }
                ),
                400,
            )

        limit = int(request.args.get("limit", 10))
        page = int(request.args.get("page", 1))

        # Call the handler
        result = funcGetUserFriendsByUsername(username, limit, page)

        # Return response
        status_code = 200 if result["status"] == "success" else 500
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# ==================  FRIEND REQUESTS  ==================#
# GET FRIEND REQUESTS (by receiver)
@app.route("/chattingapp/getfriendrequests", methods=["GET"])
def get_friend_requests_route():
    try:
        receiver = request.args.get("receiver")
        if not receiver:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: receiver",
                        "data": [],
                    }
                ),
                400,
            )

        limit = int(request.args.get("limit", 10))
        page = int(request.args.get("page", 1))

        result = funcGetFriendRequests(receiver, limit, page)

        status_code = 200 if result["status"] == "success" else 500
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# REJECT FRIEND REQUEST
@app.route("/chattingapp/rejectfriendrequest", methods=["POST"])
def reject_friend_request_route():
    try:
        data = request.get_json()
        request_id = data.get("request_id") if data else None

        if not request_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: request_id",
                        "data": [],
                    }
                ),
                400,
            )

        result = funcRejectFriendRequest(request_id)

        status_code = 200 if result["status"] == "success" else 404
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# ==================  ADD FRIEND  ==================#
# SEARCH FRIEND BY USERNAME
@app.route("/chattingapp/searchfriendbyusername", methods=["GET"])
def search_friend_by_username_route():
    try:
        user_id = request.args.get("user_id")
        keyword = request.args.get("keyword")
        if not keyword:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: keyword",
                        "data": [],
                    }
                ),
                400,
            )

        limit = int(request.args.get("limit", 10))
        page = int(request.args.get("page", 1))

        # ✅ Pass user_id to your function
        result = funcSearchFriendByUsername(user_id, keyword, limit, page)

        status_code = 200 if result.get("status") == "success" else 500
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# SEND FRIEND REQUEST
@app.route("/chattingapp/sendfriendrequest", methods=["POST"])
def send_friend_request_route():
    try:
        data = request.get_json()
        sender_id = data.get("sender_id") if data else None
        receiver_id = data.get("receiver_id") if data else None

        if not sender_id or not receiver_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameters: sender_id and receiver_id",
                        "data": [],
                    }
                ),
                400,
            )

        result = funcSendFriendRequest(sender_id, receiver_id)

        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# ACCEPT FRIEND REQUEST
@app.route("/chattingapp/acceptfriendrequest", methods=["POST"])
def accept_friend_request_route():
    try:
        data = request.get_json()
        request_id = data.get("request_id") if data else None
        sender_id = data.get("sender_id") if data else None
        receiver_id = data.get("receiver_id") if data else None

        if not request_id or not sender_id or not receiver_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameters: request_id, sender_id, receiver_id",
                        "data": [],
                    }
                ),
                400,
            )

        result = funcAcceptFriendRequest(request_id, sender_id, receiver_id)

        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# ==================  CHAT FRIEND  ==================#


# LIST CHAT ROOMS FOR USER
@app.route("/chattingapp/getchatroomlist", methods=["GET"])
def get_chat_room_list_route():
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: user_id",
                        "data": [],
                    }
                ),
                400,
            )
        limit = int(request.args.get("limit", 10))
        page = int(request.args.get("page", 1))
        search = request.args.get("search")
        result = funcGetChatRoomList(user_id, limit, page, search)
        status_code = 200 if result.get("status") == "success" else 500
        return jsonify(result), status_code
    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# CREATE OR GET CHAT ROOM
@app.route("/chattingapp/createorgetchatroom", methods=["POST"])
def create_or_get_chat_room_route():
    try:
        data = request.get_json()
        user_id_first = data.get("user_id_first")
        user_id_second = data.get("user_id_second")

        if not user_id_first or not user_id_second:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameters: user_id_first, user_id_second",
                        "data": [],
                    }
                ),
                400,
            )

        result = funcCreateOrGetChatRoom(user_id_first, user_id_second)
        status_code = 200 if result["status"] == "success" else 500

        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# GET MESSAGES FOR ROOM
@app.route("/chattingapp/getchatroomlist", methods=["GET"])
def get_chatroom_list_route():
    try:
        user_id = request.args.get("user_id")
        limit = request.args.get("limit", type=int)
        page = request.args.get("page", type=int)
        search = request.args.get("search", default="")

        if not user_id or not limit or not page:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing user_id, limit, or page",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcGetChatRoomList(user_id, limit, page, search)
        status_code = 200 if res["status"] == "success" else 404
        return jsonify(res), status_code
    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/getmessages", methods=["GET"])
def get_messages_route():
    try:
        room_id = request.args.get("room_id")
        viewer = request.args.get("viewer")  # viewer's user_id
        if not room_id or not viewer:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing room_id or viewer",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcGetMessagesForRoom(room_id, viewer)
        status_code = 200 if res["status"] == "success" else 404
        return jsonify(res), status_code
    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


# GET SINGLE MESSAGE BY ID (for realtime updates)
@app.route("/chattingapp/getmessage/<message_id>", methods=["GET"])
def get_single_message_route(message_id):
    try:
        viewer = request.args.get("viewer")
        if not viewer:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing viewer parameter",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcGetSingleMessage(message_id, viewer)
        status_code = 200 if res["status"] == "success" else res.get("code", 404)
        return jsonify(res), status_code
    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/sendmessage", methods=["POST"])
def send_message_route():
    try:
        data = request.get_json()
        room_id = data.get("room_id")
        sender = data.get("sender_id")
        message_obj = data.get("message")

        if not room_id or not sender or message_obj is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing room_id, sender_id or message",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcSendMessage(room_id, sender, message_obj)
        status_code = 200 if res["status"] == "success" else 404
        return jsonify(res), status_code
    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/deletemessage", methods=["DELETE"])
def delete_message_route():
    try:
        message_id = request.args.get("message_id")
        if not message_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing message_id",
                        "data": [],
                    }
                ),
                400,
            )
        res = funcDeleteMessage(message_id)
        code = 200 if res["status"] == "success" else 404
        return jsonify(res), code
    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/voicenote/upload", methods=["POST"])
def upload_voice_note_route():
    try:
        file = request.files.get("voice")
        sender_id = request.form.get("sender_id")
        room_id = request.form.get("room_id")
        duration = request.form.get("duration_sec")

        if not file or not sender_id or not room_id:
            return jsonify({"status": "error", "message": "Missing fields"}), 400

        file_name = f"voice_{sender_id}_{room_id}_{int(time.time())}.m4a"
        file_bytes = file.read()

        media_url = upload_voice_to_supabase(file_name, file_bytes)

        file_size = len(file_bytes)
        result = insertVoiceNote(sender_id, room_id, media_url, file_size, duration)
        print(result)
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/chattingapp/voicenote/transcribe", methods=["POST"])
def transcribe_voice_note():
    try:
        message_id = request.json.get("message_id")
        media_url = request.json.get("media_url")

        if not message_id or not media_url:
            return {"error": "Missing fields"}, 400

        audio_bytes = download_from_supabase(media_url)
        transcript = call_whisper(audio_bytes)
        transcript_for_db = ""
        if (transcript or "").strip():
            transcript_for_db = encrypt_text(transcript)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT message_id FROM media_messages WHERE media_url = %s LIMIT 1",
            (media_url,),
        )
        row = cur.fetchone()
        if row and row[0] and str(row[0]) != str(message_id):
            message_id = str(row[0])

        # Do not overwrite existing transcript with empty result
        # If transcript is empty string, keep previous value
        cur.execute(
            """
            UPDATE voice_notes
               SET transcript_text = COALESCE(NULLIF(%s, ''), transcript_text)
             WHERE message_id = %s
            """,
            (transcript_for_db, message_id),
        )

        # ✅ CRITICAL: Update messages.updated_at to trigger Realtime UPDATE event
        cur.execute(
            "UPDATE messages SET updated_at = NOW() WHERE message_id = %s",
            (message_id,),
        )

        conn.commit()
        cur.close()
        conn.close()

        # Inform caller when nothing new was written
        if not (transcript or "").strip():
            return {
                "success": False,
                "message": "Transcription empty; existing transcript preserved",
                "transcript": "",
            }, 200

        return {"success": True, "transcript": transcript}

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/chattingapp/translateasl", methods=["POST"])
def translate_asl_route():
    try:
        data = request.get_json()
        video_url = data.get("video_url")
        room_id = data.get("room_id")
        frame_rate = data.get("frame_rate")
        resolution = data.get("resolution")
        message_id = data.get("message_id")
        generate_srt = data.get("generate_srt", False)

        if not video_url or not room_id or not frame_rate or not resolution:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required keys",
                        "data": [],
                    }
                ),
                400,
            )

        # message_id is required so we can link translation to the video note/message
        res = funcTranslateVideoToText(
            room_id, video_url, frame_rate, resolution, message_id
        )

        # After saving translation, fetch saved translate_video record (includes duration and message_id)
        if res["status"] == "success":
            if message_id:
                saved = funcGetTranslateVideo(room_id, message_id)
            else:
                saved = funcGetTranslateVideoByRoomAndUrl(room_id, video_url)

            if saved.get("status") == "success":
                translate_data = saved.get("data", {})

                # Format response to match original structure: timestamps array in "data" field
                # but include additional metadata (message_id, duration, etc.)
                formatted_response = {
                    "status": "success",
                    "code": 0,
                    "message": "ASL translation completed",
                    "data": translate_data.get("timestamps", []),
                    "message_id": translate_data.get("message_id") or "",
                    "duration": translate_data.get("duration"),
                    "translated_script": translate_data.get("translated_script"),
                    "created_at": translate_data.get("created_at"),
                }

                # optionally generate SRT from saved timestamps
                if generate_srt and formatted_response.get("data"):
                    from appname.datas.model_ai import generate_srt_from_predictions

                    srt_path = generate_srt_from_predictions(
                        formatted_response["data"], f"subtitles_room_{room_id}.srt"
                    )
                    formatted_response["srt_file"] = srt_path

                return jsonify(formatted_response), 200
            else:
                return jsonify(saved), 404

        status_code = 500
        return jsonify(res), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/uploadvideonote", methods=["POST"])
def upload_video_note_route():
    try:
        file = request.files.get("video")
        resolution = request.form.get("resolution")
        frame_rate = request.form.get("frame_rate")

        if not file or not resolution or not frame_rate:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing fields: video, resolution, frame_rate are required",
                        "data": [],
                    }
                ),
                400,
            )

        file_bytes = file.read()
        file_size = len(file_bytes)

        file_name = f"video_temp_{int(time.time())}.mp4"
        media_url = upload_video_to_supabase(file_name, file_bytes)

        result = funcUploadVideoNote(media_url, file_size, resolution, frame_rate)
        return jsonify(result), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/sendvideonote", methods=["POST"])
def send_video_note_route():
    try:
        data = request.json
        sender_id = data.get("sender_id")
        room_id = data.get("room_id")
        media_url = data.get("media_url")
        file_size = data.get("file_size")
        resolution = data.get("resolution")
        frame_rate = data.get("frame_rate")
        duration_sec = data.get("duration_sec")

        if not sender_id or not room_id or not media_url:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing fields: sender_id, room_id, media_url required",
                        "data": [],
                    }
                ),
                400,
            )

        result = funcSendVideoNote(
            sender_id,
            room_id,
            media_url,
            file_size,
            resolution,
            frame_rate,
            duration_sec,
        )
        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/getvideonotes", methods=["GET"])
def get_video_notes_route():
    try:
        room_id = request.args.get("room_id")
        limit = int(request.args.get("limit", 20))
        page = int(request.args.get("page", 1))

        if not room_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: room_id",
                        "data": [],
                    }
                ),
                400,
            )

        result = funcGetVideoNotes(room_id, limit, page)
        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "code": 500,
                    "message": str(e),
                    "data": [],
                }
            ),
            500,
        )


@app.route("/chattingapp/gettranslatevideo", methods=["GET"])
def get_translate_video_route():
    try:
        room_id = request.args.get("room_id")
        message_id = request.args.get("message_id")

        if not room_id or not message_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameters: room_id and message_id",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcGetTranslateVideo(room_id, message_id)
        status_code = 200 if res.get("status") == "success" else 404
        return jsonify(res), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/updatemessageidtranslatevideo", methods=["POST"])
def update_message_id_translate_video_route():
    try:
        data = request.get_json()
        room_id = data.get("room_id") if data else None
        video_url = data.get("video_url") if data else None
        message_id = data.get("message_id") if data else None

        if not room_id or not video_url or not message_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameters: room_id, video_url, message_id",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcUpdateMessageIdTranslateVideo(room_id, video_url, message_id)
        status_code = 200 if res.get("status") == "success" else 500
        return jsonify(res), status_code

    except Exception as e:
        return (
            jsonify({"status": "error", "code": 500, "message": str(e), "data": []}),
            500,
        )


@app.route("/chattingapp/updatetranslateynvideonotes", methods=["POST"])
def update_translate_yn_video_notes_route():
    try:
        data = request.get_json()
        message_id = data.get("message_id") if data else None

        if not message_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "Missing required parameter: message_id",
                        "data": [],
                    }
                ),
                400,
            )

        res = funcUpdateVideoNoteTranslateYN(message_id)
        status_code = 200 if res.get("status") == "success" else 500
        return jsonify(res), status_code

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "code": 500,
                    "message": str(e),
                    "data": [],
                }
            ),
            500,
        )
