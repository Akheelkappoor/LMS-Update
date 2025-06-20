from datetime import datetime
from . import db

class StudentEnrollment(db.Model):
    """Student enrollment in subjects with tutors"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Enrollment details
    enrollment_date = db.Column(db.Date, nullable=False)
    hourly_rate = db.Column(db.Float, default=0)
    classes_per_week = db.Column(db.Integer, default=2)
    preferred_schedule = db.Column(db.String(50))  # morning, afternoon, evening
    
    # Progress tracking
    total_sessions = db.Column(db.Integer, default=0)
    completed_sessions = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Float, default=0)
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, paused, completed, cancelled
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='enrollments')
    tutor = db.relationship('User', backref='student_enrollments')
    classes = db.relationship('Class', backref='enrollment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudentEnrollment {self.student.first_name} - {self.subject}>'
    
    def get_completion_percentage(self):
        """Calculate completion percentage"""
        if self.total_sessions == 0:
            return 0
        return (self.completed_sessions / self.total_sessions) * 100
    
    def get_weekly_cost(self):
        """Calculate weekly cost"""
        return self.hourly_rate * self.classes_per_week
    
    def get_monthly_cost(self):
        """Calculate monthly cost (4 weeks)"""
        return self.get_weekly_cost() * 4