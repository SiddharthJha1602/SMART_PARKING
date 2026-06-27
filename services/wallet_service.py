"""
services/wallet_service.py
Simulated FASTag wallet: top-ups, automatic deductions, and
transaction history. No external payment gateway is involved -
everything is tracked inside the local database.
"""

from extensions import db
from models import Vehicle, Transaction


class InsufficientBalanceError(Exception):
    """Raised when a vehicle's wallet does not have enough balance for a deduction."""


def add_funds(vehicle: Vehicle, amount: float, description: str = "Wallet top-up") -> Transaction:
    if amount <= 0:
        raise ValueError("Top-up amount must be positive.")

    vehicle.wallet_balance += amount
    txn = Transaction(
        vehicle_id=vehicle.id,
        transaction_type="Top-up",
        amount=amount,
        balance_after=vehicle.wallet_balance,
        description=description,
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def deduct_funds(
    vehicle: Vehicle,
    amount: float,
    description: str = "Parking fee",
    parking_session_id: int = None,
    allow_negative: bool = True,
) -> Transaction:
    """
    Deduct parking fee from the vehicle's wallet. By default allows the
    balance to go negative (mirrors real FASTag behavior where a
    penalty/negative balance is recorded rather than blocking exit),
    but callers can set allow_negative=False to enforce a hard stop.
    """
    if amount < 0:
        raise ValueError("Deduction amount cannot be negative.")

    if not allow_negative and vehicle.wallet_balance < amount:
        raise InsufficientBalanceError(
            f"Insufficient wallet balance. Available: ₹{vehicle.wallet_balance:.2f}, "
            f"Required: ₹{amount:.2f}"
        )

    vehicle.wallet_balance -= amount
    txn = Transaction(
        vehicle_id=vehicle.id,
        parking_session_id=parking_session_id,
        transaction_type="Deduction",
        amount=amount,
        balance_after=vehicle.wallet_balance,
        description=description,
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def get_transaction_history(vehicle_id: int):
    return (
        Transaction.query.filter_by(vehicle_id=vehicle_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
