"""
models/__init__.py
Aggregates all ORM models so other modules can do:
    from models import User, Vehicle, ParkingSlot, ...
"""

from models.user import User
from models.vehicle import Vehicle
from models.parking_slot import ParkingSlot
from models.parking_session import ParkingSession
from models.transaction import Transaction
from models.notification import Notification
from models.reservation import Reservation
from models.compliance_log import ComplianceLog

__all__ = [
    "User",
    "Vehicle",
    "ParkingSlot",
    "ParkingSession",
    "Transaction",
    "Notification",
    "Reservation",
    "ComplianceLog",
]
