# functions/user_functions.py - COMPLETE IMPLEMENTATION

from models import db, User, Department, Class, Student, StudentEnrollment, TutorProfile
from flask_login import current_user
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

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
        from models import User, Department, Student, Class
        
        total_users = User.query.filter_by(is_active=True).count()
        total_departments = Department.query.filter_by(is_active=True).count()
        total_students = Student.query.filter_by(status='active').count()
        total_classes = Class.query.count()
        pending_approvals = User.query.filter_by(is_approved=False, is_active=True).count()
        
        return {
            'total_users': total_users,
            'total_departments': total_departments,
            'total_students': total_students,
            'total_classes': total_classes,
            'pending_approvals': pending_approvals,
            'system_health': 'Excellent'
        }
    except Exception as e:
        print(f"Superadmin dashboard data error: {str(e)}")
        return {
            'total_users': 0,
            'total_departments': 0,
            'total_students': 0,
            'total_classes': 0,
            'pending_approvals': 0,
            'system_health': 'Unknown'
        }

def get_admin_dashboard_data():
    """Get admin dashboard statistics"""
    today = datetime.now().date()
    
    data = {
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_tutors': User.query.filter_by(role='tutor', is_active=True).count(),
        'total_coordinators': User.query.filter_by(role='coordinator', is_active=True).count(),
        'total_students': Student.query.filter_by(status='active').count(),
        'pending_approvals': User.query.filter_by(is_approved=False, is_active=True).count(),
        'classes_today': Class.query.filter(Class.class_date == today).count(),
        'departments': Department.query.filter_by(is_active=True).count(),
        'recent_activity': get_recent_activity(),
        'monthly_growth': get_monthly_growth_stats()
    }
    
    return data

def get_coordinator_dashboard_data(user):
    """Get coordinator dashboard for specific department"""
    today = datetime.now().date()
    dept_id = user.department_id
    
    # Get department info
    department = Department.query.get(dept_id) if dept_id else None
    
    data = {
        'department_name': department.name if department else 'No Department',
        'total_tutors': User.query.filter_by(
            department_id=dept_id, 
            role='tutor', 
            is_active=True
        ).count(),
        'total_students': Student.query.filter_by(
            department_id=dept_id, 
            status='active'
        ).count(),
        'classes_today': get_department_classes_today(dept_id),
        'active_enrollments': StudentEnrollment.query.join(Student).filter(
            Student.department_id == dept_id,
            StudentEnrollment.status == 'active'
        ).count(),
        'pending_files': 0,  # Placeholder for pending tasks
        'recent_enrollments': get_recent_department_enrollments(dept_id),
        'department_performance': get_department_performance(dept_id)
    }
    
    return data

