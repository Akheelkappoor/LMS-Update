# functions/class_functions.py - COMPLETE IMPLEMENTATION

from models import db, Class, StudentAttendance, StudentEnrollment, Student, User, ClassSession, ClassFeedback, TutorLateArrival
from flask_login import current_user
from datetime import datetime, timedelta, time
from sqlalchemy import func, and_, or_
import calendar

def create_class(class_data):
    """Create a new class session"""
    try:
        # Validate required fields
        required_fields = ['enrollment_id', 'tutor_id', 'subject', 'class_date', 'start_time', 'end_time']
        for field in required_fields:
            if not class_data.get(field):
                return None, f"{field.replace('_', ' ').title()} is required."
        
        # Validate enrollment exists
        enrollment = StudentEnrollment.query.get(class_data['enrollment_id'])
        if not enrollment:
            return None, "Student enrollment not found."
        
        # Validate tutor exists
        tutor = User.query.filter_by(id=class_data['tutor_id'], role='tutor').first()
        if not tutor:
            return None, "Tutor not found."
        
        # Parse date and time
        if isinstance(class_data['class_date'], str):
            class_date = datetime.strptime(class_data['class_date'], '%Y-%m-%d').date()
        else:
            class_date = class_data['class_date']
        
        if isinstance(class_data['start_time'], str):
            start_time = datetime.strptime(class_data['start_time'], '%H:%M').time()
        else:
            start_time = class_data['start_time']
        
        if isinstance(class_data['end_time'], str):
            end_time = datetime.strptime(class_data['end_time'], '%H:%M').time()
        else:
            end_time = class_data['end_time']
        
        # Validate time logic
        if start_time >= end_time:
            return None, "End time must be after start time."
        
        # Check for scheduling conflicts
        conflict = Class.query.filter(
            Class.tutor_id == class_data['tutor_id'],
            Class.class_date == class_date,
            Class.status.in_(['scheduled', 'in_progress']),
            or_(
                and_(Class.start_time <= start_time, Class.end_time > start_time),
                and_(Class.start_time < end_time, Class.end_time >= end_time),
                and_(Class.start_time >= start_time, Class.end_time <= end_time)
            )
        ).first()
        
        if conflict:
            return None, f"Tutor has a scheduling conflict at {conflict.start_time}-{conflict.end_time}."
        
        # Create class
        new_class = Class(
            enrollment_id=class_data['enrollment_id'],
            tutor_id=class_data['tutor_id'],
            subject=class_data['subject'],
            class_date=class_date,
            start_time=start_time,
            end_time=end_time,
            topic_covered=class_data.get('topic_covered'),
            homework_assigned=class_data.get('homework_assigned'),
            class_notes=class_data.get('class_notes'),
            meeting_link=class_data.get('meeting_link'),
            meeting_id=class_data.get('meeting_id'),
            meeting_password=class_data.get('meeting_password'),
            status='scheduled'
        )
        
        # Handle file uploads
        if class_data.get('materials_uploaded'):
            import json
            materials = class_data['materials_uploaded']
            if isinstance(materials, list):
                new_class.materials_uploaded = json.dumps(materials)
            else:
                new_class.materials_uploaded = materials
        
        db.session.add(new_class)
        db.session.flush()  # Get class ID
        
        # Create session tracking record
        session_tracking = ClassSession(
            class_id=new_class.id,
            session_status='scheduled',
            compliance_deadline=datetime.combine(class_date, end_time) + timedelta(hours=24)
        )
        db.session.add(session_tracking)
        
        db.session.commit()
        return new_class, "Class created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Class creation failed: {str(e)}"

