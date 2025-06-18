# functions/decorators.py

from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role not in ['superadmin', 'admin']:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def coordinator_required(f):
    """Decorator for coordinator-level access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role not in ['superadmin', 'admin', 'coordinator']:
            flash('You need coordinator privileges to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    """Decorator for superadmin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'superadmin':
            flash('You need superadmin privileges to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def tutor_required(f):
    """Decorator for tutor-level access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role not in ['superadmin', 'admin', 'coordinator', 'tutor']:
            flash('You need tutor privileges to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def finance_required(f):
    """Decorator for finance coordinator access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role not in ['superadmin', 'admin', 'finance_coordinator']:
            flash('You need finance coordinator privileges to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def approved_required(f):
    """Decorator to ensure user is approved"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_approved and current_user.role != 'superadmin':
            flash('Your account is pending approval. Please wait for admin approval.', 'warning')
            return redirect(url_for('pending_approval'))
        return f(*args, **kwargs)
    return decorated_function

def active_required(f):
    """Decorator to ensure user is active"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact admin.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def department_access_required(f):
    """Decorator to check department access for coordinators"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        # Superadmin and admin have access to all departments
        if current_user.role in ['superadmin', 'admin']:
            return f(*args, **kwargs)
        
        # For coordinators, check if they have department access
        if current_user.role == 'coordinator':
            department_id = kwargs.get('department_id') or request.args.get('department_id')
            if department_id and int(department_id) != current_user.department_id:
                flash('You can only access your own department.', 'danger')
                return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator to check specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            if not current_user.has_permission(permission):
                flash(f'You need {permission} permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator