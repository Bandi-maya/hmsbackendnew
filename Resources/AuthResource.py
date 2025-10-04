from flask import request
from flask_jwt_extended import create_access_token
from flask_restful import Resource

from Models.Users import User
from Serializers.UserSerializers import user_serializer


class AuthResource(Resource):
    def post(self):
        data = request.get_json(force=True)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'msg': 'Missing username or password'}, 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return {'msg': 'Bad username or password'}, 401
        user = user_serializer.dump(user)
        if user['password'] != password:
            return {'msg': 'Bad username or password'}, 401

        access_token = create_access_token(identity=username)
        return {'access_token': access_token, "user": user, "success": True}, 200
