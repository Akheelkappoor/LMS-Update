# models/department.py - COMPLETE FIXED VERSION

from datetime import datetime
import json
from . import db

class Department(db.Model):
    """Department model with form assignments and settings"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Form assignments
    user_form_id = db.Column(db.Integer, db.ForeignKey('form_template.id'))
    tutor_form_id = db.Column(db.Integer, db.ForeignKey('form_template.id'))
    
    # Department settings (JSON)
    settings = db.Column(db.Text)  # JSON for department-specific settings
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    user_form = db.relationship('FormTemplate', foreign_keys=[user_form_id])
    tutor_form = db.relationship('FormTemplate', foreign_keys=[tutor_form_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def get_settings(self):
        """Get department settings as dictionary"""
        if self.settings:
            try:
                return json.loads(self.settings)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_settings(self, settings_dict):
        """Set department settings from dictionary"""
        self.settings = json.dumps(settings_dict) if settings_dict else None
    
    def get_coordinator(self):
        """Get department coordinator"""
        from .user import User
        return User.query.filter_by(
            department_id=self.id,
            role='coordinator',
            is_active=True
        ).first()
    
    def get_tutors(self):
        """Get all tutors in this department"""
        from .user import User
        return User.query.filter_by(
            department_id=self.id,
            role='tutor',
            is_active=True
        ).all()
    
    def get_students(self):
        """Get all students in this department"""
        from .student import Student
        return Student.query.filter_by(
            department_id=self.id,
            status='active'
        ).all()
    
    @property
    def member_count(self):
        """Get total members count"""
        from .user import User
        return User.query.filter_by(department_id=self.id, is_active=True).count()
    
    @property
    def tutor_count(self):
        """Get tutors count"""
        from .user import User
        return User.query.filter_by(
            department_id=self.id,
            role='tutor',
            is_active=True
        ).count()
    
    @property
    def student_count(self):
        """Get students count"""
        from .student import Student
        return Student.query.filter_by(
            department_id=self.id,
            status='active'
        ).count()
    
    def __repr__(self):
        return f'<Department {self.name}>'
    
def get_student_form(self):
    """Get student registration form for this department"""
    from .form_template import FormTemplate
    if self.user_form_id:  # Using user_form_id for student forms
        return FormTemplate.query.get(self.user_form_id)
    return None