# models/classes.py

from datetime import datetime
from . import db

class Class(db.Model):
    """Individual class sessions"""
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('student_enrollment.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Class details
    subject = db.Column(db.String(100), nullable=False)
    class_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Status and tracking
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, rescheduled
    actual_start_time = db.Column(db.DateTime)  # When class actually started
    actual_end_time = db.Column(db.DateTime)    # When class actually ended
    
    # Class content
    topic_covered = db.Column(db.String(200))
    homework_assigned = db.Column(db.Text)
    class_notes = db.Column(db.Text)
    
    # Meeting details
    meeting_link = db.Column(db.String(500))
    meeting_id = db.Column(db.String(100))
    meeting_password = db.Column(db.String(50))
    
    # Files and resources
    recording_link = db.Column(db.String(500))
    materials_uploaded = db.Column(db.Text)  # JSON list of file paths
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='taught_classes')
    attendance_records = db.relationship('StudentAttendance', backref='class_session')


class StudentAttendance(db.Model):
    """Student attendance marked by tutors"""
    id = db.Column(db.Integer, primary_key=True)
    class_session_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # Attendance details
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    arrival_time = db.Column(db.DateTime)  # When student actually arrived
    departure_time = db.Column(db.DateTime)  # When student left (if early)
    late_minutes = db.Column(db.Integer, default=0)
    
    # Late student management
    late_reason = db.Column(db.String(200))
    parent_notified = db.Column(db.Boolean, default=False)
    follow_up_required = db.Column(db.Boolean, default=False)
    
    # Behavior and participation
    participation_level = db.Column(db.String(20))  # excellent, good, average, poor
    behavior_notes = db.Column(db.Text)
    homework_submitted = db.Column(db.Boolean, default=False)
    
    # Metadata
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    marker = db.relationship('User', foreign_keys=[marked_by], backref='attendance_records')

custom_fields = db.Column(db.Text)  # JSON for additional class-specific data

def get_custom_fields(self):
    """Get custom fields from JSON"""
    import json
    try:
        return json.loads(self.custom_fields) if self.custom_fields else {}
    except (json.JSONDecodeError, TypeError):
        return {}

def set_custom_fields(self, custom_fields):
    """Set custom fields as JSON"""
    import json
    self.custom_fields = json.dumps(custom_fields) if custom_fields else None