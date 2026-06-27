"""
utils/decorators.py
Role-based access control helpers built on top of Flask-Login.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def user_required(view_func):
    """Allows any authenticated user (admin or regular user)."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped
