from models import Notification
from datetime import datetime
from models import db


def create_notification(user_id, text, assessment_id=None):
    notification = Notification(
        user_id=user_id,
        text=text,
        assessment_id=assessment_id,
        timestamp=datetime.now(),
        read=False,
    )
    db.session.add(notification)
    db.session.commit()