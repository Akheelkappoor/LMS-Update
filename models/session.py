# models/session.py

from datetime import datetime
import json
from . import db

class ClassSession(db.Model):
    """Enhanced class session model with compliance tracking"""
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    
    # Session status
    session_status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    
    # Compliance tracking
    feedback_submitted = db.Column(db.Boolean, default=False)
    feedback_submitted_at = db.Column(db.DateTime)
    attendance_marked = db.Column(db.Boolean, default=False)
    attendance_marked_at = db.Column(db.DateTime)
    recording_uploaded = db.Column(db.Boolean, default=False)
    recording_uploaded_at = db.Column(db.DateTime)
    materials_uploaded = db.Column(db.Boolean, default=False)
    materials_uploaded_at = db.Column(db.DateTime)
    
    # Overall compliance
    all_requirements_met = db.Column(db.Boolean, default=False)
    compliance_deadline = db.Column(db.DateTime)
    compliance_checked_at = db.Column(db.DateTime)
    
    # Late arrival tracking
    tutor_late_arrival = db.Column(db.Boolean, default=False)
    tutor_arrival_time = db.Column(db.DateTime)
    late_minutes = db.Column(db.Integer, default=0)
    late_penalty_applied = db.Column(db.Boolean, default=False)
    
    # Quality metrics
    session_rating = db.Column(db.Float)  # Derived from feedback
    technical_issues_reported = db.Column(db.Boolean, default=False)
    student_satisfaction = db.Column(db.Integer)  # 1-5 scale
    
    # Admin tracking
    reviewed_by_admin = db.Column(db.Boolean, default=False)
    admin_review_date = db.Column(db.DateTime)
    admin_reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_comments = db.Column(db.Text)
    
    # Flags and alerts
    flagged_for_review = db.Column(db.Boolean, default=False)
    flag_reasons = db.Column(db.Text)  # JSON list of reasons
    auto_flagged = db.Column(db.Boolean, default=False)
    
    # Additional session data
    session_notes = db.Column(db.Text)
    next_session_prep = db.Column(db.Text)
    homework_assigned = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_details = db.relationship('Class', foreign_keys=[class_id], backref='session_tracking')
    admin_reviewer = db.relationship('User', foreign_keys=[admin_reviewer_id])
    
    def get_flag_reasons(self):
        """Get flag reasons as list"""
        if self.flag_reasons:
            return json.loads(self.flag_reasons)
        return []
    
    def set_flag_reasons(self, reasons_list):
        """Set flag reasons from list"""
        self.flag_reasons = json.dumps(reasons_list)
    
    def calculate_compliance_score(self):
        """Calculate compliance percentage"""
        total_requirements = 4  # feedback, attendance, recording, materials
        met_requirements = sum([
            self.feedback_submitted,
            self.attendance_marked,
            self.recording_uploaded,
            self.materials_uploaded
        ])
        return round((met_requirements / total_requirements) * 100, 1)
    
    def is_overdue(self):
        """Check if session is overdue for compliance"""
        if self.compliance_deadline and datetime.utcnow() > self.compliance_deadline:
            return not self.all_requirements_met
        return False
    
    def update_compliance_status(self):
        """Update overall compliance status"""
        self.all_requirements_met = all([
            self.feedback_submitted,
            self.attendance_marked,
            self.recording_uploaded,
            self.materials_uploaded
        ])
        self.compliance_checked_at = datetime.utcnow()