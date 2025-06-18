from flask_mail import Message
from email_utils import mail
from models import EmailTemplate
from flask import current_app

def send_welcome_email(user, temporary_password):
    """Send welcome email to new user"""
    try:
        template = EmailTemplate.query.filter_by(template_type='welcome').first()
        
        if template:
            subject = template.subject.replace('{{user_name}}', user.full_name)
            body = template.body_html.replace('{{user_name}}', user.full_name).replace('{{password}}', temporary_password)
        else:
            subject = "Welcome to the System"
            body = f"Hello {user.full_name}, your account has been created. Your temporary password is: {temporary_password}"
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=body
        )
        
        mail.send(msg)
        return True, "Welcome email sent successfully."
        
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

def send_password_reset_email(user, reset_token):
    """Send password reset email"""
    try:
        template = EmailTemplate.query.filter_by(template_type='password_reset').first()
        
        reset_url = f"{current_app.config['BASE_URL']}/reset-password/{reset_token}"
        
        if template:
            subject = template.subject
            body = template.body_html.replace('{{user_name}}', user.full_name).replace('{{reset_url}}', reset_url)
        else:
            subject = "Password Reset Request"
            body = f"Hello {user.full_name}, click here to reset your password: {reset_url}"
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=body
        )
        
        mail.send(msg)
        return True, "Password reset email sent successfully."
        
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

def send_approval_notification(user, approved, comments=""):
    """Send account approval/rejection notification"""
    try:
        template_type = 'approval_approved' if approved else 'approval_rejected'
        template = EmailTemplate.query.filter_by(template_type=template_type).first()
        
        if template:
            subject = template.subject
            body = template.body_html.replace('{{user_name}}', user.full_name).replace('{{comments}}', comments)
        else:
            if approved:
                subject = "Account Approved"
                body = f"Hello {user.full_name}, your account has been approved."
            else:
                subject = "Account Rejected"
                body = f"Hello {user.full_name}, your account has been rejected. Reason: {comments}"
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=body
        )
        
        mail.send(msg)
        return True, "Approval notification sent successfully."
        
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"

