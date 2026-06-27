"""
services/analytics_service.py
Aggregations used by the dashboard, charts, and the analytics module:
revenue, occupancy, parking trends, peak hours, vehicle type
distribution, and slot usage frequency.
"""

from datetime import datetime, date, timedelta
from collections import Counter

from sqlalchemy import func

from extensions import db
from models import ParkingSession, Transaction, Vehicle, ParkingSlot
from services import slot_service


def total_vehicles() -> int:
    return Vehicle.query.count()


def active_sessions_count() -> int:
    return ParkingSession.query.filter_by(status="Active").count()


def revenue_for_date(target_date: date) -> float:
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)
    total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.transaction_type == "Deduction",
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .scalar()
    )
    return round(total or 0.0, 2)


def revenue_today() -> float:
    return revenue_for_date(date.today())


def revenue_this_month() -> float:
    today = date.today()
    start = datetime(today.year, today.month, 1)
    total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.transaction_type == "Deduction",
            Transaction.created_at >= start,
        )
        .scalar()
    )
    return round(total or 0.0, 2)


def compliance_violation_count(warning_days: int = 30) -> int:
    vehicles = Vehicle.query.all()
    return sum(1 for v in vehicles if v.overall_compliance_status(warning_days) != "Valid")


def dashboard_summary() -> dict:
    occ = slot_service.occupancy_summary()
    return {
        "total_vehicles": total_vehicles(),
        "active_sessions": active_sessions_count(),
        "revenue_today": revenue_today(),
        "revenue_month": revenue_this_month(),
        "available_slots": occ["available"],
        "occupied_slots": occ["occupied"],
        "reserved_slots": occ["reserved"],
        "compliance_violations": compliance_violation_count(),
    }


def daily_parking_trend(days: int = 7) -> dict:
    """Returns {'labels': [...], 'data': [...]} - sessions started per day."""
    today = date.today()
    labels, data = [], []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        count = ParkingSession.query.filter(
            ParkingSession.entry_time >= start, ParkingSession.entry_time < end
        ).count()
        labels.append(d.strftime("%d %b"))
        data.append(count)
    return {"labels": labels, "data": data}


def revenue_trend(days: int = 7) -> dict:
    today = date.today()
    labels, data = [], []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%d %b"))
        data.append(revenue_for_date(d))
    return {"labels": labels, "data": data}


def slot_utilization() -> dict:
    occ = slot_service.occupancy_summary()
    return {
        "labels": ["Available", "Occupied", "Reserved"],
        "data": [occ["available"], occ["occupied"], occ["reserved"]],
    }


def vehicle_type_distribution() -> dict:
    rows = (
        db.session.query(Vehicle.vehicle_type, func.count(Vehicle.id))
        .group_by(Vehicle.vehicle_type)
        .all()
    )
    labels = [r[0] for r in rows]
    data = [r[1] for r in rows]
    return {"labels": labels, "data": data}


def most_used_slot(limit: int = 5):
    rows = (
        db.session.query(ParkingSlot.slot_code, func.count(ParkingSession.id).label("uses"))
        .join(ParkingSession, ParkingSession.slot_id == ParkingSlot.id)
        .group_by(ParkingSlot.slot_code)
        .order_by(func.count(ParkingSession.id).desc())
        .limit(limit)
        .all()
    )
    return [{"slot_code": r[0], "uses": r[1]} for r in rows]


def peak_parking_hours():
    """Returns a 24-length list of entry counts per hour-of-day, all-time."""
    sessions = ParkingSession.query.all()
    hour_counter = Counter(s.entry_time.hour for s in sessions)
    return {"labels": [f"{h:02d}:00" for h in range(24)], "data": [hour_counter.get(h, 0) for h in range(24)]}


def average_parking_duration() -> float:
    avg = (
        db.session.query(func.avg(ParkingSession.duration_minutes))
        .filter(ParkingSession.status == "Completed")
        .scalar()
    )
    return round(avg or 0.0, 1)
