# functions/student_functions.py - FIXED VERSION

from models import db, Student, Parent, StudentEnrollment, StudentFee
from flask_login import current_user
from datetime import datetime, date
from .helpers import generate_student_id

def create_student(student_data):
    """Create a new student"""
    try:
        # Generate unique student ID if not provided
        student_id = student_data.get('student_id') or generate_student_id()
        
        # Handle date of birth conversion
        date_of_birth = None
        if student_data.get('date_of_birth') and student_data['date_of_birth'].strip():
            try:
                date_of_birth = datetime.strptime(student_data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                pass  # Leave as None if invalid date
        
        # Convert empty strings to None for optional fields
        def clean_field(value):
            return value.strip() if value and value.strip() else None
        
        # Convert department_id to int or None
        department_id = student_data.get('department_id')
        if department_id and department_id.strip() and department_id != '':
            try:
                department_id = int(department_id)
            except ValueError:
                department_id = None
        else:
            department_id = None
        
        student = Student(
            student_id=student_id,
            first_name=student_data['first_name'].strip(),
            last_name=student_data['last_name'].strip(),
            email=clean_field(student_data.get('email')),
            phone=clean_field(student_data.get('phone')),
            date_of_birth=date_of_birth,
            gender=clean_field(student_data.get('gender')),
            grade=clean_field(student_data.get('grade')),
            school=clean_field(student_data.get('school')),
            board=clean_field(student_data.get('board')),
            address_line1=clean_field(student_data.get('address_line1')),
            address_line2=clean_field(student_data.get('address_line2')),
            city=clean_field(student_data.get('city')),
            state=clean_field(student_data.get('state')),
            pincode=clean_field(student_data.get('pincode')),
            department_id=department_id,
            created_by=current_user.id
        )
        
        # Set custom fields (only non-empty ones)
        custom_fields = {}
        for key, value in student_data.items():
            if key.startswith('custom_') and value and value.strip():
                custom_fields[key] = value.strip()
        
        if custom_fields:
            student.set_custom_fields(custom_fields)
        
        db.session.add(student)
        db.session.flush()  # Get student ID
        
        # Create parent records if provided
        parents_created = []
        parent_count = 1
        while f'parent_{parent_count}_first_name' in student_data:
            parent_data = extract_parent_data(student_data, parent_count)
            if parent_data.get('first_name') and parent_data['first_name'].strip():
                parent = create_parent(student.id, parent_data)
                if parent:
                    parents_created.append(parent)
            parent_count += 1
        
        db.session.commit()
        return student, parents_created
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating student: {str(e)}")  # For debugging
        return None, f"Student creation failed: {str(e)}"

def extract_parent_data(form_data, parent_number):
    """Extract parent data from form submission"""
    prefix = f'parent_{parent_number}_'
    parent_data = {}
    
    for key, value in form_data.items():
        if key.startswith(prefix):
            field_name = key.replace(prefix, '')
            if value and value.strip():  # Only include non-empty values
                parent_data[field_name] = value.strip()
    
    return parent_data

def create_parent(student_id, parent_data):
    """Create a parent record"""
    try:
        def clean_field(value):
            return value.strip() if value and value.strip() else None
        
        parent = Parent(
            student_id=student_id,
            first_name=parent_data['first_name'].strip(),
            last_name=parent_data.get('last_name', '').strip() or 'Parent',
            email=clean_field(parent_data.get('email')),
            phone=clean_field(parent_data.get('phone')) or 'Not provided',
            relationship=clean_field(parent_data.get('relationship')) or 'guardian',
            is_primary_contact=bool(parent_data.get('is_primary')),
            is_emergency_contact=bool(parent_data.get('is_emergency')),
            occupation=clean_field(parent_data.get('occupation')),
            workplace=clean_field(parent_data.get('workplace')),
            work_phone=clean_field(parent_data.get('work_phone')),
            address_line1=clean_field(parent_data.get('address_line1')),
            address_line2=clean_field(parent_data.get('address_line2')),
            city=clean_field(parent_data.get('city')),
            state=clean_field(parent_data.get('state')),
            pincode=clean_field(parent_data.get('pincode'))
        )
        
        db.session.add(parent)
        return parent
        
    except Exception as e:
        print(f"Error creating parent: {str(e)}")
        return None

# Rest of your functions remain the same...
def update_student(student_id, student_data):
    """Update existing student"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        # Handle date conversion
        if 'date_of_birth' in student_data:
            if student_data['date_of_birth'] and student_data['date_of_birth'].strip():
                try:
                    student.date_of_birth = datetime.strptime(student_data['date_of_birth'], '%Y-%m-%d').date()
                except ValueError:
                    pass  # Keep existing date if invalid
            else:
                student.date_of_birth = None
        
        # Helper function
        def clean_field(value):
            return value.strip() if value and value.strip() else None
        
        # Update basic fields
        for field in ['first_name', 'last_name', 'email', 'phone', 
                     'gender', 'grade', 'school', 'board', 'address_line1', 'address_line2',
                     'city', 'state', 'pincode', 'status']:
            if field in student_data:
                if field in ['first_name', 'last_name']:
                    # Required fields
                    setattr(student, field, student_data[field].strip())
                else:
                    # Optional fields
                    setattr(student, field, clean_field(student_data[field]))
        
        # Handle department_id
        if 'department_id' in student_data:
            department_id = student_data['department_id']
            if department_id and department_id.strip() and department_id != '':
                try:
                    student.department_id = int(department_id)
                except ValueError:
                    student.department_id = None
            else:
                student.department_id = None
        
        # Update custom fields
        custom_fields = {}
        for key, value in student_data.items():
            if key.startswith('custom_') and value and value.strip():
                custom_fields[key] = value.strip()
        
        if custom_fields:
            student.set_custom_fields(custom_fields)
        
        student.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Student updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Student update failed: {str(e)}"

def delete_student(student_id):
    """Soft delete student (mark as inactive)"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        student.status = 'inactive'
        student.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Student deactivated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Student deletion failed: {str(e)}"

def enroll_student(enrollment_data):
    """Enroll student in a subject"""
    try:
        enrollment = StudentEnrollment(
            student_id=enrollment_data['student_id'],
            tutor_id=enrollment_data['tutor_id'],
            subject=enrollment_data['subject'],
            class_type=enrollment_data.get('class_type', 'regular'),
            start_date=enrollment_data['start_date'],
            end_date=enrollment_data.get('end_date'),
            sessions_per_week=enrollment_data.get('sessions_per_week', 1),
            session_duration=enrollment_data.get('session_duration', 60),
            fee_per_session=enrollment_data.get('fee_per_session', 0.0),
            total_fee=enrollment_data.get('total_fee', 0.0),
            notes=enrollment_data.get('notes'),
            created_by=current_user.id
        )
        
        # Set schedule data
        if 'schedule' in enrollment_data:
            enrollment.set_schedule(enrollment_data['schedule'])
        
        db.session.add(enrollment)
        db.session.commit()
        return enrollment, "Student enrolled successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Enrollment failed: {str(e)}"

def update_enrollment(enrollment_id, enrollment_data):
    """Update student enrollment"""
    try:
        enrollment = StudentEnrollment.query.get(enrollment_id)
        if not enrollment:
            return False, "Enrollment not found."
        
        # Update fields
        for field in ['tutor_id', 'subject', 'class_type', 'start_date', 'end_date',
                     'sessions_per_week', 'session_duration', 'fee_per_session', 
                     'total_fee', 'status', 'notes']:
            if field in enrollment_data and enrollment_data[field] is not None:
                setattr(enrollment, field, enrollment_data[field])
        
        # Update schedule
        if 'schedule' in enrollment_data:
            enrollment.set_schedule(enrollment_data['schedule'])
        
        enrollment.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Enrollment updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Enrollment update failed: {str(e)}"

def get_students_by_tutor(tutor_id):
    """Get all students assigned to a tutor"""
    enrollments = StudentEnrollment.query.filter_by(
        tutor_id=tutor_id, 
        status='active'
    ).all()
    return [enrollment.student for enrollment in enrollments]

def get_students_by_department(department_id):
    """Get all students in a department"""
    return Student.query.filter_by(
        department_id=department_id, 
        status='active'
    ).all()

def search_students(search_term):
    """Search students by name, email, or student ID"""
    return Student.query.filter(
        db.or_(
            Student.first_name.contains(search_term),
            Student.last_name.contains(search_term),
            Student.email.contains(search_term),
            Student.student_id.contains(search_term)
        )
    ).filter_by(status='active').all()

def get_student_enrollments(student_id):
    """Get all enrollments for a student"""
    return StudentEnrollment.query.filter_by(student_id=student_id).all()

def get_student_fees(student_id):
    """Get all fees for a student"""
    return StudentFee.query.filter_by(student_id=student_id).all()

def get_student_parents(student_id):
    """Get all parents for a student"""
    return Parent.query.filter_by(student_id=student_id).all()

def update_parent(parent_id, parent_data):
    """Update parent information"""
    try:
        parent = Parent.query.get(parent_id)
        if not parent:
            return False, "Parent not found."
        
        def clean_field(value):
            return value.strip() if value and value.strip() else None
        
        # Update fields
        for field in ['first_name', 'last_name', 'email', 'phone', 'relationship',
                     'is_primary_contact', 'is_emergency_contact', 'occupation',
                     'workplace', 'work_phone', 'address_line1', 'address_line2',
                     'city', 'state', 'pincode']:
            if field in parent_data:
                if field in ['first_name', 'last_name', 'phone']:
                    # Required fields
                    setattr(parent, field, parent_data[field].strip() if parent_data[field] else '')
                elif field in ['is_primary_contact', 'is_emergency_contact']:
                    # Boolean fields
                    setattr(parent, field, bool(parent_data[field]))
                else:
                    # Optional fields
                    setattr(parent, field, clean_field(parent_data[field]))
        
        db.session.commit()
        return True, "Parent updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Parent update failed: {str(e)}"

def delete_parent(parent_id):
    """Delete parent record"""
    try:
        parent = Parent.query.get(parent_id)
        if not parent:
            return False, "Parent not found."
        
        db.session.delete(parent)
        db.session.commit()
        return True, "Parent deleted successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Parent deletion failed: {str(e)}"

def bulk_update_students(student_ids, update_data):
    """Bulk update multiple students"""
    try:
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        
        for student in students:
            for field, value in update_data.items():
                if hasattr(student, field):
                    setattr(student, field, value)
            student.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True, f"Updated {len(students)} students successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Bulk update failed: {str(e)}"

def get_student_statistics():
    """Get student statistics for dashboard"""
    stats = {}
    stats['total_students'] = Student.query.filter_by(status='active').count()
    stats['total_enrollments'] = StudentEnrollment.query.filter_by(status='active').count()
    stats['students_by_grade'] = db.session.query(
        Student.grade, 
        db.func.count(Student.id)
    ).filter_by(status='active').group_by(Student.grade).all()
    
    return stats

def promote_students(student_ids, new_grade):
    """Promote students to next grade"""
    try:
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        
        for student in students:
            student.grade = new_grade
            student.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True, f"Promoted {len(students)} students to {new_grade}."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Promotion failed: {str(e)}"