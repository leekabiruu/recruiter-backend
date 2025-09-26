from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required
from models import Questions, db

parser = reqparse.RequestParser()
parser.add_argument("prompt", type=str, required=True, help="Prompt is required")
parser.add_argument(
    "type", type=str, choices=("multiple_choice", "codekata", "codewars"), required=True
)
parser.add_argument("options", type=list, location="json")
parser.add_argument("answer_key", type=str)
parser.add_argument(
    "meta", type=dict, location="json"
)  # ✅ Optional metadata for Codewars


class QuestionsListResource(Resource):
    @jwt_required()
    def get(self, assessment_id):
        questions = Questions.query.filter_by(assessment_id=assessment_id).all()
        return [q.to_dict() for q in questions], 200

    @jwt_required()
    def post(self, assessment_id):
        args = parser.parse_args()

        if args["type"] == "multiple_choice":
            if not args["options"] or not isinstance(args["options"], list):
                return {"message": "Options must be a list for multiple_choice"}, 400
            if not args["answer_key"]:
                return {"message": "Answer key is required for multiple_choice"}, 400

        if args["type"] == "codewars":
            if not args["answer_key"]:
                return {"message": "Codewars slug is required as answer_key"}, 400

        question = Questions(
            assessment_id=assessment_id,
            prompt=args["prompt"].strip(),
            type=args["type"],
            options=args.get("options"),
            answer_key=args.get("answer_key"),
            meta=args.get("meta"),
        )

        db.session.add(question)
        db.session.commit()
        return question.to_dict(), 201


class QuestionDetailResource(Resource):
    @jwt_required()
    def get(self, question_id):
        question = Questions.query.get_or_404(question_id)
        return question.to_dict(), 200

    @jwt_required()
    def patch(self, question_id):
        args = parser.parse_args()
        question = Questions.query.get_or_404(question_id)

        if args["prompt"]:
            question.prompt = args["prompt"].strip()
        if args["type"]:
            question.type = args["type"]
        if args["options"] is not None:
            if not isinstance(args["options"], list):
                return {"message": "Options must be a list"}, 400
            question.options = args["options"]
        if args["answer_key"]:
            question.answer_key = args["answer_key"]
        if args["meta"]:
            question.meta = args["meta"]

        db.session.commit()
        return question.to_dict(), 200

    @jwt_required()
    def delete(self, question_id):
        question = Questions.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        return {"message": "Question deleted"}, 204