def get_tutor_dashboard_data(user):
    """Get tutor dashboard data"""
    today = datetime.now().date()
    
    # Get tutor's classes
    today_classes = Class.query.filter_by(
        tutor_id=user.id,
        class_date=today
    ).order_by(Class.start_time).all()
    
    # Get this week's classes
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_classes = Class.query.filter(
        Class.tutor_id == user.id,
        Class.class_date >= week_start,
        Class.class_date <= week_end
    ).count()
    
    # Get students count
    student_enrollments = StudentEnrollment.query.filter_by(
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
    
    data = {
        'classes_today': len(today_classes),
        'classes_this_week': week_classes,
        'active_students': student_enrollments,
        'completed_classes': completed_classes,
        'today_schedule': today_classes,
        'upcoming_classes': get_tutor_upcoming_classes(user.id),
        'recent_feedback': get_tutor_recent_feedback(user.id),
        'performance_rating': user.feedback_rating or 0.0
    }
    
    return data

def get_finance_dashboard_data(user):
    """Get finance coordinator dashboard data"""
    from models import StudentFee, TutorLateArrival
    
    today = datetime.now().date()
    
    data = {
        'pending_payments': StudentFee.query.filter_by(payment_status='pending').count(),
        'total_revenue_month': get_monthly_revenue(),
        'late_arrival_incidents': TutorLateArrival.query.filter(
            TutorLateArrival.recorded_at >= datetime.now().replace(day=1)
        ).count(),
        'payroll_pending': get_pending_payroll_count(),
        'fee_collections': get_fee_collection_stats(),
        'tutor_penalties': get_tutor_penalty_stats(),
        'financial_overview': get_financial_overview()
    }
    
    return data

def get_default_dashboard_data():
    """Default dashboard data fallback"""
    return {
        'message': 'Welcome to the system',
        'user_role': 'default',
        'system_status': 'active'
    }

# Helper functions for dashboard data

def get_department_classes_today(department_id):
    """Get today's classes for a department"""
    today = datetime.now().date()
    return Class.query.join(StudentEnrollment).join(Student).filter(
        Student.department_id == department_id,
        Class.class_date == today
    ).count()

def get_recent_department_enrollments(department_id, limit=5):
    """Get recent enrollments for a department"""
    return StudentEnrollment.query.join(Student).filter(
        Student.department_id == department_id
    ).order_by(StudentEnrollment.created_at.desc()).limit(limit).all()

def get_department_performance(department_id):
    """Get department performance metrics"""
    completed_classes = Class.query.join(StudentEnrollment).join(Student).filter(
        Student.department_id == department_id,
        Class.status == 'completed'
    ).count()
    
    total_classes = Class.query.join(StudentEnrollment).join(Student).filter(
        Student.department_id == department_id
    ).count()
    
    completion_rate = (completed_classes / total_classes * 100) if total_classes > 0 else 0
    
    return {
        'completion_rate': round(completion_rate, 1),
        'total_classes': total_classes,
        'completed_classes': completed_classes
    }

def get_tutor_upcoming_classes(tutor_id, limit=5):
    """Get upcoming classes for a tutor"""
    tomorrow = datetime.now().date() + timedelta(days=1)
    return Class.query.filter(
        Class.tutor_id == tutor_id,
        Class.class_date >= tomorrow,
        Class.status == 'scheduled'
    ).order_by(Class.class_date, Class.start_time).limit(limit).all()

def get_tutor_recent_feedback(tutor_id, limit=3):
    """Get recent feedback for a tutor"""
    from models import ClassFeedback
    return ClassFeedback.query.filter_by(
        tutor_id=tutor_id
    ).order_by(ClassFeedback.submitted_at.desc()).limit(limit).all()

def get_recent_activity(limit=10):
    """Get recent system activity"""
    activities = []
    
    # Recent user registrations
    recent_users = User.query.filter_by(is_active=True).order_by(User.created_at.desc()).limit(5).all()
    for user in recent_users:
        activities.append({
            'type': 'user_registration',
            'message': f'New {user.role} registered: {user.full_name}',
            'timestamp': user.created_at,
            'icon': 'fa-user-plus'
        })
    
    # Recent enrollments
    recent_enrollments = StudentEnrollment.query.order_by(StudentEnrollment.created_at.desc()).limit(5).all()
    for enrollment in recent_enrollments:
        activities.append({
            'type': 'enrollment',
            'message': f'Student enrolled in {enrollment.subject}',
            'timestamp': enrollment.created_at,
            'icon': 'fa-graduation-cap'
        })
    
    # Sort by timestamp and return limited results
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]

def get_monthly_growth_stats():
    """Get monthly growth statistics"""
    current_month = datetime.now().replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    current_users = User.query.filter(
        User.created_at >= current_month,
        User.is_active == True
    ).count()
    
    last_month_users = User.query.filter(
        User.created_at >= last_month,
        User.created_at < current_month,
        User.is_active == True
    ).count()
    
    growth_rate = ((current_users - last_month_users) / last_month_users * 100) if last_month_users > 0 else 0
    
    return {
        'new_users_this_month': current_users,
        'new_users_last_month': last_month_users,
        'growth_rate': round(growth_rate, 1)
    }

