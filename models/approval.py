# models/approval.py

from datetime import datetime
from . import db

class UserApproval(db.Model):
    """User approval workflow"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    comments = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='approval_requests')
    approver = db.relationship('User', foreign_keys=[approved_by])