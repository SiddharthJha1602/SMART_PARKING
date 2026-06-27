# Smart Vehicle Compliance & Automated Parking Management System

A full-stack Flask academic project: license-plate recognition (OpenCV + EasyOCR),
automated slot allocation, a simulated FASTag wallet, compliance verification
(insurance/PUC), reservations, notifications, an admin dashboard with charts,
and PDF/CSV reports. Runs entirely on localhost with SQLite — no paid APIs,
no external hardware, no government databases.

## Quick start

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
# Note: EasyOCR will download its detection/recognition model weights
# (~100MB+) the first time it runs — this happens automatically on first
# plate-recognition upload, and needs an internet connection just that once.

# 3. Seed the database (creates admin + demo users + slots + sample data)
python database/seed.py

# 4. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Demo accounts

| Role  | Email                      | Password   |
|-------|-----------------------------|------------|
| Admin | admin@smartparking.com      | Admin@123  |
| User  | rahul@example.com           | User@123   |
| User  | priya@example.com           | User@123   |

## Project structure

```
smart_parking/
├── app.py                  # Application factory & entry point
├── config.py                # Environment-based configuration
├── extensions.py             # Flask-SQLAlchemy, Flask-Login, CSRF instances
├── forms.py                  # WTForms definitions
├── requirements.txt
├── models/                   # SQLAlchemy ORM models
├── routes/                   # Blueprints: auth, admin, user, ocr_routes, api, main
├── services/                  # Business logic (slots, wallet, parking, compliance,
│                                 reservations, analytics, reports)
├── ocr/                      # OpenCV + EasyOCR plate recognition pipeline
├── templates/                 # Jinja2 templates (base shell + admin/user/auth/ocr pages)
├── static/                   # CSS + JS
├── database/
│   ├── seed.py                # Seeds admin/demo users, slots, sample vehicles
│   └── parking.db             # SQLite database (created on first run/seed)
├── uploads/                   # Uploaded vehicle photos for OCR
└── reports/                   # Generated PDF/CSV reports land here
```

## Notes

- To reset the database from scratch: delete `database/parking.db` and re-run
  `python database/seed.py`.
- To migrate to MySQL later, change `SQLALCHEMY_DATABASE_URI` in `config.py`
  (or set the `DATABASE_URL` environment variable) to a MySQL connection string —
  the schema is written to be portable.
- The FASTag wallet, insurance, and PUC data are all simulated and stored
  locally; nothing here calls a real payment gateway or government API.
- EasyOCR runs in CPU mode by default (`OCR_GPU = False` in `config.py`) so it
  works on a standard laptop without a GPU.
