from datetime import datetime, time
import json
from . import db

class TutorProfile(db.Model):
    """Enhanced tutor profile with availability and qualifications"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Professional Information
    employee_id = db.Column(db.String(20), unique=True)
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    specialization = db.Column(db.Text)  # JSON list of subjects
    languages = db.Column(db.Text)  # JSON list of languages
    
    # Teaching Preferences
    preferred_grades = db.Column(db.Text)  # JSON list of grades
    teaching_mode = db.Column(db.String(50))  # online, offline, both
    max_students_per_day = db.Column(db.Integer, default=8)
    preferred_duration = db.Column(db.Integer, default=60)  # minutes
    
    # Availability Schedule (JSON)
    weekly_schedule = db.Column(db.Text)  # JSON with day/time availability
    
    # Status and Approval
    application_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    availability_status = db.Column(db.String(20), default='available')  # available, busy, on_leave
    is_active_for_new_students = db.Column(db.Boolean, default=True)
    
    # Finance Information
    hourly_rate = db.Column(db.Float)
    payment_mode = db.Column(db.String(50))  # bank_transfer, upi, cash
    bank_account_number = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(15))
    upi_id = db.Column(db.String(100))
    
    # Performance Metrics
    total_classes_conducted = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    total_students_taught = db.Column(db.Integer, default=0)
    
    # Documents
    resume_path = db.Column(db.String(500))
    id_proof_path = db.Column(db.String(500))
    qualification_certificates = db.Column(db.Text)  # JSON list of file paths
    
    # Metadata
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    approved_date = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_availability_update = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='tutor_profile')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def get_specialization(self):
        """Get specialization subjects as list"""
        if self.specialization:
            return json.loads(self.specialization)
        return []
    
    def set_specialization(self, subjects_list):
        """Set specialization from list"""
        self.specialization = json.dumps(subjects_list)
    
    def get_languages(self):
        """Get languages as list"""
        if self.languages:
            return json.loads(self.languages)
        return []
    
    def set_languages(self, languages_list):
        """Set languages from list"""
        self.languages = json.dumps(languages_list)
    
    def get_preferred_grades(self):
        """Get preferred grades as list"""
        if self.preferred_grades:
            return json.loads(self.preferred_grades)
        return []
    
    def set_preferred_grades(self, grades_list):
        """Set preferred grades from list"""
        self.preferred_grades = json.dumps(grades_list)
    
    def get_weekly_schedule(self):
        """Get weekly schedule as dict"""
        if self.weekly_schedule:
            return json.loads(self.weekly_schedule)
        return {}
    
    def set_weekly_schedule(self, schedule_dict):
        """Set weekly schedule from dict"""
        self.weekly_schedule = json.dumps(schedule_dict)
        self.last_availability_update = datetime.utcnow()
    
    def is_available_at(self, day, time_slot):
        """Check if tutor is available at specific day/time"""
        schedule = self.get_weekly_schedule()
        day_schedule = schedule.get(day.lower(), [])
        return time_slot in day_schedule
    
    def get_available_slots_for_day(self, day):
        """Get all available time slots for a specific day"""
        schedule = self.get_weekly_schedule()
        return schedule.get(day.lower(), [])


class TutorAvailabilitySlot(db.Model):
    """Individual availability slots for tutors"""
    id = db.Column(db.Integer, primary_key=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profile.id'), nullable=False)
    
    day_of_week = db.Column(db.String(10), nullable=False)  # monday, tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    # Booking information
    is_booked = db.Column(db.Boolean, default=False)
    booked_by_enrollment = db.Column(db.Integer, db.ForeignKey('student_enrollment.id'))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tutor_profile = db.relationship('TutorProfile', backref='availability_slots')
    enrollment = db.relationship('StudentEnrollment', backref='booked_slots')