from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .enrollment import enrollment_bp
from .attendance import attendance_bp
from .admin import admin_bp
from .super_admin import super_admin_bp
from .user import user_bp
from .face import face_bp

__all__ = [
    'auth_bp',
    'enrollment_bp',
    'attendance_bp',
    'admin_bp',
    'super_admin_bp',
    'user_bp',
    'face_bp'
]
