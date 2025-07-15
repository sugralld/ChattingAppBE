from flask import request, jsonify
from appname import app 

# IMPORT FUNCTION
from appname.functions.user_details import *
from appname.functions.user_login import *

# GET USER DETAIL
@app.route('/chattingapp/getuserdetails', methods=['GET'])
def get_users_route():
    try:
        # Get query parameters with default values
        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))

        # Call the data handler
        result = funcGetUserDetail(limit, page)

        # Return the result with appropriate status code
        status_code = 200 if result['status'] == 'success' else 500
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# GET USER DETAIL BY ID
@app.route('/chattingapp/getuserdetailsbyid', methods=['GET'])
def get_user_by_id_route():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Missing user_id parameter'}), 400

        result = funcGetUserDetailByID(user_id)

        status_code = 200 if result['status'] == 'success' else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# INSERT USER DETAIL
@app.route('/chattingapp/insertuserdetails', methods=['POST'])
def insert_user_route():
    try:
        data = request.get_json()
        result = funcInsertUserDetail(data)

        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# UPDATE USER DETAIL
@app.route('/chattingapp/updateuserdetails', methods=['PUT'])
def update_user_route():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Missing user_id parameter'}), 400

        data = request.get_json()
        result = funcUpdateUserDetail(user_id, data)

        status_code = 200 if result['status'] == 'success' else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# DELETE USER DETAIL
@app.route('/chattingapp/deleteuserdetails', methods=['DELETE'])
def delete_user_route():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Missing user_id parameter'}), 400

        result = funcDeleteUserDetail(user_id)

        status_code = 200 if result['status'] == 'success' else 404
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# LOGIN USER
@app.route('/chattingapp/loginuser', methods=['POST'])
def login_user_route():
    try:
        data = request.get_json()
        result = funcLoginUser(data)

        status_code = 200 if result['status'] == 'success' else 401
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
