"""
services/compliance_service.py
Verifies vehicle compliance (registration, insurance, PUC) and
generates alerts / compliance log entries.
"""

from datetime import date

from extensions import db
from models import Vehicle, ComplianceLog, Notification


def check_vehicle_compliance(vehicle: Vehicle, warning_days: int = 30) -> dict:
    """Runs a compliance check and writes log entries. Returns a status dict."""
    insurance_status = vehicle.insurance_status(warning_days)
    puc_status = vehicle.puc_status(warning_days)

    logs = [
        ComplianceLog(
            vehicle_id=vehicle.id,
            check_type="Insurance",
            status=insurance_status,
            details=f"Insurance expiry: {vehicle.insurance_expiry.isoformat()}",
        ),
        ComplianceLog(
            vehicle_id=vehicle.id,
            check_type="PUC",
            status=puc_status,
            details=f"PUC expiry: {vehicle.puc_expiry.isoformat()}",
        ),
    ]
    db.session.add_all(logs)

    # Generate notification if anything needs attention
    if insurance_status != "Valid":
        db.session.add(
            Notification(
                user_id=vehicle.user_id,
                title="Insurance Alert",
                message=f"{vehicle.vehicle_number}: insurance is {insurance_status.lower()}.",
                category="compliance",
            )
        )
    if puc_status != "Valid":
        db.session.add(
            Notification(
                user_id=vehicle.user_id,
                title="PUC Alert",
                message=f"{vehicle.vehicle_number}: PUC certificate is {puc_status.lower()}.",
                category="compliance",
            )
        )

    db.session.commit()

    return {
        "vehicle_number": vehicle.vehicle_number,
        "insurance_status": insurance_status,
        "puc_status": puc_status,
        "overall_status": vehicle.overall_compliance_status(warning_days),
        "is_compliant": vehicle.is_compliant(),
    }


def get_all_violations(warning_days: int = 30):
    """Returns vehicles that are Expired or Expiring Soon on any check."""
    vehicles = Vehicle.query.all()
    violations = []
    for v in vehicles:
        status = v.overall_compliance_status(warning_days)
        if status != "Valid":
            violations.append(
                {
                    "vehicle": v,
                    "insurance_status": v.insurance_status(warning_days),
                    "puc_status": v.puc_status(warning_days),
                    "overall_status": status,
                }
            )
    return violations
