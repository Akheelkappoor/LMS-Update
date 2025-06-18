# functions/helpers.py

from models import db, User, FeedbackFormTemplate, ClassSession, Student
import secrets
from datetime import datetime, timedelta

def assign_feedback_form(department_id, subject=None):
    """Auto-assign appropriate feedback form to class session"""
    # Try to find specific form for department and subject
    form = FeedbackFormTemplate.query.filter_by(
        department_id=department_id,
        subject=subject,
        is_active=True
    ).first()
    
    if not form:
        # Try department-specific form
        form = FeedbackFormTemplate.query.filter_by(
            department_id=department_id,
            subject=None,
            is_active=True
        ).first()
    
    if not form:
        # Try universal form
        form = FeedbackFormTemplate.query.filter_by(
            department_id=None,
            subject=None,
            is_active=True
        ).first()
    
    return form

def calculate_late_penalty(tutor_id, late_minutes):
    """Calculate penalty amount for late arrival"""
    # Get tutor's hourly rate
    tutor = User.query.get(tutor_id)
    hourly_rate = getattr(tutor, 'hourly_rate', 500)  # Default 500 if not set
    
    # Calculate penalty based on late minutes
    if late_minutes <= 10:
        penalty_rate = 0.1  # 10% of hourly rate
    elif late_minutes <= 20:
        penalty_rate = 0.25  # 25% of hourly rate
    else:
        penalty_rate = 0.5   # 50% of hourly rate
    
    return hourly_rate * penalty_rate

def calculate_compliance_rate():
    """Calculate overall system compliance rate"""
    total_sessions = ClassSession.query.filter_by(session_status='completed').count()
    if total_sessions == 0:
        return 100
    
    compliant_sessions = ClassSession.query.filter_by(
        session_status='completed',
        all_requirements_met=True
    ).count()
    
    return round((compliant_sessions / total_sessions) * 100, 1)

def generate_reset_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def save_reset_token(user, token):
    """Save reset token with expiration"""
    from flask import current_app as app
    # In production, store this in database
    # For now, we'll use session or a temporary dict
    if not hasattr(app, 'reset_tokens'):
        app.reset_tokens = {}
    
    app.reset_tokens[token] = {
        'user_id': user.id,
        'expires': datetime.utcnow() + timedelta(hours=1)
    }

def verify_reset_token(token):
    """Verify reset token and return user"""
    from flask import current_app as app
    if not hasattr(app, 'reset_tokens'):
        return None
    
    if token not in app.reset_tokens:
        return None
    
    token_data = app.reset_tokens[token]
    
    # Check expiration
    if datetime.utcnow() > token_data['expires']:
        del app.reset_tokens[token]
        return None
    
    return User.query.get(token_data['user_id'])

def generate_student_id():
    """Generate unique student ID"""
    from models import Student
    import random
    import datetime
    
    # Use current year + random number
    current_year = datetime.datetime.now().year
    year_suffix = str(current_year)[-2:]  # Last 2 digits of year
    
    while True:
        random_num = random.randint(10000, 99999)
        student_id = f"STU{year_suffix}{random_num}"
        
        # Check if this ID already exists
        existing = Student.query.filter_by(student_id=student_id).first()
        if not existing:
            return student_id

def generate_receipt_number():
    """Generate unique receipt number"""
    import random
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d")
    random_num = random.randint(1000, 9999)
    return f"RCP{timestamp}{random_num}"

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    today = datetime.now().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "₹0.00"
    return f"₹{amount:,.2f}"

def get_financial_year():
    """Get current financial year"""
    now = datetime.now()
    if now.month >= 4:  # April to March
        return f"{now.year}-{now.year + 1}"
    else:
        return f"{now.year - 1}-{now.year}"