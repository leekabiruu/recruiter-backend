from datetime import datetime, timedelta
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from flask import current_app
from models import db, User, Invites, Assessments
import os
import secrets
from utils.notification import create_notification


class InviteResource(Resource):
    @jwt_required()
    def get(self, invite_id):
        current_user_id = int(get_jwt_identity())
        invite = Invites.query.get_or_404(invite_id)

        if (
            invite.recruiter_id != current_user_id
            and invite.interviewee_id != current_user_id
        ):
            return {"message": "Unauthorized"}, 403

        return invite.to_dict(), 200


class InviteListResource(Resource):
    invite_parser = reqparse.RequestParser()
    invite_parser.add_argument("assessment_id", type=int, required=True)
    invite_parser.add_argument("interviewee_email", type=str, required=True)
    invite_parser.add_argument("expires_in_days", type=int, default=7)

    @jwt_required()
    def get(self):
        current_user_id = int(get_jwt_identity())
        recruiter = User.query.get(current_user_id)

        if not recruiter or recruiter.role != "recruiter":
            return {"message": "Unauthorized"}, 403

        invites = (
            Invites.query.filter_by(recruiter_id=current_user_id)
            .order_by(Invites.sent_at.desc())
            .all()
        )
        return [invite.to_dict() for invite in invites], 200

    @jwt_required()
    def post(self):
        current_user_id = int(get_jwt_identity())
        data = self.invite_parser.parse_args()

        recruiter = User.query.get(current_user_id)
        if not recruiter or recruiter.role != "recruiter":
            return {"message": "Unauthorized"}, 403

        assessment = Assessments.query.filter_by(
            id=data["assessment_id"], creator_id=current_user_id
        ).first()

        if not assessment:
            return {"message": "Assessment not found or permission denied"}, 404

        interviewee = User.query.filter_by(
            email=data["interviewee_email"], role="interviewee"
        ).first()

        if not interviewee:
            return {
                "message": "Interviewee not found. Please ensure they are registered"
            }, 404

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=data["expires_in_days"])

        invite = Invites(
            recruiter_id=current_user_id,
            interviewee_id=interviewee.id,
            assessment_id=assessment.id,
            status="pending",
            token=token,
            expires_at=expires_at,
            sent_at=datetime.utcnow(),
        )

        db.session.add(invite)
        db.session.commit()

        # 🔔 Send in-app notifications
        create_notification(
            current_user_id,
            f"Invite sent to {interviewee.email} for '{assessment.title}'",
        )
        create_notification(
            interviewee.id, f"You’ve been invited to complete '{assessment.title}'"
        )

        # ✉️ Send email if enabled
        if os.getenv("MAIL_ENABLED", "true").lower() == "true":
            try:
                frontend_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
                invite_url = f"{frontend_url}/invites/accept?token={token}"

                subject_i = "Assessment Invitation"
                body_i = f"""Hello {interviewee.name or interviewee.email},

You have been invited to take: {assessment.title}.
Accept here: {invite_url}

This invite expires on {expires_at.strftime("%Y-%m-%d %H:%M UTC")}.
Best,
{recruiter.name or "Your recruiter"}
"""
                msg_i = Message(
                    subject=subject_i, recipients=[interviewee.email], body=body_i
                )
                current_app.extensions["mail"].send(msg_i)

                subject_r = "Invitation Sent"
                body_r = f"""Hello {recruiter.name or "Recruiter"},

You successfully invited {interviewee.name or interviewee.email}
to assessment: {assessment.title}.
Invite URL: {invite_url}
Expires on: {expires_at.strftime("%Y-%m-%d %H:%M UTC")}
"""
                msg_r = Message(
                    subject=subject_r, recipients=[recruiter.email], body=body_r
                )
                current_app.extensions["mail"].send(msg_r)

            except Exception as e:
                return {
                    "message": f"Invite created but email failed to send: {str(e)}",
                    "invite": {
                        "id": invite.id,
                        "token": token,
                        "expires_at": expires_at.isoformat(),
                    },
                }, 202

        return {
            "message": "Invite created successfully",
            "invite": {
                "id": invite.id,
                "token": token,
                "expires_at": expires_at.isoformat(),
            },
        }, 201


class InviteAcceptanceResource(Resource):
    @jwt_required()
    def patch(self, token):
        current_user_id = int(get_jwt_identity())

        invite = Invites.query.filter_by(token=token).first()
        if not invite:
            return {"message": "Invalid invitation token"}, 404

        if invite.interviewee_id != current_user_id:
            return {"message": "You are not authorized to accept this invite"}, 403

        if invite.status != "pending":
            return {"message": "This invitation has already been processed"}, 400

        if datetime.now() > invite.expires_at:
            return {"message": "This invitation has expired"}, 400

        invite.status = "accepted"
        invite.accepted_at = datetime.now()
        db.session.commit()

        # 🗓 Notify interviewee of assessment time window
        assessment = Assessments.query.get(invite.assessment_id)
        if assessment:
            start_str = assessment.start_time.strftime("%Y-%m-%d %H:%M")
            end_str = assessment.end_time.strftime("%H:%M")
            message = (
                f"You’ve accepted the invite to '{assessment.title}'.\n"
                f"Time: {start_str} to {end_str}"
            )
            create_notification(
                invite.interviewee_id, message, assessment_id=assessment.id
            )
        return {
            "message": "Invitation accepted successfully",
            "assessment_id": invite.assessment_id,
        }, 200