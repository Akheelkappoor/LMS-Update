# models/__init__.py - FIXED VERSION

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models in correct order to avoid circular imports
from .user import User
from .department import Department
from .permission import Permission
from .approval import UserApproval
from .email_template import EmailTemplate
from .form import FormTemplate, FormField
from .student import Student, Parent
from .tutor import TutorProfile, TutorAvailabilitySlot
from .enrollment import StudentEnrollment
from .classes import Class, StudentAttendance
from .finance import StudentFee, FeeInstallment
from .feedback import FeedbackFormTemplate, ClassFeedback
from .notifications import SystemNotification, TutorLateArrival
from .session import ClassSession

__all__ = [
    'db',
    'User', 
    'Department', 
    'Permission',
    'UserApproval', 
    'EmailTemplate', 
    'FormTemplate', 
    'FormField', 
    'Student', 
    'Parent',
    'TutorProfile',
    'TutorAvailabilitySlot',
    'StudentEnrollment', 
    'Class', 
    'StudentAttendance',
    'StudentFee', 
    'FeeInstallment',
    'FeedbackFormTemplate', 
    'ClassFeedback',
    'SystemNotification', 
    'TutorLateArrival',
    'ClassSession'
]