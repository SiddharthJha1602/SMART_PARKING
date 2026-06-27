"""
models/user.py
User accounts. Supports two roles: 'admin' and 'user'.
Passwords are stored as salted hashes (never plaintext).
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'admin' | 'user'
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    vehicles = db.relationship(
        "Vehicle", backref="owner", lazy=True, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    reservations = db.relationship(
        "Reservation", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    # --- Password helpers ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # --- Role helpers ---
    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    # Flask-Login expects get_id() to return a string; UserMixin already
    # provides this using self.id, so no override needed.

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
