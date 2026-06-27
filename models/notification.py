"""
models/notification.py
In-app notification history for a user (reservation confirmations,
entry/exit alerts, wallet deductions, compliance expiry warnings).
"""

from datetime import datetime
from extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(30), nullable=False, default="info")
    # categories: 'reservation', 'entry', 'exit', 'wallet', 'compliance', 'info'

    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.title}>"
