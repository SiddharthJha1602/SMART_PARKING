"""
services/reservation_service.py
Handles slot reservations, ensuring no double-booking occurs.
"""

from datetime import datetime

from extensions import db
from models import Reservation, Notification, Vehicle
from services import slot_service


class DoubleBookingError(Exception):
    pass


def create_reservation(user_id: int, vehicle: Vehicle, slot_id: int, reserved_for: datetime = None) -> Reservation:
    # Prevent double booking: check no other Active reservation exists for this slot
    existing = Reservation.query.filter_by(slot_id=slot_id, status="Active").first()
    if existing:
        raise DoubleBookingError("This slot is already reserved.")

    slot = slot_service.reserve_slot(slot_id)

    reservation = Reservation(
        user_id=user_id,
        vehicle_id=vehicle.id,
        slot_id=slot.id,
        reserved_for=reserved_for or datetime.utcnow(),
        status="Active",
    )
    db.session.add(reservation)
    db.session.commit()

    db.session.add(
        Notification(
            user_id=user_id,
            title="Reservation Confirmed",
            message=f"Slot {slot.slot_code} reserved for vehicle {vehicle.vehicle_number}.",
            category="reservation",
        )
    )
    db.session.commit()

    return reservation


def cancel_reservation(reservation_id: int, user_id: int = None) -> Reservation:
    reservation = Reservation.query.get(reservation_id)
    if reservation is None:
        raise ValueError("Reservation not found.")
    if user_id is not None and reservation.user_id != user_id:
        raise PermissionError("You do not have permission to cancel this reservation.")
    if reservation.status != "Active":
        raise ValueError("Only active reservations can be cancelled.")

    reservation.status = "Cancelled"
    slot_service.release_slot(reservation.slot_id)
    db.session.commit()
    return reservation


def get_user_reservations(user_id: int):
    return (
        Reservation.query.filter_by(user_id=user_id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
