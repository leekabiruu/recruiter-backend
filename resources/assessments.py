from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Assessments, User


class AssessmentResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("title", type=str)
    parser.add_argument("time_limit", type=int)
    parser.add_argument("published", type=bool)

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or user.role != "recruiter":
            return {
                "error": "Unauthorized: Only recruiters can create assessments"
            }, 403

        args = self.parser.parse_args()
        if not args.title or not args.time_limit:
            return {"error": "Missing required fields"}, 400

        new_assessment = Assessments(
            title=args.title,
            creator_id=current_user_id,
            time_limit=args.time_limit,
            published=args.published if args.published is not None else False,
        )
        db.session.add(new_assessment)
        db.session.commit()

        return {
            "message": "Assessment created",
            "assessment": {
                "id": new_assessment.id,
                "title": new_assessment.title,
                "creator_id": new_assessment.creator_id,
                "time_limit": new_assessment.time_limit,
                "published": new_assessment.published,
            },
        }, 201

     

    @jwt_required()
    def patch(self, assessment_id):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        assessment = Assessments.query.get(assessment_id)

        if not user or user.role != "recruiter":
            return {"error": "Unauthorized"}, 403
        if not assessment or assessment.creator_id != current_user_id:
            return {"error": "Assessment not found or permission denied"}, 404

        args = self.parser.parse_args()
        if args.title is not None:
            assessment.title = args.title
        if args.time_limit is not None:
            assessment.time_limit = args.time_limit
        if args.published is not None:
            assessment.published = args.published

        db.session.commit()
        return {"message": "Assessment updated"}, 200

    @jwt_required()
    def delete(self, assessment_id):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        assessment = Assessments.query.get(assessment_id)

        if not user or user.role != "recruiter":
            return {"error": "Unauthorized"}, 403
        if not assessment or assessment.creator_id != current_user_id:
            return {"error": "Assessment not found or permission denied"}, 404

        db.session.delete(assessment)
        db.session.commit()
        return {"message": f"Assessment {assessment_id} deleted"}, 200


    @jwt_required()
    def get(self, assessment_id=None):
        
        if assessment_id:
            assessment = db.session.query(Assessments).get(assessment_id)
            if not assessment:
                return {"error": "Assessment not found"}, 404

            return {
                "id": assessment.id,
                "title": assessment.title,
                "creator_id": assessment.creator_id,
                "time_limit": assessment.time_limit,
                "published": assessment.published
            }, 200

        else:
            assessments = db.session.query(Assessments).all()
            return [
                {
                    "id": a.id,
                    "title": a.title,
                    "time_limit": a.time_limit,
                    "published": a.published
                }
                for a in assessments
            ], 200