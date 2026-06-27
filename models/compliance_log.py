"""
models/compliance_log.py
Historical log of compliance checks performed on vehicles, so the
admin can audit when a vehicle was flagged and why.
"""

from datetime import datetime
from extensions import db


class ComplianceLog(db.Model):
    __tablename__ = "compliance_logs"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)

    check_type = db.Column(db.String(30), nullable=False)  # 'Insurance' | 'PUC' | 'Registration'
    status = db.Column(db.String(20), nullable=False)      # 'Valid' | 'Expiring Soon' | 'Expired'
    details = db.Column(db.String(255), nullable=True)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ComplianceLog vehicle={self.vehicle_id} {self.check_type}={self.status}>"
