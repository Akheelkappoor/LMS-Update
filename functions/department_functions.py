# functions/department_functions.py

from models import db, Department, User
from flask_login import current_user
from datetime import datetime

def create_department(department_data):
    """Create a new department"""
    try:
        # Check if department name or code already exists
        if Department.query.filter_by(name=department_data['name']).first():
            return None, "Department name already exists."
        
        if Department.query.filter_by(code=department_data['code']).first():
            return None, "Department code already exists."
        
        department = Department(
            name=department_data['name'],
            code=department_data['code'].upper(),
            description=department_data.get('description'),
            user_form_id=department_data.get('user_form_id'),
            tutor_form_id=department_data.get('tutor_form_id'),
            created_by=current_user.id
        )
        
        db.session.add(department)
        db.session.commit()
        return department, "Department created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Department creation failed: {str(e)}"

def update_department(department_id, department_data):
    """Update existing department"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        # Check for name/code conflicts with other departments
        if 'name' in department_data:
            existing_dept = Department.query.filter(
                Department.name == department_data['name'],
                Department.id != department_id
            ).first()
            if existing_dept:
                return False, "Department name already exists."
        
        if 'code' in department_data:
            existing_dept = Department.query.filter(
                Department.code == department_data['code'].upper(),
                Department.id != department_id
            ).first()
            if existing_dept:
                return False, "Department code already exists."
        
        # Update fields
        for field in ['name', 'code', 'description', 'user_form_id', 'tutor_form_id', 'is_active']:
            if field in department_data and department_data[field] is not None:
                if field == 'code':
                    setattr(department, field, department_data[field].upper())
                else:
                    setattr(department, field, department_data[field])
        
        db.session.commit()
        return True, "Department updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Department update failed: {str(e)}"

def delete_department(department_id):
    """Delete department if no users are assigned"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        # Check if department has any users
        user_count = User.query.filter_by(department_id=department_id).count()
        if user_count > 0:
            return False, f"Cannot delete department. {user_count} users are assigned to this department."
        
        db.session.delete(department)
        db.session.commit()
        return True, "Department deleted successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Department deletion failed: {str(e)}"

def deactivate_department(department_id):
    """Deactivate department (soft delete)"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        department.is_active = False
        db.session.commit()
        return True, "Department deactivated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Department deactivation failed: {str(e)}"

def reactivate_department(department_id):
    """Reactivate department"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        department.is_active = True
        db.session.commit()
        return True, "Department reactivated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Department reactivation failed: {str(e)}"

def assign_department_coordinator(department_id, user_id):
    """Assign a coordinator to a department"""
    try:
        department = Department.query.get(department_id)
        user = User.query.get(user_id)
        
        if not department:
            return False, "Department not found."
        
        if not user:
            return False, "User not found."
        
        if user.role != 'coordinator':
            return False, "User must be a coordinator."
        
        # Update user's department
        user.department_id = department_id
        db.session.commit()
        return True, f"Coordinator {user.full_name} assigned to {department.name}."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Coordinator assignment failed: {str(e)}"

def transfer_users_to_department(user_ids, new_department_id):
    """Transfer multiple users to a new department"""
    try:
        department = Department.query.get(new_department_id)
        if not department:
            return False, "Target department not found."
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        for user in users:
            user.department_id = new_department_id
        
        db.session.commit()
        return True, f"Transferred {len(users)} users to {department.name}."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User transfer failed: {str(e)}"

def get_department_users(department_id):
    """Get all users in a department"""
    return User.query.filter_by(department_id=department_id, is_active=True).all()

def get_department_statistics(department_id):
    """Get statistics for a department"""
    from models import Student, StudentEnrollment
    
    stats = {}
    stats['total_users'] = User.query.filter_by(department_id=department_id, is_active=True).count()
    stats['total_tutors'] = User.query.filter_by(department_id=department_id, role='tutor', is_active=True).count()
    stats['total_coordinators'] = User.query.filter_by(department_id=department_id, role='coordinator', is_active=True).count()
    stats['total_students'] = Student.query.filter_by(department_id=department_id, status='active').count()
    stats['active_enrollments'] = StudentEnrollment.query.join(Student).filter(
        Student.department_id == department_id,
        StudentEnrollment.status == 'active'
    ).count()
    
    return stats

