"""
models/vehicle.py
Vehicle records owned by a User. Stores simulated compliance data
(insurance, PUC) and a simulated FASTag wallet balance.
"""

from datetime import datetime, date
from extensions import db


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    owner_name = db.Column(db.String(120), nullable=False)
    vehicle_type = db.Column(db.String(30), nullable=False, default="Car")  # Car, Bike, Truck, Bus
    registration_date = db.Column(db.Date, nullable=False, default=date.today)
    insurance_expiry = db.Column(db.Date, nullable=False)
    puc_expiry = db.Column(db.Date, nullable=False)

    # Simulated FASTag wallet
    wallet_balance = db.Column(db.Float, nullable=False, default=500.0)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    parking_sessions = db.relationship(
        "ParkingSession", backref="vehicle", lazy=True, cascade="all, delete-orphan"
    )
    transactions = db.relationship(
        "Transaction", backref="vehicle", lazy=True, cascade="all, delete-orphan"
    )
    reservations = db.relationship(
        "Reservation", backref="vehicle", lazy=True, cascade="all, delete-orphan"
    )
    compliance_logs = db.relationship(
        "ComplianceLog", backref="vehicle", lazy=True, cascade="all, delete-orphan"
    )

    # --- Compliance helpers ---
    def _expiry_status(self, expiry_date: date, warning_days: int = 30) -> str:
        today = date.today()
        if expiry_date < today:
            return "Expired"
        if (expiry_date - today).days <= warning_days:
            return "Expiring Soon"
        return "Valid"

    def insurance_status(self, warning_days: int = 30) -> str:
        return self._expiry_status(self.insurance_expiry, warning_days)

    def puc_status(self, warning_days: int = 30) -> str:
        return self._expiry_status(self.puc_expiry, warning_days)

    def overall_compliance_status(self, warning_days: int = 30) -> str:
        statuses = {self.insurance_status(warning_days), self.puc_status(warning_days)}
        if "Expired" in statuses:
            return "Expired"
        if "Expiring Soon" in statuses:
            return "Expiring Soon"
        return "Valid"

    def is_compliant(self) -> bool:
        """A vehicle must have valid (non-expired) insurance and PUC to park."""
        today = date.today()
        return self.insurance_expiry >= today and self.puc_expiry >= today

    def __repr__(self):
        return f"<Vehicle {self.vehicle_number}>"
