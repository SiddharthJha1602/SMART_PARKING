"""
models/parking_session.py
A parking session represents one vehicle's stay from entry to exit.
"""

from datetime import datetime
from extensions import db


class ParkingSession(db.Model):
    __tablename__ = "parking_sessions"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("parking_slots.id"), nullable=False)

    entry_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)

    duration_minutes = db.Column(db.Integer, nullable=True)
    fee_charged = db.Column(db.Float, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="Active")  # Active, Completed

    def __repr__(self):
        return f"<ParkingSession vehicle={self.vehicle_id} slot={self.slot_id} status={self.status}>"
