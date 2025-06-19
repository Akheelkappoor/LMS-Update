# functions/missing_functions.py - All Missing Function Implementations

from models import db, User, Student, Department, Class, StudentEnrollment, StudentFee, FormTemplate
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy import func, or_
import secrets, string

# ===================================
# USER MANAGEMENT FUNCTIONS
# ===================================

def get_user_statistics():
    """Get user statistics for dashboard"""
    try:
        total_users = User.query.filter_by(is_active=True).count()
        total_tutors = User.query.filter_by(role='tutor', is_active=True).count()
        total_coordinators = User.query.filter_by(role='coordinator', is_active=True).count()
        pending_approvals = User.query.filter_by(is_approved=False, is_active=True).count()
        
        return {
            'total_users': total_users,
            'total_tutors': total_tutors,
            'total_coordinators': total_coordinators,
            'pending_approvals': pending_approvals
        }
    except Exception as e:
        print(f"Error getting user statistics: {str(e)}")
        return {
            'total_users': 0,
            'total_tutors': 0,
            'total_coordinators': 0,
            'pending_approvals': 0
        }

def create_user(user_data):
    """Create new user with password generation"""
    try:
        # Check if user already exists
        if User.query.filter_by(email=user_data['email']).first():
            return None, "User with this email already exists."
        
        if User.query.filter_by(username=user_data['username']).first():
            return None, "Username already taken."
        
        # Generate random password
        password = secrets.token_urlsafe(8)
        
        # Create new user
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data.get('full_name'),
            phone=user_data.get('phone'),
            role=user_data.get('role', 'tutor'),
            department_id=user_data.get('department_id'),
            is_active=True,
            is_approved=True  # Auto-approved when created by admin
        )
        
        user.set_password(password)
        
        # Set permissions if provided
        if 'permissions' in user_data and user_data['permissions']:
            user.set_permissions(user_data['permissions'])
        
        db.session.add(user)
        db.session.commit()
        
        return user, password  # Return password for admin to share
        
    except Exception as e:
        db.session.rollback()
        return None, f"User creation failed: {str(e)}"

def update_user(user_id, user_data):
    """Update existing user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        # Update basic fields
        if 'full_name' in user_data:
            user.full_name = user_data['full_name']
        if 'email' in user_data:
            # Check email uniqueness
            existing = User.query.filter(User.email == user_data['email'], User.id != user_id).first()
            if existing:
                return False, "Email already exists."
            user.email = user_data['email']
        if 'phone' in user_data:
            user.phone = user_data['phone']
        if 'role' in user_data:
            user.role = user_data['role']
        if 'department_id' in user_data:
            user.department_id = user_data['department_id']
        if 'is_active' in user_data:
            user.is_active = bool(user_data['is_active'])
        
        # Update permissions if provided
        if 'permissions' in user_data:
            user.set_permissions(user_data['permissions'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, f"User {user.full_name} updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User update failed: {str(e)}"

def delete_user(user_id):
    """Soft delete user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        # Soft delete - deactivate user
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True, f"User {user.full_name} deactivated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User deletion failed: {str(e)}"

def get_user_dashboard_data(user):
    """Get dashboard data based on user role"""
    try:
        if user.role == 'superadmin':
            return get_superadmin_dashboard_data()
        elif user.role == 'admin':
            return get_admin_dashboard_data()
        elif user.role == 'coordinator':
            return get_coordinator_dashboard_data(user)
        elif user.role == 'tutor':
            return get_tutor_dashboard_data(user)
        elif user.role == 'finance_coordinator':
            return get_finance_dashboard_data(user)
        else:
            return get_default_dashboard_data()
    except Exception as e:
        print(f"Dashboard data error: {str(e)}")
        return get_default_dashboard_data()

def get_superadmin_dashboard_data():
    """Get superadmin dashboard data"""
    try:
        total_users = User.query.filter_by(is_active=True).count()
        total_departments = Department.query.filter_by(is_active=True).count()
        total_students = Student.query.filter_by(status='active').count()
        total_classes = Class.query.count()
        pending_approvals = User.query.filter_by(is_approved=False, is_active=True).count()
        
        # Get recent registrations
        recent_users = User.query.filter_by(is_active=True).order_by(User.created_at.desc()).limit(5).all()
        
        return {
            'total_users': total_users,
            'total_departments': total_departments,
            'total_students': total_students,
            'total_classes': total_classes,
            'pending_approvals': pending_approvals,
            'recent_users': recent_users,
            'system_health': 'Excellent'
        }
    except Exception as e:
        return {'error': str(e)}

