# models/feedback.py

from datetime import datetime
import json
from . import db

class FeedbackFormTemplate(db.Model):
    """Templates for class feedback forms"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Assignment criteria
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    subject = db.Column(db.String(100))  # Specific subject or None for department-wide
    class_type = db.Column(db.String(50))  # regular, demo, trial, etc.
    
    # Form configuration
    form_fields = db.Column(db.Text, nullable=False)  # JSON structure of fields
    is_active = db.Column(db.Boolean, default=True)
    is_mandatory = db.Column(db.Boolean, default=True)
    submission_deadline_hours = db.Column(db.Integer, default=3)  # Hours after class to submit
    
    # Display settings
    display_order = db.Column(db.Integer, default=0)
    allow_partial_submission = db.Column(db.Boolean, default=False)
    require_approval = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    submissions = db.relationship('ClassFeedback', backref='form_template')
    
    def get_fields(self):
        """Get form fields as Python object"""
        if self.form_fields:
            return json.loads(self.form_fields)
        return []
    
    def set_fields(self, fields_list):
        """Set form fields from Python object"""
        self.form_fields = json.dumps(fields_list)
    
    def increment_usage(self):
        """Track form usage"""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used = datetime.utcnow()


class ClassFeedback(db.Model):
    """Feedback responses submitted by tutors"""
    id = db.Column(db.Integer, primary_key=True)
    class_session_id = db.Column(db.Integer, db.ForeignKey('class_session.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    form_template_id = db.Column(db.Integer, db.ForeignKey('feedback_form_template.id'), nullable=False)
    
    # Response data
    feedback_data = db.Column(db.Text, nullable=False)  # JSON containing all form responses
    
    # Extracted key metrics (for quick reporting)
    overall_rating = db.Column(db.Integer)  # 1-5 scale
    student_engagement = db.Column(db.Integer)  # 1-5 scale
    class_completion = db.Column(db.Integer)  # Percentage
    technical_issues = db.Column(db.Boolean, default=False)
    needs_followup = db.Column(db.Boolean, default=False)
    
    # Submission tracking
    is_complete = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    submission_deadline = db.Column(db.DateTime)
    is_overdue = db.Column(db.Boolean, default=False)
    
    # Review and approval
    requires_review = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    review_status = db.Column(db.String(20))  # pending, approved, rejected, needs_revision
    review_comments = db.Column(db.Text)
    
    # Quality indicators
    auto_flagged = db.Column(db.Boolean, default=False)
    flag_reasons = db.Column(db.Text)  # JSON list of auto-flagging reasons
    
    # Relationships
    class_session = db.relationship('ClassSession', backref='feedback_submissions')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='submitted_feedback')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def get_feedback_data(self):
        """Get feedback data as Python object"""
        if self.feedback_data:
            return json.loads(self.feedback_data)
        return {}
    
    def set_feedback_data(self, data_dict):
        """Set feedback data from Python object"""
        self.feedback_data = json.dumps(data_dict)
    
    def get_flag_reasons(self):
        """Get flag reasons as list"""
        if self.flag_reasons:
            return json.loads(self.flag_reasons)
        return []
    
    def set_flag_reasons(self, reasons_list):
        """Set flag reasons from list"""
        self.flag_reasons = json.dumps(reasons_list)