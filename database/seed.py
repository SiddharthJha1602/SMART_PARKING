"""
database/seed.py
Seeds the database with:
    - An admin account
    - A couple of demo user accounts
    - Parking zones A and B (5 slots each)
    - Sample vehicles with varied compliance states
    - A few historical parking sessions / transactions for charts to
      have something to show immediately after setup

Run with:
    python database/seed.py
"""

import os
import sys
from datetime import date, datetime, timedelta

# Allow running this script directly (adds project root to sys.path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from extensions import db
from models import User, Vehicle, ParkingSlot, ParkingSession, Transaction, Notification


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.filter_by(role="admin").first():
            print("Database already seeded. Skipping.")
            return

        # --- Admin account ---
        admin = User(
            full_name="System Administrator",
            email="admin@smartparking.com",
            phone="9999999999",
            role="admin",
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # --- Demo user accounts ---
        user1 = User(full_name="Rahul Sharma", email="rahul@example.com", phone="9876543210", role="user")
        user1.set_password("User@123")

        user2 = User(full_name="Priya Verma", email="priya@example.com", phone="9123456780", role="user")
        user2.set_password("User@123")

        db.session.add_all([user1, user2])
        db.session.commit()

        # --- Parking slots: Zone A and Zone B, 5 each ---
        slots = []
        for zone in ["A", "B"]:
            for i in range(1, 6):
                slot_type = "Bike" if zone == "B" and i <= 2 else "Car"
                slots.append(ParkingSlot(slot_code=f"{zone}{i}", zone=zone, slot_type=slot_type))
        db.session.add_all(slots)
        db.session.commit()

        # --- Sample vehicles with varied compliance states ---
        today = date.today()
        vehicles = [
            Vehicle(
                vehicle_number="RJ14AB1234",
                owner_name="Rahul Sharma",
                vehicle_type="Car",
                registration_date=today - timedelta(days=600),
                insurance_expiry=today + timedelta(days=200),   # Valid
                puc_expiry=today + timedelta(days=15),           # Expiring Soon
                wallet_balance=750.0,
                user_id=user1.id,
            ),
            Vehicle(
                vehicle_number="RJ14CD5678",
                owner_name="Rahul Sharma",
                vehicle_type="Bike",
                registration_date=today - timedelta(days=300),
                insurance_expiry=today - timedelta(days=10),     # Expired
                puc_expiry=today + timedelta(days=100),
                wallet_balance=200.0,
                user_id=user1.id,
            ),
            Vehicle(
                vehicle_number="DL05XY9090",
                owner_name="Priya Verma",
                vehicle_type="Car",
                registration_date=today - timedelta(days=900),
                insurance_expiry=today + timedelta(days=365),
                puc_expiry=today + timedelta(days=365),
                wallet_balance=1000.0,
                user_id=user2.id,
            ),
        ]
        db.session.add_all(vehicles)
        db.session.commit()

        # --- A couple of completed sessions in the past few days for chart data ---
        slot_a3 = ParkingSlot.query.filter_by(slot_code="A3").first()
        slot_a4 = ParkingSlot.query.filter_by(slot_code="A4").first()

        for i, (vehicle, slot, hours_ago, duration_min, fee) in enumerate([
            (vehicles[2], slot_a3, 26, 90, 40.0),
            (vehicles[0], slot_a4, 50, 45, 20.0),
            (vehicles[2], slot_a3, 75, 120, 40.0),
        ]):
            entry = datetime.utcnow() - timedelta(hours=hours_ago)
            exit_ = entry + timedelta(minutes=duration_min)
            session = ParkingSession(
                vehicle_id=vehicle.id,
                slot_id=slot.id,
                entry_time=entry,
                exit_time=exit_,
                duration_minutes=duration_min,
                fee_charged=fee,
                status="Completed",
            )
            db.session.add(session)
            db.session.flush()

            vehicle.wallet_balance -= fee
            txn = Transaction(
                vehicle_id=vehicle.id,
                parking_session_id=session.id,
                transaction_type="Deduction",
                amount=fee,
                balance_after=vehicle.wallet_balance,
                description=f"Parking fee for session #{session.id}",
                created_at=exit_,
            )
            db.session.add(txn)

        db.session.commit()

        print("Database seeded successfully.")
        print("-" * 50)
        print("Admin login:  admin@smartparking.com / Admin@123")
        print("User login:   rahul@example.com / User@123")
        print("User login:   priya@example.com / User@123")
        print("-" * 50)


if __name__ == "__main__":
    seed()
