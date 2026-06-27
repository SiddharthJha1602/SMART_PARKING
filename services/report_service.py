"""
services/report_service.py
Generates Parking, Revenue, Compliance, and User Activity reports
as PDF (via reportlab) or CSV (via pandas).
"""

import os
import csv
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from models import ParkingSession, Transaction, Vehicle, User
from services import compliance_service


def _timestamped_filename(prefix: str, ext: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"


def _write_pdf(filepath: str, title: str, headers: list, rows: list):
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 16)]

    table_data = [headers] + rows
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)


def _write_csv(filepath: str, headers: list, rows: list):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


# --- Parking Report ---
def generate_parking_report(reports_folder: str, fmt: str = "pdf") -> str:
    sessions = ParkingSession.query.order_by(ParkingSession.entry_time.desc()).all()
    headers = ["Session ID", "Vehicle", "Slot", "Entry Time", "Exit Time", "Duration (min)", "Fee", "Status"]
    rows = []
    for s in sessions:
        rows.append(
            [
                s.id,
                s.vehicle.vehicle_number if s.vehicle else "-",
                s.slot.slot_code if s.slot else "-",
                s.entry_time.strftime("%Y-%m-%d %H:%M"),
                s.exit_time.strftime("%Y-%m-%d %H:%M") if s.exit_time else "-",
                s.duration_minutes or "-",
                f"₹{s.fee_charged:.2f}" if s.fee_charged is not None else "-",
                s.status,
            ]
        )

    ext = "pdf" if fmt == "pdf" else "csv"
    filename = _timestamped_filename("parking_report", ext)
    filepath = os.path.join(reports_folder, filename)

    if fmt == "pdf":
        _write_pdf(filepath, "Parking Report", headers, rows)
    else:
        _write_csv(filepath, headers, rows)
    return filepath


# --- Revenue Report ---
def generate_revenue_report(reports_folder: str, fmt: str = "pdf") -> str:
    txns = (
        Transaction.query.filter_by(transaction_type="Deduction")
        .order_by(Transaction.created_at.desc())
        .all()
    )
    headers = ["Transaction ID", "Vehicle", "Amount", "Balance After", "Date", "Description"]
    rows = []
    for t in txns:
        rows.append(
            [
                t.id,
                t.vehicle.vehicle_number if t.vehicle else "-",
                f"₹{t.amount:.2f}",
                f"₹{t.balance_after:.2f}",
                t.created_at.strftime("%Y-%m-%d %H:%M"),
                t.description or "-",
            ]
        )

    ext = "pdf" if fmt == "pdf" else "csv"
    filename = _timestamped_filename("revenue_report", ext)
    filepath = os.path.join(reports_folder, filename)

    if fmt == "pdf":
        _write_pdf(filepath, "Revenue Report", headers, rows)
    else:
        _write_csv(filepath, headers, rows)
    return filepath


# --- Compliance Report ---
def generate_compliance_report(reports_folder: str, fmt: str = "pdf") -> str:
    violations = compliance_service.get_all_violations()
    headers = ["Vehicle Number", "Owner", "Insurance Status", "PUC Status", "Overall Status"]
    rows = []
    for v in violations:
        vehicle = v["vehicle"]
        rows.append(
            [
                vehicle.vehicle_number,
                vehicle.owner_name,
                v["insurance_status"],
                v["puc_status"],
                v["overall_status"],
            ]
        )

    ext = "pdf" if fmt == "pdf" else "csv"
    filename = _timestamped_filename("compliance_report", ext)
    filepath = os.path.join(reports_folder, filename)

    if fmt == "pdf":
        _write_pdf(filepath, "Compliance Violations Report", headers, rows)
    else:
        _write_csv(filepath, headers, rows)
    return filepath


# --- User Activity Report ---
def generate_user_activity_report(reports_folder: str, fmt: str = "pdf") -> str:
    users = User.query.filter_by(role="user").all()
    headers = ["User", "Email", "Vehicles", "Total Sessions", "Total Spent"]
    rows = []
    for u in users:
        vehicle_ids = [v.id for v in u.vehicles]
        sessions = ParkingSession.query.filter(ParkingSession.vehicle_id.in_(vehicle_ids)).all() if vehicle_ids else []
        total_spent = sum(s.fee_charged or 0 for s in sessions)
        rows.append(
            [
                u.full_name,
                u.email,
                len(u.vehicles),
                len(sessions),
                f"₹{total_spent:.2f}",
            ]
        )

    ext = "pdf" if fmt == "pdf" else "csv"
    filename = _timestamped_filename("user_activity_report", ext)
    filepath = os.path.join(reports_folder, filename)

    if fmt == "pdf":
        _write_pdf(filepath, "User Activity Report", headers, rows)
    else:
        _write_csv(filepath, headers, rows)
    return filepath