def update_class(class_id, class_data):
    """Update existing class"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        # Check if class can be updated
        if class_obj.status in ['completed', 'cancelled']:
            return False, f"Cannot update {class_obj.status} class."
        
        # Update allowed fields
        updateable_fields = [
            'subject', 'topic_covered', 'homework_assigned', 'class_notes',
            'meeting_link', 'meeting_id', 'meeting_password'
        ]
        
        for field in updateable_fields:
            if field in class_data:
                setattr(class_obj, field, class_data[field])
        
        # Update date/time if provided and class is still scheduled
        if class_obj.status == 'scheduled':
            if 'class_date' in class_data:
                if isinstance(class_data['class_date'], str):
                    class_obj.class_date = datetime.strptime(class_data['class_date'], '%Y-%m-%d').date()
                else:
                    class_obj.class_date = class_data['class_date']
            
            if 'start_time' in class_data:
                if isinstance(class_data['start_time'], str):
                    class_obj.start_time = datetime.strptime(class_data['start_time'], '%H:%M').time()
                else:
                    class_obj.start_time = class_data['start_time']
            
            if 'end_time' in class_data:
                if isinstance(class_data['end_time'], str):
                    class_obj.end_time = datetime.strptime(class_data['end_time'], '%H:%M').time()
                else:
                    class_obj.end_time = class_data['end_time']
        
        # Handle materials upload
        if 'materials_uploaded' in class_data:
            import json
            materials = class_data['materials_uploaded']
            if isinstance(materials, list):
                class_obj.materials_uploaded = json.dumps(materials)
            else:
                class_obj.materials_uploaded = materials
        
        class_obj.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Class updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Class update failed: {str(e)}"

def start_class(class_id):
    """Start a class session"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        if class_obj.status != 'scheduled':
            return False, f"Cannot start {class_obj.status} class."
        
        # Check if it's the right time to start (within 15 minutes of start time)
        now = datetime.now()
        class_datetime = datetime.combine(class_obj.class_date, class_obj.start_time)
        
        if now < class_datetime - timedelta(minutes=15):
            return False, "Class cannot be started more than 15 minutes early."
        
        # Update class status
        class_obj.status = 'in_progress'
        class_obj.actual_start_time = now
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.session_status = 'in_progress'
            session.started_at = now
            
            # Check for late arrival
            if now > class_datetime + timedelta(minutes=5):
                late_minutes = int((now - class_datetime).total_seconds() / 60)
                session.tutor_late_arrival = True
                session.late_minutes = late_minutes
                
                # Record late arrival for payroll deduction
                record_tutor_late_arrival(class_id, late_minutes)
        
        db.session.commit()
        return True, "Class started successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to start class: {str(e)}"

def end_class(class_id):
    """End a class session"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        if class_obj.status != 'in_progress':
            return False, f"Cannot end {class_obj.status} class."
        
        now = datetime.now()
        
        # Update class status
        class_obj.status = 'completed'
        class_obj.actual_end_time = now
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.session_status = 'completed'
            session.ended_at = now
            session.update_compliance_status()
        
        # Update tutor's total classes count
        tutor = class_obj.tutor
        tutor.total_classes_taught = (tutor.total_classes_taught or 0) + 1
        
        db.session.commit()
        return True, "Class completed successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to end class: {str(e)}"

def cancel_class(class_id, reason=""):
    """Cancel a class session"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        if class_obj.status in ['completed', 'cancelled']:
            return False, f"Cannot cancel {class_obj.status} class."
        
        # Update class status
        class_obj.status = 'cancelled'
        if reason:
            class_obj.class_notes = f"{class_obj.class_notes or ''}\nCancellation reason: {reason}".strip()
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.session_status = 'cancelled'
        
        db.session.commit()
        return True, "Class cancelled successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to cancel class: {str(e)}"

