"""
routes/api.py
JSON endpoints used by Chart.js (dashboard charts) and live search
filters. Kept separate from page routes for clarity.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import Vehicle, ParkingSession, Transaction
from services import analytics_service
from utils.decorators import admin_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/charts/parking-trend")
@login_required
@admin_required
def parking_trend():
    days = request.args.get("days", 7, type=int)
    return jsonify(analytics_service.daily_parking_trend(days))


@api_bp.route("/charts/revenue-trend")
@login_required
@admin_required
def revenue_trend():
    days = request.args.get("days", 7, type=int)
    return jsonify(analytics_service.revenue_trend(days))


@api_bp.route("/charts/slot-utilization")
@login_required
@admin_required
def slot_utilization():
    return jsonify(analytics_service.slot_utilization())


@api_bp.route("/charts/vehicle-distribution")
@login_required
@admin_required
def vehicle_distribution():
    return jsonify(analytics_service.vehicle_type_distribution())


@api_bp.route("/charts/peak-hours")
@login_required
@admin_required
def peak_hours():
    return jsonify(analytics_service.peak_parking_hours())


@api_bp.route("/search/vehicles")
@login_required
@admin_required
def search_vehicles():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    vehicles = Vehicle.query.filter(
        (Vehicle.vehicle_number.ilike(f"%{q}%")) | (Vehicle.owner_name.ilike(f"%{q}%"))
    ).limit(10).all()

    return jsonify(
        [
            {
                "id": v.id,
                "vehicle_number": v.vehicle_number,
                "owner_name": v.owner_name,
                "vehicle_type": v.vehicle_type,
                "compliance_status": v.overall_compliance_status(),
            }
            for v in vehicles
        ]
    )