def get_admin_dashboard_data():
    """Get admin dashboard data"""
    try:
        total_users = User.query.filter_by(is_active=True).count()
        total_tutors = User.query.filter_by(role='tutor', is_active=True).count()
        total_students = Student.query.filter_by(status='active').count()
        pending_approvals = User.query.filter_by(is_approved=False, is_active=True).count()
        
        return {
            'total_users': total_users,
            'total_tutors': total_tutors,
            'total_students': total_students,
            'pending_approvals': pending_approvals,
            'recent_activity': get_recent_activity()
        }
    except Exception as e:
        return {'error': str(e)}

def get_coordinator_dashboard_data(user):
    """Get coordinator dashboard data"""
    try:
        dept_users = User.query.filter_by(department_id=user.department_id, is_active=True).count()
        dept_tutors = User.query.filter_by(department_id=user.department_id, role='tutor', is_active=True).count()
        dept_students = Student.query.filter_by(department_id=user.department_id, status='active').count()
        
        # Get today's classes
        today = datetime.now().date()
        today_classes = Class.query.join(StudentEnrollment).join(Student).filter(
            Student.department_id == user.department_id,
            Class.class_date == today
        ).count()
        
        return {
            'department_users': dept_users,
            'department_tutors': dept_tutors,
            'department_students': dept_students,
            'today_classes': today_classes,
            'department_name': user.department.name if user.department else 'No Department'
        }
    except Exception as e:
        return {'error': str(e)}

def get_tutor_dashboard_data(user):
    """Get tutor dashboard data"""
    try:
        today = datetime.now().date()
        
        # Get tutor's classes today
        today_classes = Class.query.filter_by(
            tutor_id=user.id,
            class_date=today
        ).count()
        
        # Get this week's classes
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_classes = Class.query.filter(
            Class.tutor_id == user.id,
            Class.class_date >= week_start,
            Class.class_date <= week_end
        ).count()
        
        # Get total students
        total_students = StudentEnrollment.query.filter_by(
            tutor_id=user.id,
            status='active'
        ).count()
        
        # Get completed classes this month
        month_start = today.replace(day=1)
        completed_classes = Class.query.filter(
            Class.tutor_id == user.id,
            Class.class_date >= month_start,
            Class.status == 'completed'
        ).count()
        
        return {
            'classes_today': today_classes,
            'classes_this_week': week_classes,
            'total_students': total_students,
            'completed_classes': completed_classes,
            'performance_rating': 4.5  # Placeholder
        }
    except Exception as e:
        return {'error': str(e)}

def get_finance_dashboard_data(user):
    """Get finance coordinator dashboard data"""
    try:
        pending_fees = StudentFee.query.filter_by(payment_status='pending').count()
        total_revenue = StudentFee.query.filter_by(payment_status='paid').with_entities(func.sum(StudentFee.amount)).scalar() or 0
        overdue_fees = StudentFee.query.filter(
            StudentFee.payment_status == 'pending',
            StudentFee.due_date < datetime.now().date()
        ).count()
        
        return {
            'pending_fees': pending_fees,
            'total_revenue': float(total_revenue),
            'overdue_fees': overdue_fees,
            'collection_rate': 85.5  # Placeholder
        }
    except Exception as e:
        return {'error': str(e)}

def get_default_dashboard_data():
    """Get default dashboard data"""
    return {
        'message': 'Welcome to the Learning Management System',
        'total_classes': 0,
        'total_students': 0
    }

def get_recent_activity():
    """Get recent system activity"""
    try:
        recent_users = User.query.filter_by(is_active=True).order_by(User.created_at.desc()).limit(5).all()
        recent_students = Student.query.filter_by(status='active').order_by(Student.created_at.desc()).limit(5).all()
        
        activity = []
        for user in recent_users:
            activity.append({
                'type': 'user_registered',
                'message': f'New user registered: {user.full_name}',
                'timestamp': user.created_at
            })
        
        for student in recent_students:
            activity.append({
                'type': 'student_created',
                'message': f'New student created: {student.full_name}',
                'timestamp': student.created_at
            })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x['timestamp'], reverse=True)
        return activity[:10]
    except Exception as e:
        return []

# ===================================
# STUDENT MANAGEMENT FUNCTIONS
# ===================================

def get_students_by_department(department_id):
    """Get students by department"""
    try:
        return Student.query.filter_by(department_id=department_id, status='active').all()
    except Exception as e:
        print(f"Error getting students: {str(e)}")
        return []

