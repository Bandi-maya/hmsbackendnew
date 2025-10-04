from flask import request, g

from Models.ActivityLogs import ActivityLog
from app_utils import db


def log_activity(action, details=None):
    try:
        user_id = getattr(g, 'user', {}).get('id', None)
        if not user_id:
            return  # Skip if user is not identified

        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Optionally log to stderr if logging fails
        print(e)