def search_departments(search_term):
    """Search departments by name or code"""
    return Department.query.filter(
        db.or_(
            Department.name.contains(search_term),
            Department.code.contains(search_term)
        )
    ).filter_by(is_active=True).all()

def get_departments_for_user(user):
    """Get departments accessible to user based on role"""
    if user.role in ['superadmin', 'admin']:
        return Department.query.filter_by(is_active=True).all()
    elif user.role == 'coordinator':
        return Department.query.filter_by(id=user.department_id, is_active=True).all()
    else:
        return []

def assign_form_to_department(department_id, form_id, form_type):
    """Assign a form template to a department"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        from models import FormTemplate
        form = FormTemplate.query.get(form_id)
        if not form:
            return False, "Form template not found."
        
        if form_type == 'user':
            department.user_form_id = form_id
        elif form_type == 'tutor':
            department.tutor_form_id = form_id
        else:
            return False, "Invalid form type. Must be 'user' or 'tutor'."
        
        db.session.commit()
        return True, f"Form assigned to department successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Form assignment failed: {str(e)}"

def remove_form_from_department(department_id, form_type):
    """Remove form assignment from department"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        if form_type == 'user':
            department.user_form_id = None
        elif form_type == 'tutor':
            department.tutor_form_id = None
        else:
            return False, "Invalid form type. Must be 'user' or 'tutor'."
        
        db.session.commit()
        return True, f"Form removed from department successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Form removal failed: {str(e)}"

def get_department_hierarchy():
    """Get department hierarchy for display"""
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    hierarchy = []
    for dept in departments:
        dept_data = {
            'id': dept.id,
            'name': dept.name,
            'code': dept.code,
            'description': dept.description,
            'user_count': len(dept.members),
            'coordinator': None,
            'forms': {
                'user_form': dept.user_form_id,
                'tutor_form': dept.tutor_form_id
            }
        }
        
        # Find coordinator
        coordinator = User.query.filter_by(
            department_id=dept.id, 
            role='coordinator', 
            is_active=True
        ).first()
        
        if coordinator:
            dept_data['coordinator'] = {
                'id': coordinator.id,
                'name': coordinator.full_name,
                'email': coordinator.email
            }
        
        hierarchy.append(dept_data)
    
    return hierarchy

def validate_department_code(code, exclude_id=None):
    """Validate department code format and uniqueness"""
    # Check format (e.g., must be uppercase, 2-10 characters)
    if not code or len(code) < 2 or len(code) > 10:
        return False, "Department code must be 2-10 characters long."
    
    if not code.replace('_', '').replace('-', '').isalnum():
        return False, "Department code can only contain letters, numbers, hyphens, and underscores."
    
    # Check uniqueness
    query = Department.query.filter_by(code=code.upper())
    if exclude_id:
        query = query.filter(Department.id != exclude_id)
    
    if query.first():
        return False, "Department code already exists."
    
    return True, "Valid department code."

def bulk_update_departments(department_ids, update_data):
    """Bulk update multiple departments"""
    try:
        departments = Department.query.filter(Department.id.in_(department_ids)).all()
        
        for dept in departments:
            for field, value in update_data.items():
                if hasattr(dept, field) and field not in ['id', 'code', 'name']:  # Prevent updating unique fields
                    setattr(dept, field, value)
        
        db.session.commit()
        return True, f"Updated {len(departments)} departments successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Bulk update failed: {str(e)}"
    

def delete_department(department_id):
    """Delete department (soft delete)"""
    try:
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        # Check if department has users
        user_count = User.query.filter_by(department_id=department_id, is_active=True).count()
        if user_count > 0:
            return False, f"Cannot delete department with {user_count} active users. Please transfer users first."
        
        # Soft delete
        department.is_active = False
        db.session.commit()
        return True, "Department deleted successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Department deletion failed: {str(e)}"