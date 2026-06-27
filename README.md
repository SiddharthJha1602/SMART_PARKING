# 🚗 Smart Vehicle Compliance & Automated Parking Management System

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![EasyOCR](https://img.shields.io/badge/EasyOCR-License%20Plate%20Recognition-orange)
![Status](https://img.shields.io/badge/Status-Completed-success)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📖 Overview

The **Smart Vehicle Compliance & Automated Parking Management System** is a full-stack Flask web application designed to automate vehicle parking operations while ensuring compliance with essential vehicle regulations.

The system combines **Computer Vision**, **OCR**, and **Web Technologies** to provide intelligent parking management with automatic vehicle identification, compliance verification, parking slot allocation, reservation management, wallet simulation, analytics, and administrative reporting.

Designed as a **college-level major project**, it demonstrates practical applications of Artificial Intelligence and modern web development.

---

# ✨ Features

### 🚘 Vehicle Management

- Register vehicles
- Update vehicle information
- Delete vehicles
- View registered vehicles

### 📷 Automatic Number Plate Recognition

- Upload vehicle image
- Detect license plate using **OpenCV**
- Extract registration number using **EasyOCR**
- Automatic vehicle lookup

### 🅿 Smart Parking

- Automatic parking slot allocation
- Slot reservation system
- Entry & Exit management
- Parking duration calculation
- Parking fee calculation

### 📋 Vehicle Compliance

- Insurance expiry tracking
- PUC expiry verification
- Compliance status dashboard
- Expiry warning notifications

### 💳 FASTag Wallet Simulation

- Wallet creation
- Add balance
- Automatic parking fee deduction
- Transaction history

### 📊 Dashboard & Analytics

- Parking statistics
- Occupancy charts
- Revenue analytics
- Vehicle activity monitoring

### 📄 Reports

- PDF Reports
- CSV Export
- Parking Reports
- Compliance Reports

### 👨‍💼 Admin Panel

- User Management
- Vehicle Management
- Parking Slot Management
- Reports
- Dashboard Analytics

---

# 🛠 Tech Stack

## Backend

- Python
- Flask
- SQLAlchemy
- Flask-Login
- Flask-WTF

## Database

- SQLite

## Frontend

- HTML5
- CSS3
- Bootstrap
- JavaScript

## Computer Vision

- OpenCV
- EasyOCR

## Data Processing

- NumPy
- Pandas

## Report Generation

- ReportLab

---

# 📂 Project Structure

```
smart_parking/
│
├── app.py
├── config.py
├── requirements.txt
├── extensions.py
├── forms.py
│
├── database/
│   ├── parking.db
│   └── seed.py
│
├── models/
│
├── routes/
│
├── services/
│
├── templates/
│
├── static/
│
├── uploads/
│
├── reports/
│
└── ocr/
```

---

# ⚙ Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/smart-parking-system.git

cd smart-parking-system
```

## Create Virtual Environment

```bash
python -m venv venv
```

Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Seed Database

```bash
python database/seed.py
```

---

## Run Project

```bash
python app.py
```

---

Open Browser

```
http://127.0.0.1:5000
```

---

# 🔑 Demo Credentials

## 👨‍💼 Admin

Email

```
admin@smartparking.com
```

Password

```
Admin@123
```

---

## 👤 User

Email

```
rahul@example.com
```

Password

```
User@123
```

---

# 📷 Screenshots

> Add screenshots of the following pages here.

- Home Page
- Login Page
- Dashboard
- Parking Slots
- Vehicle Registration
- OCR Detection
- Reports
- Analytics

---

# 🚀 Future Enhancements

- QR Code Based Parking
- RFID Integration
- AI-based Parking Prediction
- Google Maps Integration
- UPI Payment Gateway
- Email & SMS Notifications
- Cloud Database Support
- Mobile Application
- Real-time Camera Integration
- Vehicle Tracking

---

# 🎯 Learning Outcomes

This project demonstrates practical implementation of:

- Flask Web Development
- MVC Architecture
- SQLAlchemy ORM
- Authentication & Authorization
- OCR Technology
- Computer Vision
- REST APIs
- Database Design
- Dashboard Analytics
- Report Generation
- File Upload Handling

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

---

# 📜 License

This project is developed for educational and academic purposes.

---

# 👨‍💻 Developer

**Siddharth Jha**

B.Tech Computer Science Engineering

Manipal University Jaipur

GitHub: https://github.com/yourusername

LinkedIn: https://linkedin.com/in/yourprofile

---

⭐ If you found this project useful, don't forget to give it a **Star** on GitHub.
