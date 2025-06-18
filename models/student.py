# models/student.py - FIXED WITH PROPER RELATIONSHIPS

from datetime import datetime, date
import json
from . import db

class Student(db.Model):
    """Enhanced Student model with proper relationships"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    
    # Academic Information
    grade = db.Column(db.String(20))
    school = db.Column(db.String(200))
    board = db.Column(db.String(50))  # CBSE, ICSE, State, etc.
    
    # Address
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    country = db.Column(db.String(100), default='India')
    
    # Department and status
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    status = db.Column(db.String(20), default='active')  # active, inactive, graduated, dropped
    
    # Custom form data (JSON)
    custom_fields = db.Column(db.Text)  # JSON string for additional fields
    
    # Documents
    documents_uploaded = db.Column(db.Text)  # JSON list of document file paths
    profile_picture_path = db.Column(db.String(500))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships - FIXED
    department = db.relationship('Department', backref='students')
    parents = db.relationship('Parent', backref='student', cascade='all, delete-orphan')
    enrollments = db.relationship('StudentEnrollment', backref='student', cascade='all, delete-orphan')
    attendance_records = db.relationship('StudentAttendance', backref='student', cascade='all, delete-orphan')
    fees = db.relationship('StudentFee', backref='student', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_students')
    
    def get_custom_fields(self):
        """Get custom fields as dictionary"""
        if self.custom_fields:
            try:
                return json.loads(self.custom_fields)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_custom_fields(self, fields_dict):
        """Set custom fields from dictionary"""
        self.custom_fields = json.dumps(fields_dict) if fields_dict else None
    
    def get_documents(self):
        """Get uploaded documents as list"""
        if self.documents_uploaded:
            try:
                return json.loads(self.documents_uploaded)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_documents(self, documents_list):
        """Set documents from list"""
        self.documents_uploaded = json.dumps(documents_list) if documents_list else None
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def primary_parent(self):
        """Get primary parent contact"""
        return next((parent for parent in self.parents if parent.is_primary_contact), None)
    
    @property
    def active_enrollments(self):
        """Get active enrollments"""
        return [enrollment for enrollment in self.enrollments if enrollment.status == 'active']
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.full_name}>'


class Parent(db.Model):
    """Parent/Guardian model with proper relationships"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)  # father, mother, guardian, etc.
    
    # Contact preferences
    is_primary_contact = db.Column(db.Boolean, default=False)
    is_emergency_contact = db.Column(db.Boolean, default=False)
    
    # Additional Information
    occupation = db.Column(db.String(100))
    workplace = db.Column(db.String(200))
    work_phone = db.Column(db.String(20))
    
    # Address (can be different from student)
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Parent {self.full_name} ({self.relationship})>'