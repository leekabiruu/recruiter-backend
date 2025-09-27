from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token
from models import db, User
from flask_bcrypt import check_password_hash

class LoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True, help="Email cannot be blank")
        parser.add_argument("password", type=str, required=True, help="Password cannot be blank")
        data = parser.parse_args()

        user = User.query.filter_by(email=data["email"]).first()
        if not user or not check_password_hash(user.password, data["password"]):
            return {"message": "Invalid email or password"}, 401

        access_token = create_access_token(identity=user.id)
        return {"access_token": access_token, "user": user.to_dict()}, 200
