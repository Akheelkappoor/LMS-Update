# models/email_template.py

from datetime import datetime
from . import db

class EmailTemplate(db.Model):
    """Email templates for system notifications"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    body_text = db.Column(db.Text)
    template_type = db.Column(db.String(50))  # welcome, password_reset, approval, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)