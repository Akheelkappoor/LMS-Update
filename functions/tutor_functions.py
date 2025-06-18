from models import TutorProfile, db
from datetime import datetime

def generate_employee_id():
    """Generate unique employee ID for tutor"""
    import secrets
    import string
    
    while True:
        # Format: TUT + year + 4 random digits
        year = datetime.now().year
        random_part = ''.join(secrets.choice(string.digits) for _ in range(4))
        employee_id = f"TUT{year}{random_part}"
        
        # Check if already exists
        existing = TutorProfile.query.filter_by(employee_id=employee_id).first()
        if not existing:
            return employee_id

def find_available_tutors(search_criteria):
    """Find tutors based on search criteria"""
    try:
        from models import TutorProfile, User
        
        query = TutorProfile.query.join(User).filter(
            TutorProfile.application_status == 'approved',
            TutorProfile.availability_status == 'available',
            TutorProfile.is_active_for_new_students == True
        )
        
        # Apply search criteria
        if 'subject' in search_criteria:
            query = query.filter(TutorProfile.specialization.contains(search_criteria['subject']))
        
        if 'grade' in search_criteria:
            query = query.filter(TutorProfile.preferred_grades.contains(search_criteria['grade']))
        
        if 'department_id' in search_criteria:
            query = query.filter(User.department_id == search_criteria['department_id'])
        
        if 'max_rate' in search_criteria:
            query = query.filter(TutorProfile.hourly_rate <= search_criteria['max_rate'])
        
        if 'min_experience' in search_criteria:
            query = query.filter(TutorProfile.experience_years >= search_criteria['min_experience'])
        
        tutors = query.all()
        
        # Check availability for specific day/time if provided
        if 'day' in search_criteria and 'time_slot' in search_criteria:
            available_tutors = []
            for tutor in tutors:
                if tutor.is_available_at(search_criteria['day'], search_criteria['time_slot']):
                    available_tutors.append(tutor)
            tutors = available_tutors
        
        return tutors, "Search completed successfully."
        
    except Exception as e:
        return [], f"Search failed: {str(e)}"

def update_tutor_availability(tutor_profile_id, availability_data):
    """Update tutor availability schedule"""
    try:
        tutor_profile = TutorProfile.query.get(tutor_profile_id)
        if not tutor_profile:
            return False, "Tutor profile not found."
        
        tutor_profile.set_weekly_schedule(availability_data['schedule'])
        tutor_profile.availability_status = availability_data.get('status', 'available')
        tutor_profile.is_active_for_new_students = availability_data.get('accepting_new_students', True)
        
        db.session.commit()
        return True, "Availability updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Update failed: {str(e)}"