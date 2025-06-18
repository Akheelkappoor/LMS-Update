# models/user.py - COMPLETE FIXED VERSION

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json
from . import db

class User(UserMixin, db.Model):
    """Enhanced User model with permissions and custom fields"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    profile_picture = db.Column(db.String(500))
    date_of_birth = db.Column(db.Date)
    
    # Role and Department
    role = db.Column(db.String(50), nullable=False, default='tutor')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    
    # Permissions and Access
    permissions = db.Column(db.Text)  # JSON string of permissions
    custom_fields = db.Column(db.Text)  # JSON string for dynamic fields
    
    # Status and Tracking
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    
    # Emergency Contact
    emergency_contact = db.Column(db.Text)  # JSON for emergency contact info
    
    # Performance metrics (for tutors)
    feedback_rating = db.Column(db.Float, default=0.0)
    total_classes_taught = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    department = db.relationship('Department', backref='members')
    creator = db.relationship('User', foreign_keys=[created_by], remote_side=[id])
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def set_permissions(self, permissions_list):
        """Set user permissions"""
        if permissions_list:
            self.permissions = json.dumps(permissions_list)
        else:
            self.permissions = None
    
    def get_permissions(self):
        """Get user permissions as list"""
        if self.permissions:
            try:
                return json.loads(self.permissions)
            except (json.JSONDecodeError, TypeError):
                return []
        
        # Return default role permissions if no custom permissions
        return self.get_default_role_permissions()
    
    def get_default_role_permissions(self):
        """Get default permissions for user's role"""
        role_permissions = {
            'tutor': [
                'view_own_classes',
                'mark_attendance', 
                'upload_recordings',
                'submit_feedback',
                'view_own_schedule',
                'view_own_students',
                'view_own_payroll',
                'update_profile'
            ],
            'coordinator': [
                'view_department_users',
                'create_students',
                'manage_enrollments',
                'view_department_classes',
                'generate_department_reports',
                'approve_requests',
                'manage_department_schedule',
                'view_department_analytics'
            ],
            'finance_coordinator': [
                'manage_all_payroll',
                'process_payments',
                'view_financial_reports',
                'manage_fees',
                'approve_penalties',
                'view_all_departments'
            ],
            'admin': [
                'manage_all_users',
                'manage_departments',
                'system_settings',
                'view_all_reports',
                'approve_users',
                'manage_forms'
            ],
            'superadmin': ['*']  # All permissions
        }
        
        return role_permissions.get(self.role, [])
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        try:
            # Superadmin has all permissions
            if self.role == 'superadmin':
                return True
            
            user_permissions = self.get_permissions()
            
            # Check for wildcard permission
            if '*' in user_permissions:
                return True
                
            # Check specific permission
            return permission in user_permissions
            
        except:
            return False
    
    def set_custom_fields(self, fields_dict):
        """Set custom fields from dictionary"""
        self.custom_fields = json.dumps(fields_dict) if fields_dict else None
    
    def get_custom_fields(self):
        """Get custom fields as dictionary"""
        if self.custom_fields:
            try:
                return json.loads(self.custom_fields)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_emergency_contact(self, contact_dict):
        """Set emergency contact info"""
        self.emergency_contact = json.dumps(contact_dict) if contact_dict else None
    
    def get_emergency_contact(self):
        """Get emergency contact info"""
        if self.emergency_contact:
            try:
                return json.loads(self.emergency_contact)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def update_feedback_rating(self, new_rating):
        """Update feedback rating with running average"""
        if self.feedback_rating == 0:
            self.feedback_rating = new_rating
        else:
            # Simple average for now - can be enhanced
            self.feedback_rating = (self.feedback_rating + new_rating) / 2
    
    def is_coordinator_of_department(self, department_id):
        """Check if user is coordinator of specific department"""
        return self.role == 'coordinator' and self.department_id == department_id
    
    def can_access_department(self, department_id):
        """Check if user can access specific department"""
        if self.role in ['superadmin', 'admin']:
            return True
        elif self.role == 'finance_coordinator':
            return True  # Finance coordinators can access all departments
        elif self.role == 'coordinator':
            return self.department_id == department_id
        else:
            return self.department_id == department_id
    
    @property
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.role in ['superadmin', 'admin']
    
    @property
    def is_coordinator(self):
        """Check if user is a coordinator"""
        return self.role in ['coordinator', 'finance_coordinator']
    
    def __repr__(self):
        return f'<User {self.username}>'