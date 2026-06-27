"""
models/parking_slot.py
Parking slots, grouped into zones (e.g. Zone A: A1-A5, Zone B: B1-B5).
"""

from extensions import db

SLOT_STATUS_AVAILABLE = "Available"
SLOT_STATUS_OCCUPIED = "Occupied"
SLOT_STATUS_RESERVED = "Reserved"


class ParkingSlot(db.Model):
    __tablename__ = "parking_slots"

    id = db.Column(db.Integer, primary_key=True)
    slot_code = db.Column(db.String(10), unique=True, nullable=False, index=True)  # e.g. "A1"
    zone = db.Column(db.String(10), nullable=False)  # e.g. "A"
    status = db.Column(db.String(20), nullable=False, default=SLOT_STATUS_AVAILABLE)
    slot_type = db.Column(db.String(20), nullable=False, default="Car")  # Car, Bike, Truck

    # Relationships
    parking_sessions = db.relationship("ParkingSession", backref="slot", lazy=True)
    reservations = db.relationship("Reservation", backref="slot", lazy=True)

    def __repr__(self):
        return f"<ParkingSlot {self.slot_code} ({self.status})>"