def reschedule_class(class_id, new_date, new_start_time, new_end_time, reason=""):
    """Reschedule a class to new date/time"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        if class_obj.status != 'scheduled':
            return False, f"Cannot reschedule {class_obj.status} class."
        
        # Parse new date/time
        if isinstance(new_date, str):
            new_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        
        if isinstance(new_start_time, str):
            new_start_time = datetime.strptime(new_start_time, '%H:%M').time()
        
        if isinstance(new_end_time, str):
            new_end_time = datetime.strptime(new_end_time, '%H:%M').time()
        
        # Validate new time
        if new_start_time >= new_end_time:
            return False, "End time must be after start time."
        
        # Check for conflicts with new time
        conflict = Class.query.filter(
            Class.tutor_id == class_obj.tutor_id,
            Class.class_date == new_date,
            Class.id != class_id,
            Class.status.in_(['scheduled', 'in_progress']),
            or_(
                and_(Class.start_time <= new_start_time, Class.end_time > new_start_time),
                and_(Class.start_time < new_end_time, Class.end_time >= new_end_time),
                and_(Class.start_time >= new_start_time, Class.end_time <= new_end_time)
            )
        ).first()
        
        if conflict:
            return False, f"Scheduling conflict with existing class at {conflict.start_time}-{conflict.end_time}."
        
        # Update class details
        old_schedule = f"{class_obj.class_date} {class_obj.start_time}-{class_obj.end_time}"
        class_obj.class_date = new_date
        class_obj.start_time = new_start_time
        class_obj.end_time = new_end_time
        class_obj.status = 'rescheduled'
        
        # Add reschedule note
        reschedule_note = f"Rescheduled from {old_schedule} to {new_date} {new_start_time}-{new_end_time}"
        if reason:
            reschedule_note += f". Reason: {reason}"
        
        class_obj.class_notes = f"{class_obj.class_notes or ''}\n{reschedule_note}".strip()
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.compliance_deadline = datetime.combine(new_date, new_end_time) + timedelta(hours=24)
        
        db.session.commit()
        return True, "Class rescheduled successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to reschedule class: {str(e)}"

def mark_student_attendance(class_id, student_id, attendance_data):
    """Mark student attendance for a class"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."
        
        # Check if attendance already exists
        existing = StudentAttendance.query.filter_by(
            class_session_id=class_id,
            student_id=student_id
        ).first()
        
        if existing:
            # Update existing attendance
            existing.status = attendance_data.get('status', 'present')
            existing.arrival_time = attendance_data.get('arrival_time')
            existing.departure_time = attendance_data.get('departure_time')
            existing.notes = attendance_data.get('notes', '')
            existing.updated_at = datetime.utcnow()
        else:
            # Create new attendance record
            attendance = StudentAttendance(
                class_session_id=class_id,
                student_id=student_id,
                status=attendance_data.get('status', 'present'),
                arrival_time=attendance_data.get('arrival_time'),
                departure_time=attendance_data.get('departure_time'),
                notes=attendance_data.get('notes', ''),
                marked_by=current_user.id if current_user.is_authenticated else None
            )
            db.session.add(attendance)
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.attendance_marked = True
            session.attendance_marked_at = datetime.utcnow()
            session.update_compliance_status()
        
        db.session.commit()
        return True, f"Attendance marked as {attendance_data.get('status', 'present')}."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to mark attendance: {str(e)}"

def upload_class_recording(class_id, recording_data):
    """Upload class recording"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        if class_obj.status != 'completed':
            return False, "Can only upload recordings for completed classes."
        
        # Update recording link
        class_obj.recording_link = recording_data.get('recording_link')
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.recording_uploaded = True
            session.recording_uploaded_at = datetime.utcnow()
            session.update_compliance_status()
        
        db.session.commit()
        return True, "Class recording uploaded successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to upload recording: {str(e)}"

def submit_class_feedback(class_id, feedback_data):
    """Submit class feedback by tutor"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        if class_obj.status != 'completed':
            return False, "Can only submit feedback for completed classes."
        
        # Get appropriate feedback form
        enrollment = class_obj.enrollment
        from functions.helpers import assign_feedback_form
        form = assign_feedback_form(
            enrollment.student.department_id,
            class_obj.subject
        )
        
        if not form:
            return False, "No feedback form available."
        
        # Create feedback record
        feedback = ClassFeedback(
            class_session_id=class_id,
            tutor_id=current_user.id if current_user.is_authenticated else class_obj.tutor_id,
            form_template_id=form.id,
            overall_rating=feedback_data.get('overall_rating'),
            student_engagement=feedback_data.get('student_engagement'),
            class_completion=feedback_data.get('class_completion'),
            technical_issues=feedback_data.get('technical_issues', False),
            needs_followup=feedback_data.get('needs_followup', False),
            is_complete=True,
            submission_deadline=datetime.utcnow() + timedelta(hours=form.submission_deadline_hours if hasattr(form, 'submission_deadline_hours') else 24)
        )
        
        feedback.set_feedback_data(feedback_data)
        db.session.add(feedback)
        
        # Update session tracking
        session = ClassSession.query.filter_by(class_id=class_id).first()
        if session:
            session.feedback_submitted = True
            session.feedback_submitted_at = datetime.utcnow()
            session.update_compliance_status()
        
        # Update tutor's average rating
        if feedback_data.get('overall_rating'):
            tutor = class_obj.tutor
            tutor.update_feedback_rating(float(feedback_data['overall_rating']))
        
        db.session.commit()
        return True, "Class feedback submitted successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to submit feedback: {str(e)}"

