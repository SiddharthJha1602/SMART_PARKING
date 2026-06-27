"""
routes/user.py
Regular-user features: profile, vehicle registration, wallet,
parking history, reservations, and notifications.
"""

from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from extensions import db
from models import Vehicle, ParkingSlot, Notification, Reservation
from forms import VehicleForm, TopUpForm, ReservationForm
from services import wallet_service, parking_service, slot_service, reservation_service, compliance_service
from services.reservation_service import DoubleBookingError
from services.slot_service import NoAvailableSlotError

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/dashboard")
@login_required
def dashboard():
    vehicles = current_user.vehicles

    history = []
    for v in vehicles:
        history.extend(v.parking_sessions)
    history.sort(key=lambda s: s.entry_time, reverse=True)
    history = history[:5]

    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    return render_template(
        "user/dashboard.html",
        vehicles=vehicles,
        recent_history=history,
        unread_notifications=unread_notifications,
    )


@user_bp.route("/profile")
@login_required
def profile():
    return render_template("user/profile.html")


# --- Vehicle Registration ---
@user_bp.route("/vehicles")
@login_required
def my_vehicles():
    return render_template("user/vehicles.html", vehicles=current_user.vehicles)


@user_bp.route("/vehicles/add", methods=["GET", "POST"])
@login_required
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        normalized_number = form.vehicle_number.data.upper().strip()
        existing = Vehicle.query.filter_by(vehicle_number=normalized_number).first()
        if existing:
            flash("A vehicle with this number is already registered.", "danger")
            return render_template("user/vehicle_form.html", form=form, mode="add")

        vehicle = Vehicle(
            vehicle_number=normalized_number,
            owner_name=form.owner_name.data.strip(),
            vehicle_type=form.vehicle_type.data,
            registration_date=form.registration_date.data,
            insurance_expiry=form.insurance_expiry.data,
            puc_expiry=form.puc_expiry.data,
            user_id=current_user.id,
            wallet_balance=500.0,
        )
        db.session.add(vehicle)
        db.session.commit()
        flash("Vehicle registered successfully.", "success")
        return redirect(url_for("user.my_vehicles"))

    return render_template("user/vehicle_form.html", form=form, mode="add")


@user_bp.route("/vehicles/<int:vehicle_id>")
@login_required
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    transactions = wallet_service.get_transaction_history(vehicle.id)
    return render_template("user/vehicle_detail.html", vehicle=vehicle, transactions=transactions)


@user_bp.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    if request.method == "GET":
        form = VehicleForm(
            vehicle_number=vehicle.vehicle_number,
            owner_name=vehicle.owner_name,
            vehicle_type=vehicle.vehicle_type,
            registration_date=vehicle.registration_date,
            insurance_expiry=vehicle.insurance_expiry,
            puc_expiry=vehicle.puc_expiry,
        )
    else:
        form = VehicleForm()

    if form.validate_on_submit():
        normalized_number = form.vehicle_number.data.upper().strip()
        duplicate = Vehicle.query.filter(
            Vehicle.vehicle_number == normalized_number, Vehicle.id != vehicle.id
        ).first()
        if duplicate:
            flash("Another vehicle already uses this number.", "danger")
            return render_template("user/vehicle_form.html", form=form, mode="edit", vehicle=vehicle)

        vehicle.vehicle_number = normalized_number
        vehicle.owner_name = form.owner_name.data.strip()
        vehicle.vehicle_type = form.vehicle_type.data
        vehicle.registration_date = form.registration_date.data
        vehicle.insurance_expiry = form.insurance_expiry.data
        vehicle.puc_expiry = form.puc_expiry.data
        db.session.commit()
        flash("Vehicle details updated.", "success")
        return redirect(url_for("user.vehicle_detail", vehicle_id=vehicle.id))

    return render_template("user/vehicle_form.html", form=form, mode="edit", vehicle=vehicle)


@user_bp.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    db.session.delete(vehicle)
    db.session.commit()
    flash("Vehicle removed.", "info")
    return redirect(url_for("user.my_vehicles"))


# --- Wallet ---
@user_bp.route("/vehicles/<int:vehicle_id>/wallet", methods=["GET", "POST"])
@login_required
def wallet(vehicle_id):
    vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=current_user.id).first_or_404()
    form = TopUpForm()
    if form.validate_on_submit():
        wallet_service.add_funds(vehicle, form.amount.data, description="Wallet top-up via portal")
        flash(f"₹{form.amount.data:.2f} added to wallet.", "success")
        return redirect(url_for("user.wallet", vehicle_id=vehicle.id))

    transactions = wallet_service.get_transaction_history(vehicle.id)
    return render_template("user/wallet.html", vehicle=vehicle, form=form, transactions=transactions)


# --- Parking History ---
@user_bp.route("/history")
@login_required
def parking_history():
    vehicle_ids = [v.id for v in current_user.vehicles]
    sessions = []
    for vid in vehicle_ids:
        sessions.extend(parking_service.get_parking_history(vehicle_id=vid))
    sessions.sort(key=lambda s: s.entry_time, reverse=True)
    return render_template("user/history.html", sessions=sessions)


# --- Reservations ---
@user_bp.route("/reservations", methods=["GET", "POST"])
@login_required
def reservations():
    form = ReservationForm()
    form.vehicle_id.choices = [(v.id, v.vehicle_number) for v in current_user.vehicles]
    available_slots = slot_service.get_available_slots()
    form.slot_id.choices = [(s.id, f"{s.slot_code} ({s.zone})") for s in available_slots]

    if form.validate_on_submit():
        vehicle = Vehicle.query.filter_by(id=form.vehicle_id.data, user_id=current_user.id).first()
        if vehicle is None:
            flash("Invalid vehicle selection.", "danger")
        elif not vehicle.is_compliant():
            flash("This vehicle has expired insurance or PUC and cannot be reserved a slot.", "danger")
        else:
            try:
                reservation_service.create_reservation(current_user.id, vehicle, form.slot_id.data)
                flash("Slot reserved successfully.", "success")
                return redirect(url_for("user.reservations"))
            except DoubleBookingError as e:
                flash(str(e), "danger")
            except NoAvailableSlotError as e:
                flash(str(e), "danger")

    my_reservations = reservation_service.get_user_reservations(current_user.id)
    return render_template("user/reservations.html", form=form, reservations=my_reservations)


@user_bp.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(reservation_id):
    try:
        reservation_service.cancel_reservation(reservation_id, user_id=current_user.id)
        flash("Reservation cancelled.", "info")
    except (ValueError, PermissionError) as e:
        flash(str(e), "danger")
    return redirect(url_for("user.reservations"))


# --- Notifications ---
@user_bp.route("/notifications")
@login_required
def notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()
    # Mark all as read when viewed
    for n in notes:
        n.is_read = True
    db.session.commit()
    return render_template("user/notifications.html", notifications=notes)
