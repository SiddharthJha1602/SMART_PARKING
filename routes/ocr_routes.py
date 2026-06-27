"""
routes/ocr_routes.py
Number-plate-recognition workflow: upload an image, run OpenCV +
EasyOCR, match against the Vehicle table, and optionally record
entry/exit directly from the recognition result.

Also exposes a manual entry/exit path for staff who don't have a
usable photo (kept in this blueprint since it shares the same
vehicle-entry/exit business logic).
"""

import os
import uuid

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Vehicle, ParkingSlot
from forms import PlateUploadForm, ManualEntryForm, ManualExitForm
from ocr import plate_recognition
from services import parking_service, slot_service
from services.parking_service import VehicleAlreadyParkedError, NoActiveSessionError
from services.slot_service import NoAvailableSlotError
from utils.decorators import admin_required

ocr_bp = Blueprint("ocr", __name__, url_prefix="/ocr")


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


@ocr_bp.route("/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload():
    form = PlateUploadForm()
    result = None
    matched_vehicle = None

    if form.validate_on_submit():
        file = form.image.data
        if not _allowed_file(file.filename):
            flash("Unsupported file type. Please upload a JPG, PNG, or BMP image.", "danger")
            return render_template("ocr/upload.html", form=form, result=None, matched_vehicle=None)

        safe_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(upload_path)

        try:
            result = plate_recognition.recognize_plate(upload_path)
            if result["normalized_text"]:
                matched_vehicle = plate_recognition.match_vehicle_by_plate(result["normalized_text"])
            if not result["raw_text"]:
                flash("No text could be detected on this image. Try a clearer photo.", "warning")
            elif matched_vehicle is None:
                flash("Plate text detected, but no matching vehicle was found in the database.", "warning")
        except FileNotFoundError:
            flash("Uploaded file could not be processed.", "danger")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:  # OCR/model errors shouldn't crash the page
            flash(f"OCR processing failed: {e}", "danger")

    return render_template(
        "ocr/upload.html", form=form, result=result, matched_vehicle=matched_vehicle
    )


@ocr_bp.route("/entry/<int:vehicle_id>", methods=["POST"])
@login_required
@admin_required
def record_entry_from_ocr(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if not vehicle.is_compliant():
        flash(
            f"{vehicle.vehicle_number} has expired insurance or PUC. Entry blocked until compliant.",
            "danger",
        )
        return redirect(url_for("ocr.upload"))

    try:
        session = parking_service.vehicle_entry(vehicle, slot_type=vehicle.vehicle_type)
        flash(f"Entry recorded for {vehicle.vehicle_number} at slot {session.slot.slot_code}.", "success")
    except VehicleAlreadyParkedError as e:
        flash(str(e), "warning")
    except NoAvailableSlotError as e:
        flash(str(e), "danger")

    return redirect(url_for("ocr.upload"))


@ocr_bp.route("/manual-entry", methods=["GET", "POST"])
@login_required
@admin_required
def manual_entry():
    form = ManualEntryForm()
    available_slots = slot_service.get_available_slots()
    form.slot_id.choices = [(0, "-- Auto Allocate --")] + [
        (s.id, f"{s.slot_code} ({s.zone})") for s in available_slots
    ]

    if form.validate_on_submit():
        vehicle_number = form.vehicle_number.data.upper().strip()
        vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
        if vehicle is None:
            flash("No vehicle found with this number. Register the vehicle first.", "danger")
        elif not vehicle.is_compliant():
            flash(f"{vehicle.vehicle_number} has expired insurance or PUC. Entry blocked.", "danger")
        else:
            try:
                slot_id = form.slot_id.data if form.slot_id.data not in (0, None) else None
                session = parking_service.vehicle_entry(vehicle, slot_id=slot_id, slot_type=vehicle.vehicle_type)
                flash(f"Entry recorded at slot {session.slot.slot_code}.", "success")
                return redirect(url_for("ocr.manual_entry"))
            except VehicleAlreadyParkedError as e:
                flash(str(e), "warning")
            except NoAvailableSlotError as e:
                flash(str(e), "danger")

    return render_template("ocr/manual_entry.html", form=form)


@ocr_bp.route("/manual-exit", methods=["GET", "POST"])
@login_required
@admin_required
def manual_exit():
    form = ManualExitForm()
    receipt = None

    if form.validate_on_submit():
        vehicle_number = form.vehicle_number.data.upper().strip()
        vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
        if vehicle is None:
            flash("No vehicle found with this number.", "danger")
        else:
            try:
                session = parking_service.vehicle_exit(
                    vehicle,
                    rate_per_hour=current_app.config["PARKING_RATE_PER_HOUR"],
                    min_charge=current_app.config["MIN_CHARGE"],
                )
                receipt = {
                    "vehicle_number": vehicle.vehicle_number,
                    "slot_code": session.slot.slot_code,
                    "entry_time": session.entry_time,
                    "exit_time": session.exit_time,
                    "duration_minutes": session.duration_minutes,
                    "fee_charged": session.fee_charged,
                    "wallet_balance": vehicle.wallet_balance,
                }
                flash("Exit recorded and fee deducted.", "success")
            except NoActiveSessionError as e:
                flash(str(e), "danger")

    return render_template("ocr/manual_exit.html", form=form, receipt=receipt)
