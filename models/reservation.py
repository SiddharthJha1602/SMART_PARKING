"""
models/reservation.py
Slot reservations made in advance by users. A unique constraint on
(slot_id, status='Active') style prevention is enforced at the service
layer (see services/reservation_service.py) to keep this portable
across SQLite/MySQL.
"""

from datetime import datetime
from extensions import db


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("parking_slots.id"), nullable=False)

    reserved_for = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default="Active")  # Active, Cancelled, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Reservation user={self.user_id} slot={self.slot_id} status={self.status}>"
