from flask import request, jsonify
from appname import app

# IMPORT FUNCTION
from appname.datas.user_details import *
from appname.datas.user_login import *
from appname.datas.user_friends import *
from appname.datas.friend_request import *
from appname.functions.user_register import *
from appname.functions.add_friend import *

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
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
        return jsonify({'status': 'error', 'message': str(e)}), 500


# INSERT USER DETAIL
@app.route("/chattingapp/insertuserdetails", methods=["POST"])
def insert_user_route():
    try:
        data = request.get_json()
        result = funcInsertUserDetail(data)

        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
        result = funcRegisterUser(data)

        status_code = 201 if result["status"] == "success" else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

#==================  FRIENDLISTS  ==================#
# GET USER FRIENDS by user_id
@app.route('/chattingapp/getuserfriends', methods=['GET'])
def get_user_friends_route():
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameter: user_id",
                "data": []
            }), 400

        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))

        # Call the handler
        result = funcGetUserFriends(user_id, limit, page)

        # Return response
        status_code = 200 if result['status'] == 'success' else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e),
            'data': []
        }), 500

# GET USER FRIENDS by username
@app.route('/chattingapp/getuserfriendsbyusername', methods=['GET'])
def get_user_friends_by_username_route():
    try:
        # Get query parameters
        username = request.args.get('username')
        if not username:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameter: username",
                "data": []
            }), 400

        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))

        # Call the handler
        result = funcGetUserFriendsByUsername(username, limit, page)

        # Return response
        status_code = 200 if result['status'] == 'success' else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': str(e),
            'data': []
        }), 500
    
#==================  FRIEND REQUESTS  ==================#
# GET FRIEND REQUESTS (by receiver)
@app.route('/chattingapp/getfriendrequests', methods=['GET'])
def get_friend_requests_route():
    try:
        receiver = request.args.get('receiver')
        if not receiver:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameter: receiver",
                "data": []
            }), 400

        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))

        result = funcGetFriendRequests(receiver, limit, page)

        status_code = 200 if result["status"] == "success" else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }), 500

# REJECT FRIEND REQUEST
@app.route('/chattingapp/rejectfriendrequest', methods=['POST'])
def reject_friend_request_route():
    try:
        data = request.get_json()
        request_id = data.get("request_id") if data else None

        if not request_id:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameter: request_id",
                "data": []
            }), 400

        result = funcRejectFriendRequest(request_id)

        status_code = 200 if result["status"] == "success" else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }), 500

#==================  ADD FRIEND  ==================#
# SEARCH FRIEND BY USERNAME
@app.route('/chattingapp/searchfriendbyusername', methods=['GET'])
def search_friend_by_username_route():
    try:
        keyword = request.args.get('keyword')
        if not keyword:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameter: keyword",
                "data": []
            }), 400

        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))

        result = funcSearchFriendByUsername(keyword, limit, page)

        status_code = 200 if result['status'] == 'success' else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }), 500

# SEND FRIEND REQUEST
@app.route('/chattingapp/sendfriendrequest', methods=['POST'])
def send_friend_request_route():
    try:
        data = request.get_json()
        sender_id = data.get("sender_id") if data else None
        receiver_id = data.get("receiver_id") if data else None

        if not sender_id or not receiver_id:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameters: sender_id and receiver_id",
                "data": []
            }), 400

        result = funcSendFriendRequest(sender_id, receiver_id)

        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }), 500

# ACCEPT FRIEND REQUEST
@app.route('/chattingapp/acceptfriendrequest', methods=['POST'])
def accept_friend_request_route():
    try:
        data = request.get_json()
        request_id = data.get("request_id") if data else None
        sender_id = data.get("sender_id") if data else None
        receiver_id = data.get("receiver_id") if data else None

        if not request_id or not sender_id or not receiver_id:
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Missing required parameters: request_id, sender_id, receiver_id",
                "data": []
            }), 400

        result = funcAcceptFriendRequest(request_id, sender_id, receiver_id)

        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "code": 500,
            "message": str(e),
            "data": []
        }), 500
