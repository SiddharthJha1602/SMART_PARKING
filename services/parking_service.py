"""
services/parking_service.py
Handles vehicle entry, exit, fee calculation, and receipt generation.
"""

import math
from datetime import datetime

from extensions import db
from models import ParkingSession, Vehicle, Notification
from services import slot_service, wallet_service


class VehicleAlreadyParkedError(Exception):
    pass


class NoActiveSessionError(Exception):
    pass


def vehicle_entry(vehicle: Vehicle, slot_type: str = None, slot_id: int = None) -> ParkingSession:
    """
    Record a vehicle entry. If slot_id is given, use manual allocation;
    otherwise auto-allocate based on the vehicle's type.
    """
    existing_active = ParkingSession.query.filter_by(
        vehicle_id=vehicle.id, status="Active"
    ).first()
    if existing_active:
        raise VehicleAlreadyParkedError(
            f"Vehicle {vehicle.vehicle_number} already has an active parking session."
        )

    if slot_id:
        slot = slot_service.manual_allocate_slot(slot_id)
    else:
        slot = slot_service.auto_allocate_slot(slot_type or vehicle.vehicle_type)

    session = ParkingSession(
        vehicle_id=vehicle.id,
        slot_id=slot.id,
        entry_time=datetime.utcnow(),
        status="Active",
    )
    db.session.add(session)
    db.session.commit()

    notification = Notification(
        user_id=vehicle.user_id,
        title="Vehicle Entry Recorded",
        message=f"{vehicle.vehicle_number} parked at slot {slot.slot_code}.",
        category="entry",
    )
    db.session.add(notification)
    db.session.commit()

    return session


def calculate_fee(entry_time: datetime, exit_time: datetime, rate_per_hour: float, min_charge: float) -> tuple:
    """Returns (duration_minutes, fee)."""
    duration = exit_time - entry_time
    duration_minutes = max(int(duration.total_seconds() // 60), 0)
    hours = math.ceil(duration_minutes / 60) if duration_minutes > 0 else 0
    fee = max(hours * rate_per_hour, min_charge if duration_minutes > 0 else 0)
    return duration_minutes, round(fee, 2)


def vehicle_exit(
    vehicle: Vehicle,
    rate_per_hour: float,
    min_charge: float,
    allow_negative_balance: bool = True,
) -> ParkingSession:
    session = ParkingSession.query.filter_by(vehicle_id=vehicle.id, status="Active").first()
    if session is None:
        raise NoActiveSessionError(f"No active parking session found for {vehicle.vehicle_number}.")

    exit_time = datetime.utcnow()
    duration_minutes, fee = calculate_fee(session.entry_time, exit_time, rate_per_hour, min_charge)

    session.exit_time = exit_time
    session.duration_minutes = duration_minutes
    session.fee_charged = fee
    session.status = "Completed"

    txn = wallet_service.deduct_funds(
        vehicle,
        fee,
        description=f"Parking fee for session #{session.id}",
        parking_session_id=session.id,
        allow_negative=allow_negative_balance,
    )

    slot_service.release_slot(session.slot_id)
    db.session.commit()

    notif1 = Notification(
        user_id=vehicle.user_id,
        title="Vehicle Exit Recorded",
        message=f"{vehicle.vehicle_number} exited after {duration_minutes} min. Fee: ₹{fee:.2f}.",
        category="exit",
    )
    notif2 = Notification(
        user_id=vehicle.user_id,
        title="Wallet Deduction",
        message=f"₹{fee:.2f} deducted. New balance: ₹{vehicle.wallet_balance:.2f}.",
        category="wallet",
    )
    db.session.add_all([notif1, notif2])
    db.session.commit()

    return session


def get_parking_history(vehicle_id: int = None, limit: int = None):
    query = ParkingSession.query
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    query = query.order_by(ParkingSession.entry_time.desc())
    if limit:
        query = query.limit(limit)
    return query.all()