def get_monthly_revenue():
    """Get monthly revenue (placeholder)"""
    # This would connect to actual payment data
    return 50000.0  # Placeholder

def get_pending_payroll_count():
    """Get count of pending payroll items"""
    # This would connect to actual payroll data
    return 5  # Placeholder

def get_fee_collection_stats():
    """Get fee collection statistics"""
    from models import StudentFee
    
    total_fees = StudentFee.query.count()
    paid_fees = StudentFee.query.filter_by(payment_status='paid').count()
    pending_fees = StudentFee.query.filter_by(payment_status='pending').count()
    
    return {
        'total': total_fees,
        'paid': paid_fees,
        'pending': pending_fees,
        'collection_rate': round((paid_fees / total_fees * 100) if total_fees > 0 else 0, 1)
    }

def get_tutor_penalty_stats():
    """Get tutor penalty statistics"""
    from models import TutorLateArrival
    
    current_month = datetime.now().replace(day=1)
    incidents = TutorLateArrival.query.filter(
        TutorLateArrival.recorded_at >= current_month
    ).count()
    
    total_penalties = db.session.query(func.sum(TutorLateArrival.penalty_amount)).filter(
        TutorLateArrival.recorded_at >= current_month
    ).scalar() or 0
    
    return {
        'incidents_this_month': incidents,
        'total_penalties': float(total_penalties)
    }

def get_financial_overview():
    """Get financial overview"""
    return {
        'total_revenue': 150000.0,  # Placeholder
        'pending_collections': 25000.0,  # Placeholder
        'monthly_expenses': 80000.0,  # Placeholder
        'net_profit': 45000.0  # Placeholder
    }

# User management functions

def update_user_profile(user_id, profile_data):
    """Update user profile information"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        # Update allowed profile fields
        allowed_fields = ['full_name', 'phone', 'profile_picture', 'date_of_birth']
        for field in allowed_fields:
            if field in profile_data and profile_data[field]:
                setattr(user, field, profile_data[field])
        
        # Update emergency contact if provided
        if 'emergency_contact' in profile_data:
            user.set_emergency_contact(profile_data['emergency_contact'])
        
        # Update custom fields if provided
        if any(key.startswith('custom_') for key in profile_data.keys()):
            custom_fields = user.get_custom_fields()
            for key, value in profile_data.items():
                if key.startswith('custom_'):
                    custom_fields[key] = value
            user.set_custom_fields(custom_fields)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Profile updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Profile update failed: {str(e)}"

def get_user_statistics():
    """Get user statistics for admin dashboard"""
    stats = {
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_tutors': User.query.filter_by(role='tutor', is_active=True).count(),
        'total_coordinators': User.query.filter_by(role='coordinator', is_active=True).count(),
        'total_admins': User.query.filter(User.role.in_(['admin', 'superadmin']), User.is_active == True).count(),
        'pending_approvals': User.query.filter_by(is_approved=False, is_active=True).count(),
        'inactive_users': User.query.filter_by(is_active=False).count(),
        'users_by_department': get_users_by_department_stats(),
        'recent_registrations': User.query.filter_by(is_active=True).order_by(User.created_at.desc()).limit(10).all()
    }
    
    return stats

def get_users_by_department_stats():
    """Get user count by department"""
    return db.session.query(
        Department.name,
        func.count(User.id).label('user_count')
    ).join(User, User.department_id == Department.id).filter(
        User.is_active == True,
        Department.is_active == True
    ).group_by(Department.name).all()

def search_users(search_term):
    """Search users by name, email, or username"""
    search_pattern = f"%{search_term}%"
    return User.query.filter(
        or_(
            User.full_name.ilike(search_pattern),
            User.email.ilike(search_pattern),
            User.username.ilike(search_pattern)
        ),
        User.is_active == True
    ).all()

def get_users_by_role(role):
    """Get users by specific role"""
    return User.query.filter_by(role=role, is_active=True).all()

def get_users_by_department(department_id):
    """Get users by department"""
    return User.query.filter_by(department_id=department_id, is_active=True).all()

# Permission management functions

def get_role_permissions(role):
    """Get default permissions for a role"""
    role_permissions = {
        'tutor': [
            'view_own_classes',
            'mark_attendance', 
            'upload_recordings',
            'submit_feedback',
            'view_own_schedule',
            'view_own_students',
            'view_own_payroll',
            'update_profile'
        ],
        'coordinator': [
            'view_department_users',
            'create_students',
            'manage_enrollments',
            'view_department_classes',
            'generate_department_reports',
            'approve_requests',
            'manage_department_schedule',
            'view_department_analytics'
        ],
        'finance_coordinator': [
            'manage_all_payroll',
            'process_payments',
            'view_financial_reports',
            'manage_fees',
            'approve_penalties',
            'view_all_departments'
        ],
        'admin': [
            'manage_all_users',
            'manage_departments',
            'system_settings',
            'view_all_reports',
            'approve_users',
            'manage_forms'
        ],
        'superadmin': ['*']  # All permissions
    }
    
    return role_permissions.get(role, [])

def check_user_permission(user, permission):
    """Check if user has specific permission"""
    try:
        # Superadmin has all permissions
        if user.role == 'superadmin':
            return True
        
        # Use the user's has_permission method
        return user.has_permission(permission)
        
    except Exception as e:
        print(f"Permission check error: {str(e)}")
        return False

def update_user_permissions(user_id, permissions):
    """Update user permissions"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        user.set_permissions(permissions)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Permissions updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Permission update failed: {str(e)}"

