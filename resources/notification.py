# resources/notification.py

from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification


class NotificationListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        notifications = (
            Notification.query.filter_by(user_id=user_id)
            .order_by(Notification.timestamp.desc())
            .all()
        )
        return [n.to_dict() for n in notifications], 200




class NotificationReadResource(Resource):
    @jwt_required()
    def patch(self, notification_id):
        current_user_id = int(get_jwt_identity())
        notification = Notification.query.get_or_404(notification_id)

        if notification.user_id != current_user_id:
            return {"message": "Unauthorized"}, 403

        if notification.read:
            return {"message": "Already marked as read"}, 200

        notification.read = True
        db.session.commit()
        return {"message": "Notification marked as read"}, 200