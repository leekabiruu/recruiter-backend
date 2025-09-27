from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from flask import Flask
from flask_restful import Api
from flask_mail import Mail

from models import db


from resources.user import (
    LoginResource,
    SignupResource,
    UserListResource,
    RecruiterStatsResource,
    UserDetailResource,
)
from resources.assessments import AssessmentResource
from resources.Questions import QuestionDetailResource, QuestionsListResource
from resources.results import (
    IntervieweeResultsResource,
    ResultReleaseResource,
    ResultCreateOrUpdateResource,
    IntervieweeRankingResource,
)
from resources.feedback import FeedbackResource
from resources.profile import ProfileResource
from resources.Submission import SubmissionListResource, SubmissionDetailResource
from resources.notification import NotificationListResource, NotificationReadResource
from resources.invites import InviteListResource, InviteResource, InviteAcceptanceResource


load_dotenv() 
app = Flask(__name__)
api = Api(app)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
jwt = JWTManager(app)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)

migrate = Migrate(app, db) 
db.init_app(app) 


@app.route("/")
def index():
    return {"message": "Welcome to Smart Recruiter API"}, 200

 
api.add_resource(SignupResource, "/signup")
api.add_resource(LoginResource, "/login")
api.add_resource(UserListResource, "/users")
api.add_resource(UserDetailResource, "/users/<int:user_id>")
api.add_resource(RecruiterStatsResource, "/stats/recruiter")

api.add_resource(AssessmentResource, "/assessments", "/assessments/<int:assessment_id>") 
api.add_resource(QuestionsListResource, "/assessments/<int:assessment_id>/questions")
api.add_resource(QuestionDetailResource, "/questions/<int:id>")

api.add_resource(SubmissionListResource, "/submissions")
api.add_resource(SubmissionDetailResource, "/submissions/<int:submission_id>")

api.add_resource(FeedbackResource, "/feedback", "/feedback/<int:id>")

api.add_resource(ProfileResource, "/profile", "/profile/<int:id>")

api.add_resource(InviteListResource, "/invites")
api.add_resource(InviteResource, "/invites/<int:invite_id>")
api.add_resource(InviteAcceptanceResource, "/invites/accept/<string:token>")

api.add_resource(IntervieweeResultsResource, "/interviewee/results")
api.add_resource(ResultReleaseResource, "/results/<int:result_id>/release")
api.add_resource(ResultCreateOrUpdateResource, "/results")
api.add_resource(IntervieweeRankingResource, "/interviewee-rankings")

api.add_resource(NotificationListResource, "/notifications")
api.add_resource(NotificationReadResource, "/notifications/<int:notification_id>/read")


if __name__ == "__main__":
    app.run(debug=True) 