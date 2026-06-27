"""
services/slot_service.py
Business logic for parking slot allocation, release, and occupancy
tracking. Kept separate from routes so it can be reused by the OCR
entry workflow, the manual admin workflow, and the reservation system.
"""

from extensions import db
from models import ParkingSlot
from models.parking_slot import (
    SLOT_STATUS_AVAILABLE,
    SLOT_STATUS_OCCUPIED,
    SLOT_STATUS_RESERVED,
)


class NoAvailableSlotError(Exception):
    """Raised when there is no free slot matching the requested type."""


def get_available_slots(slot_type: str = None):
    query = ParkingSlot.query.filter_by(status=SLOT_STATUS_AVAILABLE)
    if slot_type:
        query = query.filter_by(slot_type=slot_type)
    return query.order_by(ParkingSlot.slot_code).all()


def auto_allocate_slot(slot_type: str = "Car") -> ParkingSlot:
    """
    Automatically pick the first available slot matching the vehicle type.
    Falls back to any available slot if no type-matched slot exists.
    """
    slot = (
        ParkingSlot.query.filter_by(status=SLOT_STATUS_AVAILABLE, slot_type=slot_type)
        .order_by(ParkingSlot.slot_code)
        .first()
    )
    if slot is None:
        slot = (
            ParkingSlot.query.filter_by(status=SLOT_STATUS_AVAILABLE)
            .order_by(ParkingSlot.slot_code)
            .first()
        )
    if slot is None:
        raise NoAvailableSlotError("No available parking slots at this time.")

    slot.status = SLOT_STATUS_OCCUPIED
    db.session.commit()
    return slot


def manual_allocate_slot(slot_id: int) -> ParkingSlot:
    slot = ParkingSlot.query.get(slot_id)
    if slot is None:
        raise ValueError("Slot not found.")
    if slot.status != SLOT_STATUS_AVAILABLE:
        raise NoAvailableSlotError(f"Slot {slot.slot_code} is not available.")

    slot.status = SLOT_STATUS_OCCUPIED
    db.session.commit()
    return slot


def reserve_slot(slot_id: int) -> ParkingSlot:
    slot = ParkingSlot.query.get(slot_id)
    if slot is None:
        raise ValueError("Slot not found.")
    if slot.status != SLOT_STATUS_AVAILABLE:
        raise NoAvailableSlotError(f"Slot {slot.slot_code} is not available for reservation.")

    slot.status = SLOT_STATUS_RESERVED
    db.session.commit()
    return slot


def release_slot(slot_id: int) -> ParkingSlot:
    slot = ParkingSlot.query.get(slot_id)
    if slot is None:
        raise ValueError("Slot not found.")

    slot.status = SLOT_STATUS_AVAILABLE
    db.session.commit()
    return slot


def occupancy_summary() -> dict:
    total = ParkingSlot.query.count()
    available = ParkingSlot.query.filter_by(status=SLOT_STATUS_AVAILABLE).count()
    occupied = ParkingSlot.query.filter_by(status=SLOT_STATUS_OCCUPIED).count()
    reserved = ParkingSlot.query.filter_by(status=SLOT_STATUS_RESERVED).count()
    return {
        "total": total,
        "available": available,
        "occupied": occupied,
        "reserved": reserved,
    }
