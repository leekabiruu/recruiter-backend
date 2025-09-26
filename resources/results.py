from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Results, Submissions, Assessments, User


class IntervieweeResultsResource(Resource):
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())

        results = (
            Results.query.join(Submissions)
            .filter(Submissions.user_id == user_id, Results.is_released == True)
            .all()
        )

        return [r.to_dict() for r in results], 200


class ResultReleaseResource(Resource):
    @jwt_required()
    def patch(self, result_id):
        recruiter_id = int(get_jwt_identity())
        result = Results.query.get_or_404(result_id)

        # Confirm this recruiter owns the assessment
        assessment = Assessments.query.get(result.submission.assessment_id)
        if assessment.creator_id != recruiter_id:
            return {"message": "Unauthorized"}, 403

        result.is_released = True
        db.session.commit()

        return {"message": "Result released successfully"}, 200
    

class ResultCreateOrUpdateResource(Resource):
    @jwt_required()
    def post(self):
        recruiter_id = int(get_jwt_identity())
        data = request.get_json()

        submission_id = data.get("submission_id")
        score = data.get("score")
        time_taken = data.get("time_taken", None)
        rank = data.get("rank", None)
        pass_status = data.get("pass_status", False)
        is_released = data.get("is_released", False)
        feedback_summary = data.get("feedback_summary", "")

        if submission_id is None or score is None:
            return {"message": "submission_id and score are required"}, 400

        submission = Submissions.query.get_or_404(submission_id)
        assessment = Assessments.query.get(submission.assessment_id)

        if assessment.creator_id != recruiter_id:
            return {"message": "Unauthorized"}, 403

        # Check if result already exists for this submission
        existing = Results.query.filter_by(submission_id=submission_id).first()

        if existing:
            # Update existing result
            existing.score = score
            existing.time_taken = time_taken
            existing.rank = rank
            existing.pass_status = pass_status
            existing.is_released = is_released
            existing.feedback_summary = feedback_summary
            db.session.commit()
            return {"message": "Result updated", "result": existing.to_dict()}, 200
        else:
            # Create new result
            result = Results(
                submission_id=submission_id,
                score=score,
                time_taken=time_taken,
                rank=rank,
                pass_status=pass_status,
                is_released=is_released,
                feedback_summary=feedback_summary,
            )

            db.session.add(result)
            db.session.commit()
            return {"message": "Result created", "result": result.to_dict()}, 201

class IntervieweeRankingResource(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if user.role != "recruiter":
            return {"error": "Unauthorized"}, 403

        ranked = (
            db.session.query(Results, User.name)
            .join(Submissions, Results.submission_id == Submissions.id)
            .join(User, User.id == Submissions.user_id)
            .order_by(Results.score.desc())
            .all()
        )

        return [
            {
                "name": name,
                "score": result.score,
                "rank": result.rank,
                "pass_status": result.pass_status,
                "is_released": result.is_released,
                "time_taken": result.time_taken,
                "feedback_summary": result.feedback_summary,
            }
            for result, name in ranked
        ], 200