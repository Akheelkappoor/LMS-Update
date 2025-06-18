# models/enrollment.py

from datetime import datetime
import json
from . import db

class StudentEnrollment(db.Model):
    """Student enrollment in subjects"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Course details
    subject = db.Column(db.String(100), nullable=False)
    class_type = db.Column(db.String(50), default='regular')  # regular, trial, demo, batch
    
    # Schedule details
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    sessions_per_week = db.Column(db.Integer, default=1)
    session_duration = db.Column(db.Integer, default=60)  # minutes
    
    # Schedule data (JSON) - stores day/time combinations
    schedule_data = db.Column(db.Text)  # JSON: [{"day": "monday", "time": "14:00"}, ...]
    
    # Status and tracking
    status = db.Column(db.String(20), default='active')  # active, inactive, completed, cancelled
    total_sessions = db.Column(db.Integer, default=0)
    completed_sessions = db.Column(db.Integer, default=0)
    
    # Financial
    fee_per_session = db.Column(db.Float, default=0.0)
    total_fee = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    
    # Metadata
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='tutor_enrollments')
    creator = db.relationship('User', foreign_keys=[created_by])
    classes = db.relationship('Class', backref='enrollment')
    
    def get_schedule(self):
        """Get schedule as list"""
        if self.schedule_data:
            return json.loads(self.schedule_data)
        return []
    
    def set_schedule(self, schedule_list):
        """Set schedule from list"""
        self.schedule_data = json.dumps(schedule_list)