def record_tutor_late_arrival(class_id, late_minutes):
    """Record tutor late arrival for penalty calculation"""
    try:
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found."
        
        from functions.helpers import calculate_late_penalty
        penalty_amount = calculate_late_penalty(class_obj.tutor_id, late_minutes)
        
        late_record = TutorLateArrival(
            tutor_id=class_obj.tutor_id,
            class_id=class_id,
            scheduled_time=datetime.combine(class_obj.class_date, class_obj.start_time),
            actual_arrival_time=class_obj.actual_start_time,
            late_minutes=late_minutes,
            penalty_amount=penalty_amount,
            recorded_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(late_record)
        
        # Send notification to finance coordinators
        from functions.notification_functions import send_late_arrival_notification
        send_late_arrival_notification(class_obj.tutor_id, late_minutes, class_id)
        
        db.session.commit()
        return True, f"Late arrival recorded: {late_minutes} minutes, penalty: ₹{penalty_amount}"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Failed to record late arrival: {str(e)}"

# Class querying and statistics functions

def get_classes_by_tutor(tutor_id, date_range=None, status=None):
    """Get all classes for a tutor"""
    query = Class.query.filter_by(tutor_id=tutor_id)
    
    if date_range:
        if date_range.get('start_date'):
            query = query.filter(Class.class_date >= date_range['start_date'])
        if date_range.get('end_date'):
            query = query.filter(Class.class_date <= date_range['end_date'])
    
    if status:
        query = query.filter_by(status=status)
    
    return query.order_by(Class.class_date.desc(), Class.start_time.desc()).all()

def get_classes_by_student(student_id, date_range=None, status=None):
    """Get all classes for a student"""
    enrollments = StudentEnrollment.query.filter_by(student_id=student_id).all()
    enrollment_ids = [e.id for e in enrollments]
    
    query = Class.query.filter(Class.enrollment_id.in_(enrollment_ids))
    
    if date_range:
        if date_range.get('start_date'):
            query = query.filter(Class.class_date >= date_range['start_date'])
        if date_range.get('end_date'):
            query = query.filter(Class.class_date <= date_range['end_date'])
    
    if status:
        query = query.filter_by(status=status)
    
    return query.order_by(Class.class_date.desc(), Class.start_time.desc()).all()

def get_classes_by_department(department_id, date_range=None):
    """Get all classes for a department"""
    query = Class.query.join(StudentEnrollment).join(Student).filter(
        Student.department_id == department_id
    )
    
    if date_range:
        if date_range.get('start_date'):
            query = query.filter(Class.class_date >= date_range['start_date'])
        if date_range.get('end_date'):
            query = query.filter(Class.class_date <= date_range['end_date'])
    
    return query.order_by(Class.class_date.desc(), Class.start_time.desc()).all()

def get_class_statistics():
    """Get class statistics for dashboard"""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    stats = {
        'total_classes': Class.query.count(),
        'completed_classes': Class.query.filter_by(status='completed').count(),
        'scheduled_classes': Class.query.filter_by(status='scheduled').count(),
        'cancelled_classes': Class.query.filter_by(status='cancelled').count(),
        'classes_today': Class.query.filter_by(class_date=today).count(),
        'classes_this_week': Class.query.filter(
            Class.class_date >= week_start,
            Class.class_date < week_start + timedelta(days=7)
        ).count(),
        'classes_this_month': Class.query.filter(
            Class.class_date >= month_start
        ).count(),
        'average_class_duration': get_average_class_duration(),
        'completion_rate': get_class_completion_rate(),
        'attendance_rate': get_average_attendance_rate()
    }
    
    return stats

def get_average_class_duration():
    """Calculate average class duration in minutes"""
    try:
        completed_classes = Class.query.filter_by(status='completed').all()
        if not completed_classes:
            return 0
        
        total_duration = 0
        for class_obj in completed_classes:
            if class_obj.actual_start_time and class_obj.actual_end_time:
                duration = (class_obj.actual_end_time - class_obj.actual_start_time).total_seconds() / 60
                total_duration += duration
        
        return round(total_duration / len(completed_classes), 1)
    except:
        return 0

def get_class_completion_rate():
    """Calculate class completion rate percentage"""
    total_classes = Class.query.filter(Class.status != 'scheduled').count()
    completed_classes = Class.query.filter_by(status='completed').count()
    
    if total_classes > 0:
        return round((completed_classes / total_classes) * 100, 1)
    return 0

def get_average_attendance_rate():
    """Calculate average attendance rate"""
    try:
        total_attendance = StudentAttendance.query.count()
        present_attendance = StudentAttendance.query.filter_by(status='present').count()
        
        if total_attendance > 0:
            return round((present_attendance / total_attendance) * 100, 1)
        return 0
    except:
        return 0

# Class generation functions

def generate_classes_from_enrollment(enrollment_id, weeks=4):
    """Generate class sessions from enrollment schedule"""
    try:
        enrollment = StudentEnrollment.query.get(enrollment_id)
        if not enrollment:
            return False, "Enrollment not found."
        
        schedule = enrollment.get_schedule()
        if not schedule:
            return False, "No schedule data found for this enrollment."
        
        start_date = enrollment.start_date
        end_date = enrollment.end_date or (start_date + timedelta(weeks=weeks))
        
        classes_created = 0
        current_date = start_date
        
        while current_date <= end_date:
            day_name = calendar.day_name[current_date.weekday()].lower()
            
            for schedule_item in schedule:
                if schedule_item['day'].lower() == day_name:
                    # Check if class already exists
                    existing_class = Class.query.filter(
                        Class.enrollment_id == enrollment_id,
                        Class.class_date == current_date,
                        Class.start_time == datetime.strptime(schedule_item['time'], '%H:%M').time()
                    ).first()
                    
                    if not existing_class:
                        # Create new class
                        start_time = datetime.strptime(schedule_item['time'], '%H:%M').time()
                        end_time = (datetime.combine(current_date, start_time) + 
                                   timedelta(minutes=enrollment.session_duration)).time()
                        
                        new_class = Class(
                            enrollment_id=enrollment_id,
                            tutor_id=enrollment.tutor_id,
                            subject=enrollment.subject,
                            class_date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            status='scheduled'
                        )
                        
                        db.session.add(new_class)
                        classes_created += 1
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        return True, f"Generated {classes_created} class sessions successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Class generation failed: {str(e)}"

def bulk_update_classes(class_ids, update_data):
    """Bulk update multiple classes"""
    try:
        classes = Class.query.filter(Class.id.in_(class_ids)).all()
        
        updateable_fields = ['status', 'topic_covered', 'homework_assigned', 'meeting_link']
        updated_count = 0
        
        for class_obj in classes:
            # Only update if class is in valid state
            if class_obj.status in ['scheduled', 'in_progress']:
                for field, value in update_data.items():
                    if field in updateable_fields:
                        setattr(class_obj, field, value)
                class_obj.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        return True, f"Updated {updated_count} classes successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Bulk update failed: {str(e)}"