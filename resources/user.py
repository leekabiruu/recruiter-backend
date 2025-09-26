from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User,Assessments
from flask_bcrypt import generate_password_hash, check_password_hash




class UserListResource(Resource):
    def get(self):
        users = User.query.all()
        return [user.to_dict() for user in users], 200


class SignupResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("name", required=True, help="Name is required")
    parser.add_argument("email", required=True, help="Email is required")
    parser.add_argument("password", required=True, help="Password is required")
    parser.add_argument(
        "role",
        required=True,
        choices=("recruiter", "interviewee"),
        help="Role must be either recruiter or interviewee",
    )

    def post(self):
        data = self.parser.parse_args()

        if User.query.filter_by(email=data["email"]).first():
            return {"message": "User already exists"}, 422

        data["password"] = generate_password_hash(data["password"]).decode("utf-8")
        user = User(**data)

        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        return {
            "message": "Signup successful",
            "user": user.to_dict(),
            "access_token": access_token,
        }, 201


class LoginResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "email", required=True, type=str, help="Email address is required"
    )
    parser.add_argument(
        "password", required=True, type=str, help="Password is required"
    )

    def post(self):
        data = self.parser.parse_args()
        user = User.query.filter_by(email=data["email"]).first()

        if not user or not check_password_hash(user.password, data["password"]):
            return {"message": "Invalid email or password"}, 401

        access_token = create_access_token(identity=str(user.id))
        return {
            "message": "Login successful",
            
            "access_token": access_token,

            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
            "role": user.role,

        }, 201

class RecruiterStatsResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        interviewees = User.query.filter_by(role="interviewee").count()
        assessments = Assessments.query.filter_by(creator_id=user_id).count()

        return {
            "interviewees": interviewees,
            "assessments": assessments,
        }, 200