def get_available_permissions():
    """Get all available permissions in the system"""
    return [
        # Class Management
        'view_own_classes', 'view_department_classes', 'view_all_classes',
        'create_classes', 'edit_classes', 'delete_classes',
        'mark_attendance', 'upload_recordings', 'submit_feedback',
        
        # Student Management  
        'view_own_students', 'view_department_students', 'view_all_students',
        'create_students', 'edit_students', 'delete_students',
        'manage_enrollments', 'approve_demo_requests',
        
        # Financial Management
        'view_own_payroll', 'view_department_payroll', 'manage_all_payroll',
        'process_payments', 'manage_fees', 'approve_penalties',
        
        # User Management
        'create_users', 'edit_users', 'delete_users', 'approve_users',
        'manage_departments', 'assign_permissions',
        
        # Communication
        'email_reminders', 'escalation_management', 'bulk_communications',
        
        # System Administration
        'system_settings', 'view_logs', 'manage_forms', 'generate_reports',
        
        # New Features
        'manage_demos', 'schedule_demos', 'payment_approval', 
        'late_arrival_management', 'quality_assurance'
    ]

def assign_user_to_department(user_id, department_id):
    """Assign user to a department"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        department = Department.query.get(department_id)
        if not department:
            return False, "Department not found."
        
        user.department_id = department_id
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, f"User assigned to {department.name} successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Department assignment failed: {str(e)}"

def create_user(user_data):
    """Create a new user (admin function)"""
    try:
        # Check if user already exists
        if User.query.filter_by(email=user_data['email']).first():
            return None, "User with this email already exists."
        
        if User.query.filter_by(username=user_data['username']).first():
            return None, "Username already taken."
        
        # Create new user
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data.get('full_name'),
            phone=user_data.get('phone'),
            role=user_data.get('role', 'tutor'),
            department_id=user_data.get('department_id'),
            is_active=True,
            is_approved=user_data.get('is_approved', True),  # Admin-created users can be auto-approved
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        # Set password
        password = user_data.get('password', 'temp123456')  # Default temp password
        user.set_password(password)
        
        # Set permissions if provided
        if 'permissions' in user_data:
            user.set_permissions(user_data['permissions'])
        
        # Set custom fields if provided
        custom_fields = {k: v for k, v in user_data.items() if k.startswith('custom_')}
        if custom_fields:
            user.set_custom_fields(custom_fields)
        
        db.session.add(user)
        db.session.commit()
        
        return user, "User created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"User creation failed: {str(e)}"