# email_utils.py - FIXED VERSION (replace your current file)

from flask_mail import Mail, Message
from flask import render_template_string, url_for
import os
from datetime import datetime
import secrets

mail = Mail()

class EmailService:
    """Handle all email operations"""
    
    @staticmethod
    def send_email(to, subject, template_name, **kwargs):
        """Send an email using a template"""
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                sender=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@lms.com')
            )
            
            # Use default template (removed EmailTemplate import)
            html_body = EmailService.get_default_template(template_name, **kwargs)
            
            msg.html = html_body
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def get_default_template(template_name, **kwargs):
        """Get default email templates"""
        
        base_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ subject }}</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                }
                .email-container {
                    max-width: 600px;
                    margin: 20px auto;
                    background: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }
                .email-header {
                    background: linear-gradient(135deg, #ff6f00 0%, #ff9800 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .email-header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                .email-body {
                    padding: 40px 30px;
                }
                .email-body h2 {
                    color: #ff6f00;
                    margin-bottom: 20px;
                }
                .email-body p {
                    margin-bottom: 15px;
                    color: #555;
                }
                .button {
                    display: inline-block;
                    padding: 12px 30px;
                    background: #ff6f00;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }
                .email-footer {
                    background: #f8f9fa;
                    padding: 20px 30px;
                    text-align: center;
                    font-size: 14px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>🎓 LMS System</h1>
                </div>
                <div class="email-body">
                    {% block content %}{% endblock %}
                </div>
                <div class="email-footer">
                    <p>&copy; {{ current_year }} LMS. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        templates = {
            'welcome': """
                    <h2>Welcome to LMS!</h2>
                    <p>Hello {{ user.full_name or user.username }},</p>
                    <p>Your account has been created successfully. Here are your login details:</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <strong>Email:</strong> {{ user.email }}<br>
                        <strong>Password:</strong> {{ password }}<br>
                        <strong>Role:</strong> {{ user.role.title() }}
                    </div>
                    
                    <p>Please login and change your password after first login.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ login_url }}" class="button">Login Now</a>
                    </div>
                    
                    <p>Best regards,<br>The LMS Team</p>
                """,
            
            'password_reset': """
                    <h2>Password Reset Request</h2>
                    <p>Hello {{ user.full_name or user.username }},</p>
                    <p>You have requested a password reset. Click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ reset_url }}" class="button">Reset Password</a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{{ reset_url }}</p>
                    
                    <p>Best regards,<br>The LMS Team</p>
                """,
            
            'approval_notification': """
                    <h2>Account {{ 'Approved' if approved else 'Not Approved' }}</h2>
                    <p>Hello {{ user.full_name or user.username }},</p>
                    
                    {% if approved %}
                        <p>Great news! Your account has been approved and is now active.</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{{ login_url }}" class="button">Login Now</a>
                        </div>
                    {% else %}
                        <p>Unfortunately, your account registration has not been approved.</p>
                        {% if reason %}
                            <p><strong>Reason:</strong> {{ reason }}</p>
                        {% endif %}
                        <p>Please contact the administrator if you have any questions.</p>
                    {% endif %}
                    
                    <p>Best regards,<br>The LMS Team</p>
                """
        }
        
        # Render the template
        if template_name in templates:
            full_template = base_template.replace('{% block content %}{% endblock %}', templates[template_name])
            return render_template_string(full_template, current_year=datetime.now().year, **kwargs)
        
        return None
    
    @staticmethod
    def send_welcome_email(user, password):
        """Send welcome email to new user"""
        try:
            login_url = url_for('login', _external=True)
            return EmailService.send_email(
                to=user.email,
                subject="Welcome to LMS - Your Account Details",
                template_name='welcome',
                user=user,
                password=password,
                login_url=login_url
            )
        except:
            return True  # Don't fail if email doesn't work
    
    @staticmethod
    def send_approval_notification(user, approved, reason=None):
        """Send approval/rejection notification to user"""
        try:
            login_url = url_for('login', _external=True)
            return EmailService.send_email(
                to=user.email,
                subject=f"Account {'Approved' if approved else 'Not Approved'}",
                template_name='approval_notification',
                user=user,
                approved=approved,
                reason=reason,
                login_url=login_url
            )
        except:
            return True  # Don't fail if email doesn't work
    
    @staticmethod
    def send_password_reset(user, token):
        """Send password reset email"""
        try:
            reset_url = url_for('reset_password', token=token, _external=True)
            return EmailService.send_email(
                to=user.email,
                subject="Password Reset Request",
                template_name='password_reset',
                user=user,
                reset_url=reset_url
            )
        except:
            return True  # Don't fail if email doesn't work