def search_students(search_term):
    """Search students by name or ID"""
    try:
        search_pattern = f"%{search_term}%"
        return Student.query.filter(
            or_(
                Student.first_name.ilike(search_pattern),
                Student.last_name.ilike(search_pattern),
                Student.student_id.ilike(search_pattern),
                Student.email.ilike(search_pattern)
            ),
            Student.status == 'active'
        ).all()
    except Exception as e:
        print(f"Error searching students: {str(e)}")
        return []

# ===================================
# CLASS MANAGEMENT FUNCTIONS
# ===================================

def get_classes_by_tutor(tutor_id):
    """Get classes by tutor"""
    try:
        return Class.query.filter_by(tutor_id=tutor_id).order_by(Class.class_date.desc()).all()
    except Exception as e:
        print(f"Error getting tutor classes: {str(e)}")
        return []

# ===================================
# REPORT FUNCTIONS
# ===================================

def generate_user_report(filters):
    """Generate user report"""
    try:
        query = User.query.filter_by(is_active=True)
        
        if filters.get('role'):
            query = query.filter_by(role=filters['role'])
        if filters.get('department'):
            query = query.filter_by(department_id=filters['department'])
        
        users = query.all()
        
        report_data = {
            'total_users': len(users),
            'users': users,
            'by_role': {},
            'by_department': {}
        }
        
        # Group by role
        for user in users:
            role = user.role
            if role not in report_data['by_role']:
                report_data['by_role'][role] = 0
            report_data['by_role'][role] += 1
        
        # Group by department
        for user in users:
            dept = user.department.name if user.department else 'No Department'
            if dept not in report_data['by_department']:
                report_data['by_department'][dept] = 0
            report_data['by_department'][dept] += 1
        
        return report_data, "Report generated successfully."
        
    except Exception as e:
        return {}, f"Report generation failed: {str(e)}"

def generate_class_performance_report(date_range, filters):
    """Generate class performance report"""
    try:
        query = Class.query
        
        if date_range.get('start_date'):
            query = query.filter(Class.class_date >= datetime.strptime(date_range['start_date'], '%Y-%m-%d').date())
        if date_range.get('end_date'):
            query = query.filter(Class.class_date <= datetime.strptime(date_range['end_date'], '%Y-%m-%d').date())
        
        classes = query.all()
        
        report_data = {
            'total_classes': len(classes),
            'completed_classes': len([c for c in classes if c.status == 'completed']),
            'cancelled_classes': len([c for c in classes if c.status == 'cancelled']),
            'classes': classes
        }
        
        return report_data, "Report generated successfully."
        
    except Exception as e:
        return {}, f"Report generation failed: {str(e)}"

# ===================================
# FINANCE FUNCTIONS
# ===================================

def get_financial_dashboard_data():
    """Get financial dashboard data"""
    try:
        total_fees = StudentFee.query.count()
        paid_fees = StudentFee.query.filter_by(payment_status='paid').count()
        pending_fees = StudentFee.query.filter_by(payment_status='pending').count()
        overdue_fees = StudentFee.query.filter(
            StudentFee.payment_status == 'pending',
            StudentFee.due_date < datetime.now().date()
        ).count()
        
        total_revenue = StudentFee.query.filter_by(payment_status='paid').with_entities(func.sum(StudentFee.amount)).scalar() or 0
        pending_amount = StudentFee.query.filter_by(payment_status='pending').with_entities(func.sum(StudentFee.amount)).scalar() or 0
        
        data = {
            'total_fees': total_fees,
            'paid_fees': paid_fees,
            'pending_fees': pending_fees,
            'overdue_fees': overdue_fees,
            'total_revenue': float(total_revenue),
            'pending_amount': float(pending_amount),
            'collection_rate': round((paid_fees / total_fees * 100) if total_fees > 0 else 0, 1)
        }
        
        return data, "Financial data loaded successfully."
        
    except Exception as e:
        return {}, f"Financial data loading failed: {str(e)}"

def process_fee_payment(fee_id, payment_data):
    """Process student fee payment"""
    try:
        fee = StudentFee.query.get(fee_id)
        if not fee:
            return False, "Fee record not found."
        
        amount_paid = float(payment_data.get('amount_paid', 0))
        payment_method = payment_data.get('payment_method')
        transaction_id = payment_data.get('transaction_id', '')
        
        if amount_paid <= 0:
            return False, "Payment amount must be greater than zero."
        
        if amount_paid > fee.pending_amount:
            return False, f"Payment amount cannot exceed pending amount of ₹{fee.pending_amount}."
        
        # Update fee record
        fee.paid_amount += amount_paid
        fee.pending_amount -= amount_paid
        fee.payment_method = payment_method
        fee.transaction_id = transaction_id
        fee.processed_by = current_user.id if current_user.is_authenticated else None
        
        if fee.pending_amount <= 0:
            fee.payment_status = 'paid'
            fee.payment_date = datetime.now().date()
        else:
            fee.payment_status = 'partial'
        
        db.session.commit()
        
        return True, f"Payment of ₹{amount_paid} processed successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Payment processing failed: {str(e)}"

