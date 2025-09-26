from flask_restful import Resource,reqparse 
from models import Feedback, User, db

class FeedbackResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("question_id", type=int, required=True, help="question_id is required")
    parser.add_argument("submission_id", type=int, required=False, help="submission_id is required")
    parser.add_argument("recruiter_name", type=str, required=True, help="recruiter_name is required")
    parser.add_argument("comment", type=str, required=True, help="comment is required")

    def get(self, id=None):  
      if id is None:
        feedbacks = Feedback.query.all()
        return [feedback.to_dict() for feedback in feedbacks], 200  
      else:
        feedback = Feedback.query.filter_by(id=id).first()
        if feedback:
            return feedback.to_dict(), 200
        return {"error": "Feedback not found"}, 404

    def post(self):
        data = FeedbackResource.parser.parse_args()

        recruiter = User.query.filter_by(name=data["recruiter_name"], role="recruiter").first()

        if not recruiter:
            return {"error": "Recruiter not found"}, 403

        if not recruiter:
            return {"error": "Recruiter not found"}, 404

        feedback = Feedback(
            question_id=data["question_id"],
            submission_id=data["submission_id"],
            recruiter_id=recruiter.id,
            comment=data["comment"]
        )

        db.session.add(feedback)
        db.session.commit()

        return (feedback.to_dict())