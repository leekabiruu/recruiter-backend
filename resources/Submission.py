from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Submissions, Assessments, User


class SubmissionListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())

        submissions = (
            Submissions.query.join(Assessments)
            .filter(Assessments.creator_id == user_id)
            .all()
        )

        result = []
        for sub in submissions:
            data = sub.to_dict()
            data["user"] = User.query.get(sub.user_id).to_dict()
            result.append(data)

        return result, 200

    @jwt_required()
    def post(self):
        data = request.get_json()
        user_id = get_jwt_identity()
        assessment_id = data.get("assessment_id")
        answers = data.get("answers")

        if not assessment_id or not answers:
            return {"error": "assessment_id and answers are required"}, 400

        submission = Submissions(
            user_id=user_id,
            assessment_id=assessment_id,
            answers=answers,
            submitted_at=datetime.now(),
            grade=None,
        )

        db.session.add(submission)
        db.session.commit()

        return {"message": "Submission successful", "submission_id": submission.id}, 201
    @jwt_required()
    def delete(self):
        user_id = int(get_jwt_identity())

        # Grab all submissions linked to assessments created by this user
        submissions = (
            Submissions.query
            .join(Assessments)
            .filter(Assessments.creator_id == user_id)
            .all()
        )

        if not submissions:
            return {"message": "No submissions found"}, 404

        for sub in submissions:
            db.session.delete(sub)

        db.session.commit()
        return {"message": "All submissions deleted"}, 200
    

class SubmissionDetailResource(Resource):
    @jwt_required()
    def patch(self, submission_id):
        user_id = int(get_jwt_identity())
        data = request.get_json()
        new_grade = data.get("grade")

        if new_grade is None:
            return {"message": "Grade is required"}, 400

        submission = Submissions.query.get_or_404(submission_id)
        assessment = Assessments.query.get(submission.assessment_id)

        if assessment.creator_id != user_id:
            return {"message": "Unauthorized to update this grade"}, 403

        submission.grade = new_grade
        db.session.commit()

        return {"message": "Grade updated successfully", "grade": submission.grade}, 200