# ===================================
# FORM FUNCTIONS
# ===================================

def create_form_template(form_data):
    """Create form template"""
    try:
        form_template = FormTemplate(
            name=form_data['name'],
            description=form_data.get('description', ''),
            form_type=form_data['form_type'],
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        if 'fields' in form_data:
            form_template.set_fields(form_data['fields'])
        
        db.session.add(form_template)
        db.session.commit()
        
        return form_template, "Form template created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Form creation failed: {str(e)}"

def generate_form_html(form_id):
    """Generate HTML for form preview"""
    try:
        form_template = FormTemplate.query.get(form_id)
        if not form_template:
            return "", "Form not found."
        
        fields = form_template.get_fields()
        html_parts = []
        
        for field in fields:
            field_html = generate_field_html(field)
            html_parts.append(field_html)
        
        return '\n'.join(html_parts), "HTML generated successfully."
        
    except Exception as e:
        return "", f"HTML generation failed: {str(e)}"

def generate_field_html(field):
    """Generate HTML for a single field"""
    field_type = field.get('type', 'text')
    field_name = field.get('name', '')
    field_label = field.get('label', '')
    required = 'required' if field.get('required', False) else ''
    
    if field_type == 'text':
        return f'''
        <div class="form-group">
            <label for="{field_name}">{field_label}</label>
            <input type="text" name="{field_name}" id="{field_name}" class="form-control" {required}>
        </div>
        '''
    elif field_type == 'email':
        return f'''
        <div class="form-group">
            <label for="{field_name}">{field_label}</label>
            <input type="email" name="{field_name}" id="{field_name}" class="form-control" {required}>
        </div>
        '''
    elif field_type == 'textarea':
        return f'''
        <div class="form-group">
            <label for="{field_name}">{field_label}</label>
            <textarea name="{field_name}" id="{field_name}" class="form-control" rows="3" {required}></textarea>
        </div>
        '''
    elif field_type == 'select':
        options = field.get('options', [])
        option_html = '\n'.join([f'<option value="{opt}">{opt}</option>' for opt in options])
        return f'''
        <div class="form-group">
            <label for="{field_name}">{field_label}</label>
            <select name="{field_name}" id="{field_name}" class="form-control" {required}>
                <option value="">Select...</option>
                {option_html}
            </select>
        </div>
        '''
    else:
        return f'''
        <div class="form-group">
            <label for="{field_name}">{field_label}</label>
            <input type="{field_type}" name="{field_name}" id="{field_name}" class="form-control" {required}>
        </div>
        '''

# ===================================
# UTILITY FUNCTIONS
# ===================================

def get_available_permissions():
    """Get all available permissions"""
    return [
        'view_own_classes', 'view_department_classes', 'view_all_classes',
        'create_classes', 'edit_classes', 'delete_classes',
        'mark_attendance', 'upload_recordings', 'submit_feedback',
        'view_own_students', 'view_department_students', 'view_all_students',
        'create_students', 'edit_students', 'delete_students',
        'manage_enrollments', 'approve_demo_requests',
        'view_own_payroll', 'view_department_payroll', 'manage_all_payroll',
        'process_payments', 'manage_fees', 'approve_penalties',
        'create_users', 'edit_users', 'delete_users', 'approve_users',
        'manage_departments', 'assign_permissions',
        'email_reminders', 'escalation_management', 'bulk_communications',
        'system_settings', 'view_logs', 'manage_forms', 'generate_reports'
    ]

def update_user_profile(user_id, profile_data):
    """Update user profile"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        # Update allowed fields
        if 'full_name' in profile_data:
            user.full_name = profile_data['full_name']
        if 'phone' in profile_data:
            user.phone = profile_data['phone']
        if 'email' in profile_data:
            # Check email uniqueness
            existing = User.query.filter(User.email == profile_data['email'], User.id != user_id).first()
            if existing:
                return False, "Email already exists."
            user.email = profile_data['email']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Profile updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Profile update failed: {str(e)}"

