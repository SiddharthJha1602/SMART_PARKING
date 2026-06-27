"""
routes/admin.py
Admin dashboard, user/vehicle/slot management, transactions,
compliance violations, and report generation.
"""

import os
from datetime import date

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, send_file, jsonify
)
from flask_login import login_required, current_user

from extensions import db
from models import User, Vehicle, ParkingSlot, ParkingSession, Transaction, Reservation
from forms import VehicleForm
from services import analytics_service, slot_service, compliance_service, report_service
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    summary = analytics_service.dashboard_summary()
    parking_trend = analytics_service.daily_parking_trend(7)
    revenue_trend = analytics_service.revenue_trend(7)
    slot_util = analytics_service.slot_utilization()
    vehicle_dist = analytics_service.vehicle_type_distribution()

    return render_template(
        "admin/dashboard.html",
        summary=summary,
        parking_trend=parking_trend,
        revenue_trend=revenue_trend,
        slot_util=slot_util,
        vehicle_dist=vehicle_dist,
    )


# --- User Management ---
@admin_bp.route("/users")
@login_required
@admin_required
def manage_users():
    search = request.args.get("search", "").strip()
    query = User.query
    if search:
        query = query.filter(
            db.or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, search=search)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "warning")
        return redirect(url_for("admin.manage_users"))

    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash(f"User {user.full_name} {'activated' if user.is_active_account else 'deactivated'}.", "success")
    return redirect(url_for("admin.manage_users"))


# --- Vehicle Management ---
@admin_bp.route("/vehicles")
@login_required
@admin_required
def manage_vehicles():
    search = request.args.get("search", "").strip()
    query = Vehicle.query
    if search:
        query = query.filter(
            db.or_(
                Vehicle.vehicle_number.ilike(f"%{search}%"),
                Vehicle.owner_name.ilike(f"%{search}%"),
            )
        )
    vehicles = query.order_by(Vehicle.created_at.desc()).all()
    return render_template("admin/vehicles.html", vehicles=vehicles, search=search)


@admin_bp.route("/vehicles/<int:vehicle_id>")
@login_required
@admin_required
def vehicle_detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    sessions = analytics_service  # not used directly; history fetched below
    history = vehicle.parking_sessions
    transactions = vehicle.transactions
    return render_template(
        "admin/vehicle_detail.html", vehicle=vehicle, history=history, transactions=transactions
    )


@admin_bp.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = VehicleForm(obj=vehicle)
    if request.method == "GET":
        form = VehicleForm(
            vehicle_number=vehicle.vehicle_number,
            owner_name=vehicle.owner_name,
            vehicle_type=vehicle.vehicle_type,
            registration_date=vehicle.registration_date,
            insurance_expiry=vehicle.insurance_expiry,
            puc_expiry=vehicle.puc_expiry,
        )

    if form.validate_on_submit():
        normalized_number = form.vehicle_number.data.upper().strip()
        duplicate = Vehicle.query.filter(
            Vehicle.vehicle_number == normalized_number, Vehicle.id != vehicle.id
        ).first()
        if duplicate:
            flash("Another vehicle already uses this number.", "danger")
            return render_template("admin/vehicle_form.html", form=form, mode="edit", vehicle=vehicle)

        vehicle.vehicle_number = normalized_number
        vehicle.owner_name = form.owner_name.data.strip()
        vehicle.vehicle_type = form.vehicle_type.data
        vehicle.registration_date = form.registration_date.data
        vehicle.insurance_expiry = form.insurance_expiry.data
        vehicle.puc_expiry = form.puc_expiry.data
        db.session.commit()
        flash("Vehicle updated successfully.", "success")
        return redirect(url_for("admin.vehicle_detail", vehicle_id=vehicle.id))

    return render_template("admin/vehicle_form.html", form=form, mode="edit", vehicle=vehicle)


@admin_bp.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    flash("Vehicle deleted.", "info")
    return redirect(url_for("admin.manage_vehicles"))


# --- Slot Management ---
@admin_bp.route("/slots")
@login_required
@admin_required
def manage_slots():
    slots = ParkingSlot.query.order_by(ParkingSlot.zone, ParkingSlot.slot_code).all()
    occ = slot_service.occupancy_summary()
    return render_template("admin/slots.html", slots=slots, occ=occ)


@admin_bp.route("/slots/<int:slot_id>/release", methods=["POST"])
@login_required
@admin_required
def release_slot(slot_id):
    slot_service.release_slot(slot_id)
    flash("Slot released.", "success")
    return redirect(url_for("admin.manage_slots"))


# --- Transactions ---
@admin_bp.route("/transactions")
@login_required
@admin_required
def view_transactions():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    user_search = request.args.get("user_search", "").strip()

    query = Transaction.query.join(Vehicle).join(User, Vehicle.user_id == User.id)
    if date_from:
        query = query.filter(Transaction.created_at >= date_from)
    if date_to:
        query = query.filter(Transaction.created_at <= f"{date_to} 23:59:59")
    if user_search:
        query = query.filter(
            db.or_(User.full_name.ilike(f"%{user_search}%"), Vehicle.vehicle_number.ilike(f"%{user_search}%"))
        )

    transactions = query.order_by(Transaction.created_at.desc()).all()
    return render_template(
        "admin/transactions.html",
        transactions=transactions,
        date_from=date_from or "",
        date_to=date_to or "",
        user_search=user_search,
    )


# --- Compliance Violations ---
@admin_bp.route("/compliance")
@login_required
@admin_required
def compliance_violations():
    violations = compliance_service.get_all_violations(
        warning_days=current_app.config["COMPLIANCE_WARNING_DAYS"]
    )
    return render_template("admin/compliance.html", violations=violations)


# --- Reports ---
@admin_bp.route("/reports")
@login_required
@admin_required
def reports_home():
    return render_template("admin/reports.html")


@admin_bp.route("/reports/generate/<report_type>/<fmt>")
@login_required
@admin_required
def generate_report(report_type, fmt):
    folder = current_app.config["REPORTS_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    generators = {
        "parking": report_service.generate_parking_report,
        "revenue": report_service.generate_revenue_report,
        "compliance": report_service.generate_compliance_report,
        "user-activity": report_service.generate_user_activity_report,
    }

    if report_type not in generators or fmt not in ("pdf", "csv"):
        flash("Invalid report request.", "danger")
        return redirect(url_for("admin.reports_home"))

    filepath = generators[report_type](folder, fmt=fmt)
    return send_file(filepath, as_attachment=True)
