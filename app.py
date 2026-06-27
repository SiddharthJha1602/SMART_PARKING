"""
app.py
Application factory and entry point for the Smart Vehicle Compliance
& Automated Parking Management System.

Run with:
    python app.py
"""

import os
from flask import Flask
from flask_login import current_user

from config import config_map
from extensions import db, login_manager, csrf


def create_app(env: str = None):
    app = Flask(__name__)

    env = env or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env, config_map["default"]))

    # --- Init extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # --- User loader for Flask-Login ---
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register blueprints ---
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.ocr_routes import ocr_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(api_bp)

    # --- Template context: inject compliance-warning days, current year, etc. ---
    from datetime import datetime

    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.utcnow().year,
            "app_name": "Smart Parking System",
        }

    # --- Ensure required directories exist ---
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORTS_FOLDER"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")), exist_ok=True) \
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///") else None

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="127.0.0.1", port=5000)
