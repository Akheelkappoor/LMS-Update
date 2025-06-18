# models/notifications.py - FIXED VERSION (replace your current file)

from datetime import datetime
import json
from . import db

class SystemNotification(db.Model):
    """System-wide notifications"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Notification details
    notification_type = db.Column(db.String(50), nullable=False)  # system, user, tutor, finance, etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Targeting
    recipient_type = db.Column(db.String(20), nullable=False)  # user, role, department, all
    recipient_id = db.Column(db.Integer)  # User ID if targeted to specific user
    recipient_role = db.Column(db.String(20))  # Role if targeted to role
    recipient_department = db.Column(db.Integer, db.ForeignKey('department.id'))  # Department if targeted
    recipient_email = db.Column(db.String(120))  # For email notifications
    
    # Status tracking
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    is_email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    
    # Action tracking
    action_required = db.Column(db.Boolean, default=False)
    action_taken = db.Column(db.Boolean, default=False)
    action_taken_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    action_taken_at = db.Column(db.DateTime)
    
    # Links and references
    related_entity_type = db.Column(db.String(50))  # class, user, student, etc.
    related_entity_id = db.Column(db.Integer)
    action_url = db.Column(db.String(500))  # URL for action button
    
    # Additional data - CHANGED FROM 'metadata' to 'extra_data'
    extra_data = db.Column(db.Text)  # JSON for additional data
    
    # Expiry and cleanup
    expires_at = db.Column(db.DateTime)
    auto_delete = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    action_taker = db.relationship('User', foreign_keys=[action_taken_by])
    
    def get_extra_data(self):
        """Get extra data as Python object"""
        if self.extra_data:
            return json.loads(self.extra_data)
        return {}
    
    def set_extra_data(self, data_dict):
        """Set extra data from Python object"""
        self.extra_data = json.dumps(data_dict)


class TutorLateArrival(db.Model):
    """Track tutor late arrivals for payroll deductions"""
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    
    # Late arrival details
    scheduled_time = db.Column(db.DateTime, nullable=False)
    actual_arrival_time = db.Column(db.DateTime, nullable=False)
    late_minutes = db.Column(db.Integer, nullable=False)
    
    # Financial impact
    penalty_amount = db.Column(db.Float, default=0.0)
    penalty_applied = db.Column(db.Boolean, default=False)
    penalty_reason = db.Column(db.String(200))
    
    # Approval and review
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    approval_status = db.Column(db.String(20), default='pending')  # pending, approved, waived
    
    # Justification
    tutor_explanation = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    
    # Notification tracking
    tutor_notified = db.Column(db.Boolean, default=False)
    finance_notified = db.Column(db.Boolean, default=False)
    coordinator_notified = db.Column(db.Boolean, default=False)
    
    # Metadata
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='late_arrivals')
    class_session = db.relationship('Class', foreign_keys=[class_id])
    approver = db.relationship('User', foreign_keys=[approved_by])
    recorder = db.relationship('User', foreign_keys=[recorded_by])