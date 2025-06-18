# functions/auth_functions.py - COMPLETE IMPLEMENTATION

from models import db, User, UserApproval
from flask import flash, redirect, url_for
from flask_login import login_user, logout_user
from datetime import datetime
import secrets

def authenticate_user(email, password):
    """Authenticate user with email and password"""
    try:
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return None, "Your account has been deactivated. Please contact admin."
            
            if not user.is_approved and user.role != 'superadmin':
                return None, "Your account is pending approval. Please wait for admin approval."
            
            # Reset failed login attempts
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return user, None
        else:
            # Track failed login attempts
            if user:
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.utcnow()
                db.session.commit()
        
        return None, "Invalid email or password."
    except Exception as e:
        return None, f"Login failed: {str(e)}"

def register_new_user(form_data):
    """Register a new user"""
    try:
        # Check if user already exists
        if User.query.filter_by(email=form_data['email']).first():
            return None, "User with this email already exists."
        
        if User.query.filter_by(username=form_data['username']).first():
            return None, "Username already taken."
        
        # Create new user
        user = User(
            username=form_data['username'],
            email=form_data['email'],
            full_name=form_data.get('full_name'),
            phone=form_data.get('phone'),
            role=form_data.get('role', 'tutor'),
            department_id=form_data.get('department_id'),
            is_active=True,
            is_approved=False  # Requires approval except for superadmin
        )
        
        user.set_password(form_data['password'])
        
        # Set custom fields if provided
        custom_fields = {}
        for key, value in form_data.items():
            if key.startswith('custom_'):
                custom_fields[key] = value
        
        if custom_fields:
            user.set_custom_fields(custom_fields)
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create approval request
        approval = UserApproval(
            user_id=user.id,
            status='pending',
            requested_at=datetime.utcnow()
        )
        db.session.add(approval)
        
        db.session.commit()
        return user, "Registration successful! Please wait for admin approval."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Registration failed: {str(e)}"

def create_superadmin(admin_data):
    """Create the initial superadmin user"""
    try:
        # Check if superadmin already exists
        existing_superadmin = User.query.filter_by(role='superadmin').first()
        if existing_superadmin:
            return False, "Superadmin already exists."
        
        # Validate required fields
        required_fields = ['full_name', 'username', 'email', 'password']
        for field in required_fields:
            if not admin_data.get(field):
                return False, f"{field.replace('_', ' ').title()} is required."
        
        # Create superadmin user
        superadmin = User(
            username=admin_data['username'],
            email=admin_data['email'],
            full_name=admin_data['full_name'],
            phone=admin_data.get('mobile', admin_data.get('phone')),
            role='superadmin',
            is_active=True,
            is_approved=True,  # Superadmin is auto-approved
            created_at=datetime.utcnow()
        )
        
        superadmin.set_password(admin_data['password'])
        
        # Set all permissions for superadmin
        superadmin.set_permissions(['*'])
        
        db.session.add(superadmin)
        db.session.commit()
        
        return True, f"Superadmin account created successfully for {admin_data['full_name']}!"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Superadmin creation failed: {str(e)}"

def login_user_session(user, remember=False):
    """Login user and create session"""
    try:
        login_user(user, remember=remember)
        return True
    except Exception as e:
        return False

def logout_user_session():
    """Logout user and clear session"""
    try:
        logout_user()
        return True
    except Exception as e:
        return False

def reset_user_password(user, new_password):
    """Reset user password"""
    try:
        user.set_password(new_password)
        user.failed_login_attempts = 0  # Reset failed attempts
        db.session.commit()
        return True, "Password reset successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Password reset failed: {str(e)}"

def change_user_password(user, current_password, new_password):
    """Change user password with current password verification"""
    try:
        # Verify current password
        if not user.check_password(current_password):
            return False, "Current password is incorrect."
        
        # Validate new password
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."
        
        # Set new password
        user.set_password(new_password)
        db.session.commit()
        
        return True, "Password changed successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Password change failed: {str(e)}"

def approve_user_account(user_id, approved_by_id, comments=""):
    """Approve user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        # Update user approval status
        user.is_approved = True
        
        # Update approval record
        approval = UserApproval.query.filter_by(user_id=user_id).first()
        if approval:
            approval.status = 'approved'
            approval.approved_by = approved_by_id
            approval.approved_at = datetime.utcnow()
            approval.comments = comments
        
        db.session.commit()
        return True, f"User {user.full_name} approved successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User approval failed: {str(e)}"

def reject_user_account(user_id, rejected_by_id, reason=""):
    """Reject user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        # Update approval record
        approval = UserApproval.query.filter_by(user_id=user_id).first()
        if approval:
            approval.status = 'rejected'
            approval.approved_by = rejected_by_id
            approval.approved_at = datetime.utcnow()
            approval.comments = reason
        
        # Deactivate user account
        user.is_active = False
        
        db.session.commit()
        return True, f"User {user.full_name} rejected."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User rejection failed: {str(e)}"

def generate_reset_token():
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)

def save_reset_token(user, token):
    """Save password reset token"""
    try:
        from flask import current_app
        
        # Store in app context (in production, use Redis or database)
        if not hasattr(current_app, 'reset_tokens'):
            current_app.reset_tokens = {}
        
        current_app.reset_tokens[token] = {
            'user_id': user.id,
            'expires': datetime.utcnow().timestamp() + 3600  # 1 hour
        }
        
        return True
        
    except Exception as e:
        return False

def verify_reset_token(token):
    """Verify and return user for reset token"""
    try:
        from flask import current_app
        
        if not hasattr(current_app, 'reset_tokens'):
            return None
        
        if token not in current_app.reset_tokens:
            return None
        
        token_data = current_app.reset_tokens[token]
        
        # Check expiration
        if datetime.utcnow().timestamp() > token_data['expires']:
            del current_app.reset_tokens[token]
            return None
        
        user = User.query.get(token_data['user_id'])
        if user:
            # Clean up used token
            del current_app.reset_tokens[token]
        
        return user
        
    except Exception as e:
        return None

def get_pending_users():
    """Get all users pending approval"""
    try:
        pending_users = db.session.query(User, UserApproval).join(
            UserApproval, User.id == UserApproval.user_id
        ).filter(
            UserApproval.status == 'pending',
            User.is_active == True
        ).all()
        
        return [approval for user, approval in pending_users]
        
    except Exception as e:
        return []

def deactivate_user(user_id, deactivated_by_id, reason=""):
    """Deactivate user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True, f"User {user.full_name} deactivated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User deactivation failed: {str(e)}"

def reactivate_user(user_id, reactivated_by_id):
    """Reactivate user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
        
        user.is_active = True
        user.failed_login_attempts = 0
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True, f"User {user.full_name} reactivated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"User reactivation failed: {str(e)}"