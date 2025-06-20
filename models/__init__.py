# models/__init__.py - FIXED VERSION

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models in correct order to avoid circular imports
from .user import *
from .department import *
from .permission import *
from .approval import *
from .email_template import *
from .form import *
from .student import *
from .tutor import *
from .enrollment import *
from .classes import *
from .finance import *
from .feedback import *
from .notifications import *
from .session import *
from .tutor import *

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