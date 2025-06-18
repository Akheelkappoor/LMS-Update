# functions/notification_functions.py - FIXED VERSION

from models import db, SystemNotification, User, TutorLateArrival
from flask_login import current_user
from datetime import datetime

def send_late_arrival_notification(tutor_id, late_minutes, class_id):
    """Send notification about tutor late arrival"""
    try:
        tutor = User.query.get(tutor_id)
        from models import Class
        class_obj = Class.query.get(class_id)
        
        # Notify finance coordinators
        finance_coordinators = User.query.filter_by(role='finance_coordinator', is_active=True).all()
        
        for coordinator in finance_coordinators:
            notification = SystemNotification(
                notification_type='tutor_late_arrival',
                title='Tutor Late Arrival Alert',
                message=f'{tutor.full_name} arrived {late_minutes} minutes late for {class_obj.subject} class.',
                priority='high',
                recipient_type='user',
                recipient_id=coordinator.id,
                recipient_email=coordinator.email,
                action_required=True,
                related_entity_type='class',
                related_entity_id=class_id,
                created_by=current_user.id
            )
            db.session.add(notification)
        
        db.session.commit()
        return True, "Late arrival notifications sent."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Notification failed: {str(e)}"

def create_system_notification(notification_data):
    """Create a system notification"""
    try:
        notification = SystemNotification(
            notification_type=notification_data['type'],
            title=notification_data['title'],
            message=notification_data['message'],
            priority=notification_data.get('priority', 'normal'),
            recipient_type=notification_data['recipient_type'],
            recipient_id=notification_data.get('recipient_id'),
            recipient_role=notification_data.get('recipient_role'),
            recipient_department=notification_data.get('recipient_department'),
            recipient_email=notification_data.get('recipient_email'),
            action_required=notification_data.get('action_required', False),
            related_entity_type=notification_data.get('related_entity_type'),
            related_entity_id=notification_data.get('related_entity_id'),
            action_url=notification_data.get('action_url'),
            expires_at=notification_data.get('expires_at'),
            created_by=current_user.id
        )
        
        # CHANGED: Use extra_data instead of metadata
        if 'extra_data' in notification_data:
            notification.set_extra_data(notification_data['extra_data'])
        
        db.session.add(notification)
        db.session.commit()
        return notification, "Notification created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Notification creation failed: {str(e)}"

def mark_notification_as_read(notification_id, user_id):
    """Mark notification as read"""
    try:
        notification = SystemNotification.query.get(notification_id)
        if not notification:
            return False, "Notification not found."
        
        # Check if user can mark this notification as read
        if notification.recipient_type == 'user' and notification.recipient_id != user_id:
            return False, "Access denied."
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        db.session.commit()
        return True, "Notification marked as read."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to mark notification as read: {str(e)}"

def get_user_notifications(user_id, unread_only=False):
    """Get notifications for a user"""
    query = SystemNotification.query.filter(
        db.or_(
            SystemNotification.recipient_id == user_id,
            SystemNotification.recipient_role == User.query.get(user_id).role,
            SystemNotification.recipient_type == 'all'
        )
    )
    
    if unread_only:
        query = query.filter(SystemNotification.is_read == False)
    
    return query.order_by(SystemNotification.created_at.desc()).all()