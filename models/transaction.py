"""
models/transaction.py
Simulated FASTag wallet transactions: top-ups and parking-fee deductions.
"""

from datetime import datetime
from extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    parking_session_id = db.Column(
        db.Integer, db.ForeignKey("parking_sessions.id"), nullable=True
    )

    transaction_type = db.Column(db.String(20), nullable=False)  # 'Top-up' | 'Deduction'
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parking_session = db.relationship("ParkingSession", backref="transactions", lazy=True)

    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.amount}>"
