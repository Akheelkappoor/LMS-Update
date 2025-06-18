# functions/report_functions.py - COMPLETE IMPLEMENTATION

from models import db, User, Student, Class, StudentEnrollment, StudentAttendance, StudentFee, TutorPayroll, Department, TutorLateArrival, ClassFeedback
from flask_login import current_user
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract, case
import json

def generate_user_report(filters=None):
    """Generate comprehensive user report"""
    try:
        filters = filters or {}
        
        # Base query
        query = User.query.filter_by(is_active=True)
        
        # Apply filters
        if filters.get('role'):
            query = query.filter_by(role=filters['role'])
        
        if filters.get('department'):
            query = query.filter_by(department_id=filters['department'])
        
        if filters.get('approval_status'):
            if filters['approval_status'] == 'approved':
                query = query.filter_by(is_approved=True)
            elif filters['approval_status'] == 'pending':
                query = query.filter_by(is_approved=False)
        
        if filters.get('date_from'):
            query = query.filter(User.created_at >= datetime.strptime(filters['date_from'], '%Y-%m-%d'))
        
        if filters.get('date_to'):
            query = query.filter(User.created_at <= datetime.strptime(filters['date_to'], '%Y-%m-%d'))
        
        users = query.all()
        
        # Generate statistics
        total_users = len(users)
        role_breakdown = {}
        department_breakdown = {}
        approval_stats = {'approved': 0, 'pending': 0}
        
        for user in users:
            # Role breakdown
            role_breakdown[user.role] = role_breakdown.get(user.role, 0) + 1
            
            # Department breakdown
            dept_name = user.department.name if user.department else 'No Department'
            department_breakdown[dept_name] = department_breakdown.get(dept_name, 0) + 1
            
            # Approval stats
            if user.is_approved:
                approval_stats['approved'] += 1
            else:
                approval_stats['pending'] += 1
        
        # Recent activity
        recent_users = User.query.filter_by(is_active=True).order_by(User.created_at.desc()).limit(10).all()
        
        # Generate monthly registration trend
        monthly_trend = get_user_registration_trend(6)  # Last 6 months
        
        report_data = {
            'summary': {
                'total_users': total_users,
                'role_breakdown': role_breakdown,
                'department_breakdown': department_breakdown,
                'approval_stats': approval_stats
            },
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role,
                    'department': user.department.name if user.department else 'No Department',
                    'is_approved': user.is_approved,
                    'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None,
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
                }
                for user in users
            ],
            'recent_activity': [
                {
                    'id': user.id,
                    'full_name': user.full_name,
                    'role': user.role,
                    'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None
                }
                for user in recent_users
            ],
            'trends': {
                'monthly_registrations': monthly_trend
            },
            'filters_applied': filters,
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user.full_name if current_user.is_authenticated else 'System'
        }
        
        return report_data, "User report generated successfully."
        
    except Exception as e:
        return None, f"User report generation failed: {str(e)}"

def generate_student_report(filters=None):
    """Generate comprehensive student report"""
    try:
        filters = filters or {}
        
        # Base query
        query = Student.query.filter_by(status='active')
        
        # Apply filters
        if filters.get('grade'):
            query = query.filter_by(grade=filters['grade'])
        
        if filters.get('department'):
            query = query.filter_by(department_id=filters['department'])
        
        if filters.get('board'):
            query = query.filter_by(board=filters['board'])
        
        if filters.get('date_from'):
            query = query.filter(Student.created_at >= datetime.strptime(filters['date_from'], '%Y-%m-%d'))
        
        if filters.get('date_to'):
            query = query.filter(Student.created_at <= datetime.strptime(filters['date_to'], '%Y-%m-%d'))
        
        students = query.all()
        
        # Generate statistics
        total_students = len(students)
        grade_breakdown = {}
        department_breakdown = {}
        board_breakdown = {}
        enrollment_stats = {'active': 0, 'inactive': 0, 'completed': 0}
        
        for student in students:
            # Grade breakdown
            grade_breakdown[student.grade or 'Not Specified'] = grade_breakdown.get(student.grade or 'Not Specified', 0) + 1
            
            # Department breakdown
            dept_name = student.department.name if student.department else 'No Department'
            department_breakdown[dept_name] = department_breakdown.get(dept_name, 0) + 1
            
            # Board breakdown
            board_breakdown[student.board or 'Not Specified'] = board_breakdown.get(student.board or 'Not Specified', 0) + 1
            
            # Count active enrollments
            active_enrollments = sum(1 for enrollment in student.enrollments if enrollment.status == 'active')
            if active_enrollments > 0:
                enrollment_stats['active'] += 1
            else:
                enrollment_stats['inactive'] += 1
        
        # Fee collection statistics
        fee_stats = get_student_fee_statistics(students)
        
        # Performance metrics
        performance_stats = get_student_performance_statistics(students)
        
        report_data = {
            'summary': {
                'total_students': total_students,
                'grade_breakdown': grade_breakdown,
                'department_breakdown': department_breakdown,
                'board_breakdown': board_breakdown,
                'enrollment_stats': enrollment_stats,
                'fee_stats': fee_stats,
                'performance_stats': performance_stats
            },
            'students': [
                {
                    'id': student.id,
                    'student_id': student.student_id,
                    'full_name': student.full_name,
                    'email': student.email,
                    'grade': student.grade,
                    'school': student.school,
                    'board': student.board,
                    'department': student.department.name if student.department else 'No Department',
                    'active_enrollments': len([e for e in student.enrollments if e.status == 'active']),
                    'total_fees': sum(fee.amount for fee in student.fees),
                    'paid_fees': sum(fee.paid_amount for fee in student.fees),
                    'created_at': student.created_at.strftime('%Y-%m-%d') if student.created_at else None
                }
                for student in students
            ],
            'filters_applied': filters,
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user.full_name if current_user.is_authenticated else 'System'
        }
        
        return report_data, "Student report generated successfully."
        
    except Exception as e:
        return None, f"Student report generation failed: {str(e)}"

def generate_class_performance_report(date_range=None, filters=None):
    """Generate class performance report"""
    try:
        date_range = date_range or {}
        filters = filters or {}
        
        # Base query
        query = Class.query
        
        # Apply date range
        if date_range.get('start_date'):
            query = query.filter(Class.class_date >= datetime.strptime(date_range['start_date'], '%Y-%m-%d').date())
        
        if date_range.get('end_date'):
            query = query.filter(Class.class_date <= datetime.strptime(date_range['end_date'], '%Y-%m-%d').date())
        
        # Apply filters
        if filters.get('tutor_id'):
            query = query.filter_by(tutor_id=filters['tutor_id'])
        
        if filters.get('subject'):
            query = query.filter_by(subject=filters['subject'])
        
        if filters.get('status'):
            query = query.filter_by(status=filters['status'])
        
        if filters.get('department'):
            query = query.join(StudentEnrollment).join(Student).filter(Student.department_id == filters['department'])
        
        classes = query.all()
        
        # Generate statistics
        total_classes = len(classes)
        status_breakdown = {}
        subject_breakdown = {}
        tutor_performance = {}
        monthly_trends = {}
        
        for class_obj in classes:
            # Status breakdown
            status_breakdown[class_obj.status] = status_breakdown.get(class_obj.status, 0) + 1
            
            # Subject breakdown
            subject_breakdown[class_obj.subject] = subject_breakdown.get(class_obj.subject, 0) + 1
            
            # Tutor performance
            tutor_id = class_obj.tutor_id
            if tutor_id not in tutor_performance:
                tutor = class_obj.tutor
                tutor_performance[tutor_id] = {
                    'tutor_name': tutor.full_name if tutor else 'Unknown',
                    'total_classes': 0,
                    'completed_classes': 0,
                    'cancelled_classes': 0,
                    'subjects': set(),
                    'average_rating': 0,
                    'late_arrivals': 0
                }
            
            tutor_performance[tutor_id]['total_classes'] += 1
            tutor_performance[tutor_id]['subjects'].add(class_obj.subject)
            
            if class_obj.status == 'completed':
                tutor_performance[tutor_id]['completed_classes'] += 1
            elif class_obj.status == 'cancelled':
                tutor_performance[tutor_id]['cancelled_classes'] += 1
            
            # Monthly trends
            month_key = class_obj.class_date.strftime('%Y-%m')
            if month_key not in monthly_trends:
                monthly_trends[month_key] = {
                    'total': 0,
                    'completed': 0,
                    'cancelled': 0,
                    'completion_rate': 0
                }
            
            monthly_trends[month_key]['total'] += 1
            if class_obj.status == 'completed':
                monthly_trends[month_key]['completed'] += 1
            elif class_obj.status == 'cancelled':
                monthly_trends[month_key]['cancelled'] += 1
        
        # Calculate completion rates and ratings
        for tutor_id, stats in tutor_performance.items():
            if stats['total_classes'] > 0:
                stats['completion_rate'] = round((stats['completed_classes'] / stats['total_classes']) * 100, 1)
            
            # Convert set to list for JSON serialization
            stats['subjects'] = list(stats['subjects'])
            
            # Get average rating from feedback
            avg_rating = db.session.query(func.avg(ClassFeedback.overall_rating)).join(Class).filter(
                Class.tutor_id == tutor_id,
                ClassFeedback.overall_rating.isnot(None)
            ).scalar()
            stats['average_rating'] = round(float(avg_rating), 1) if avg_rating else 0
            
            # Get late arrival count
            late_count = TutorLateArrival.query.filter_by(tutor_id=tutor_id).count()
            stats['late_arrivals'] = late_count
        
        # Calculate monthly completion rates
        for month_data in monthly_trends.values():
            if month_data['total'] > 0:
                month_data['completion_rate'] = round((month_data['completed'] / month_data['total']) * 100, 1)
        
        # Overall metrics
        completion_rate = round((status_breakdown.get('completed', 0) / total_classes * 100), 1) if total_classes > 0 else 0
        cancellation_rate = round((status_breakdown.get('cancelled', 0) / total_classes * 100), 1) if total_classes > 0 else 0
        
        report_data = {
            'summary': {
                'total_classes': total_classes,
                'completion_rate': completion_rate,
                'cancellation_rate': cancellation_rate,
                'status_breakdown': status_breakdown,
                'subject_breakdown': subject_breakdown
            },
            'tutor_performance': list(tutor_performance.values()),
            'monthly_trends': [
                {
                    'month': month,
                    'month_name': datetime.strptime(month, '%Y-%m').strftime('%B %Y'),
                    **data
                }
                for month, data in sorted(monthly_trends.items())
                ],
            'classes': [
                {
                    'id': class_obj.id,
                    'subject': class_obj.subject,
                    'tutor_name': class_obj.tutor.full_name if class_obj.tutor else 'Unknown',
                    'student_name': class_obj.enrollment.student.full_name if class_obj.enrollment and class_obj.enrollment.student else 'Unknown',
                    'class_date': class_obj.class_date.strftime('%Y-%m-%d'),
                    'start_time': class_obj.start_time.strftime('%H:%M'),
                    'end_time': class_obj.end_time.strftime('%H:%M'),
                    'status': class_obj.status,
                    'duration_minutes': get_class_duration(class_obj),
                    'attendance_marked': has_attendance_marked(class_obj.id),
                    'feedback_submitted': has_feedback_submitted(class_obj.id)
                }
                for class_obj in classes[:100]  # Limit to 100 for performance
            ],
            'filters_applied': filters,
            'date_range': date_range,
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user.full_name if current_user.is_authenticated else 'System'
        }
        
        return report_data, "Class performance report generated successfully."
        
    except Exception as e:
        return None, f"Class performance report generation failed: {str(e)}"

def generate_financial_report(date_range=None, filters=None):
    """Generate comprehensive financial report"""
    try:
        date_range = date_range or {}
        filters = filters or {}
        
        # Set default date range if not provided
        if not date_range.get('start_date'):
            date_range['start_date'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_range.get('end_date'):
            date_range['end_date'] = datetime.now().strftime('%Y-%m-%d')
        
        start_date = datetime.strptime(date_range['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(date_range['end_date'], '%Y-%m-%d').date()
        
        # Revenue analysis
        revenue_data = get_revenue_analysis(start_date, end_date, filters)
        
        # Fee collection analysis
        fee_analysis = get_fee_collection_analysis(start_date, end_date, filters)
        
        # Payroll analysis
        payroll_analysis = get_payroll_analysis(start_date, end_date, filters)
        
        # Penalty analysis
        penalty_analysis = get_penalty_analysis(start_date, end_date, filters)
        
        # Trends
        monthly_trends = get_financial_trends(start_date, end_date)
        
        report_data = {
            'summary': {
                'total_revenue': revenue_data['total_revenue'],
                'total_collections': fee_analysis['total_collected'],
                'pending_collections': fee_analysis['pending_amount'],
                'collection_rate': fee_analysis['collection_rate'],
                'total_payroll': payroll_analysis['total_payroll'],
                'total_penalties': penalty_analysis['total_penalties'],
                'net_profit': revenue_data['total_revenue'] - payroll_analysis['total_payroll']
            },
            'revenue_analysis': revenue_data,
            'fee_analysis': fee_analysis,
            'payroll_analysis': payroll_analysis,
            'penalty_analysis': penalty_analysis,
            'trends': monthly_trends,
            'date_range': date_range,
            'filters_applied': filters,
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user.full_name if current_user.is_authenticated else 'System'
        }
        
        return report_data, "Financial report generated successfully."
        
    except Exception as e:
        return None, f"Financial report generation failed: {str(e)}"

def generate_attendance_report(date_range=None, filters=None):
    """Generate attendance report"""
    try:
        date_range = date_range or {}
        filters = filters or {}
        
        # Base query for classes in date range
        query = Class.query
        
        if date_range.get('start_date'):
            query = query.filter(Class.class_date >= datetime.strptime(date_range['start_date'], '%Y-%m-%d').date())
        
        if date_range.get('end_date'):
            query = query.filter(Class.class_date <= datetime.strptime(date_range['end_date'], '%Y-%m-%d').date())
        
        if filters.get('department'):
            query = query.join(StudentEnrollment).join(Student).filter(Student.department_id == filters['department'])
        
        classes = query.all()
        
        # Analyze attendance
        total_classes = len(classes)
        total_possible_attendance = 0
        total_present = 0
        total_absent = 0
        total_late = 0
        
        student_attendance = {}
        tutor_punctuality = {}
        daily_trends = {}
        
        for class_obj in classes:
            # Get attendance records for this class
            attendance_records = StudentAttendance.query.filter_by(class_session_id=class_obj.id).all()
            
            for record in attendance_records:
                total_possible_attendance += 1
                
                if record.status == 'present':
                    total_present += 1
                elif record.status == 'absent':
                    total_absent += 1
                elif record.status == 'late':
                    total_late += 1
                
                # Student-wise analysis
                student_id = record.student_id
                if student_id not in student_attendance:
                    student = record.student
                    student_attendance[student_id] = {
                        'student_name': student.full_name if student else 'Unknown',
                        'total_classes': 0,
                        'present': 0,
                        'absent': 0,
                        'late': 0,
                        'attendance_rate': 0
                    }
                
                student_attendance[student_id]['total_classes'] += 1
                student_attendance[student_id][record.status] += 1
            
            # Tutor punctuality analysis
            tutor_id = class_obj.tutor_id
            if tutor_id not in tutor_punctuality:
                tutor = class_obj.tutor
                tutor_punctuality[tutor_id] = {
                    'tutor_name': tutor.full_name if tutor else 'Unknown',
                    'total_classes': 0,
                    'on_time': 0,
                    'late_arrivals': 0,
                    'punctuality_rate': 0
                }
            
            tutor_punctuality[tutor_id]['total_classes'] += 1
            
            # Check if tutor was late
            late_arrival = TutorLateArrival.query.filter_by(class_id=class_obj.id).first()
            if late_arrival:
                tutor_punctuality[tutor_id]['late_arrivals'] += 1
            else:
                tutor_punctuality[tutor_id]['on_time'] += 1
            
            # Daily trends
            date_key = class_obj.class_date.strftime('%Y-%m-%d')
            if date_key not in daily_trends:
                daily_trends[date_key] = {
                    'date': date_key,
                    'total_classes': 0,
                    'total_attendance': 0,
                    'present': 0,
                    'absent': 0,
                    'attendance_rate': 0
                }
            
            daily_trends[date_key]['total_classes'] += 1
            daily_trends[date_key]['total_attendance'] += len(attendance_records)
            daily_trends[date_key]['present'] += len([r for r in attendance_records if r.status == 'present'])
            daily_trends[date_key]['absent'] += len([r for r in attendance_records if r.status == 'absent'])
        
        # Calculate attendance rates
        for student_data in student_attendance.values():
            if student_data['total_classes'] > 0:
                student_data['attendance_rate'] = round((student_data['present'] / student_data['total_classes']) * 100, 1)
        
        # Calculate punctuality rates
        for tutor_data in tutor_punctuality.values():
            if tutor_data['total_classes'] > 0:
                tutor_data['punctuality_rate'] = round((tutor_data['on_time'] / tutor_data['total_classes']) * 100, 1)
        
        # Calculate daily attendance rates
        for day_data in daily_trends.values():
            if day_data['total_attendance'] > 0:
                day_data['attendance_rate'] = round((day_data['present'] / day_data['total_attendance']) * 100, 1)
        
        # Overall statistics
        overall_attendance_rate = round((total_present / total_possible_attendance * 100), 1) if total_possible_attendance > 0 else 0
        
        report_data = {
            'summary': {
                'total_classes': total_classes,
                'total_possible_attendance': total_possible_attendance,
                'total_present': total_present,
                'total_absent': total_absent,
                'total_late': total_late,
                'overall_attendance_rate': overall_attendance_rate
            },
            'student_attendance': list(student_attendance.values()),
            'tutor_punctuality': list(tutor_punctuality.values()),
            'daily_trends': list(daily_trends.values()),
            'date_range': date_range,
            'filters_applied': filters,
            'generated_at': datetime.now().isoformat(),
            'generated_by': current_user.full_name if current_user.is_authenticated else 'System'
        }
        
        return report_data, "Attendance report generated successfully."
        
    except Exception as e:
        return None, f"Attendance report generation failed: {str(e)}"

# Helper functions for report generation

def get_user_registration_trend(months):
    """Get user registration trend for last N months"""
    trends = []
    current_date = datetime.now().replace(day=1)
    
    for i in range(months):
        month_start = current_date - timedelta(days=32*i)
        month_start = month_start.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = User.query.filter(
            User.created_at >= month_start,
            User.created_at <= month_end,
            User.is_active == True
        ).count()
        
        trends.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'registrations': count
        })
    
    return list(reversed(trends))

def get_student_fee_statistics(students):
    """Get fee statistics for students"""
    total_fees = 0
    paid_fees = 0
    pending_fees = 0
    overdue_fees = 0
    
    today = date.today()
    
    for student in students:
        for fee in student.fees:
            total_fees += fee.amount
            paid_fees += fee.paid_amount
            pending_fees += fee.pending_amount
            
            if fee.payment_status == 'pending' and fee.due_date < today:
                overdue_fees += fee.pending_amount
    
    return {
        'total_fees': total_fees,
        'paid_fees': paid_fees,
        'pending_fees': pending_fees,
        'overdue_fees': overdue_fees,
        'collection_rate': round((paid_fees / total_fees * 100), 1) if total_fees > 0 else 0
    }

def get_student_performance_statistics(students):
    """Get performance statistics for students"""
    total_enrollments = 0
    active_enrollments = 0
    completed_enrollments = 0
    
    for student in students:
        for enrollment in student.enrollments:
            total_enrollments += 1
            if enrollment.status == 'active':
                active_enrollments += 1
            elif enrollment.status == 'completed':
                completed_enrollments += 1
    
    return {
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'completion_rate': round((completed_enrollments / total_enrollments * 100), 1) if total_enrollments > 0 else 0
    }

def get_class_duration(class_obj):
    """Calculate class duration in minutes"""
    if class_obj.actual_start_time and class_obj.actual_end_time:
        duration = (class_obj.actual_end_time - class_obj.actual_start_time).total_seconds() / 60
        return int(duration)
    else:
        # Use scheduled duration
        start_dt = datetime.combine(date.today(), class_obj.start_time)
        end_dt = datetime.combine(date.today(), class_obj.end_time)
        duration = (end_dt - start_dt).total_seconds() / 60
        return int(duration)

def has_attendance_marked(class_id):
    """Check if attendance is marked for class"""
    return StudentAttendance.query.filter_by(class_session_id=class_id).count() > 0

def has_feedback_submitted(class_id):
    """Check if feedback is submitted for class"""
    return ClassFeedback.query.filter_by(class_session_id=class_id).count() > 0

def get_revenue_analysis(start_date, end_date, filters):
    """Get revenue analysis for date range"""
    query = StudentFee.query.filter(
        StudentFee.payment_date >= start_date,
        StudentFee.payment_date <= end_date,
        StudentFee.payment_status.in_(['paid', 'partial'])
    )
    
    if filters.get('department'):
        query = query.join(Student).filter(Student.department_id == filters['department'])
    
    fees = query.all()
    
    total_revenue = sum(fee.paid_amount for fee in fees)
    fee_type_breakdown = {}
    
    for fee in fees:
        fee_type_breakdown[fee.fee_type] = fee_type_breakdown.get(fee.fee_type, 0) + fee.paid_amount
    
    return {
        'total_revenue': total_revenue,
        'fee_type_breakdown': fee_type_breakdown,
        'transaction_count': len(fees)
    }

def get_fee_collection_analysis(start_date, end_date, filters):
    """Get fee collection analysis"""
    # All fees in date range
    query = StudentFee.query.filter(
        StudentFee.due_date >= start_date,
        StudentFee.due_date <= end_date
    )
    
    if filters.get('department'):
        query = query.join(Student).filter(Student.department_id == filters['department'])
    
    fees = query.all()
    
    total_amount = sum(fee.amount for fee in fees)
    total_collected = sum(fee.paid_amount for fee in fees)
    pending_amount = sum(fee.pending_amount for fee in fees)
    overdue_amount = sum(fee.pending_amount for fee in fees if fee.due_date < date.today() and fee.payment_status in ['pending', 'partial'])
    
    collection_rate = round((total_collected / total_amount * 100), 1) if total_amount > 0 else 0
    
    return {
        'total_amount': total_amount,
        'total_collected': total_collected,
        'pending_amount': pending_amount,
        'overdue_amount': overdue_amount,
        'collection_rate': collection_rate
    }

def get_payroll_analysis(start_date, end_date, filters):
    """Get payroll analysis"""
    start_year = start_date.year
    end_year = end_date.year
    start_month = start_date.month
    end_month = end_date.month
    
    query = TutorPayroll.query.filter(
        or_(
            and_(TutorPayroll.year == start_year, TutorPayroll.month >= start_month),
            and_(TutorPayroll.year == end_year, TutorPayroll.month <= end_month),
            and_(TutorPayroll.year > start_year, TutorPayroll.year < end_year)
        )
    )
    
    if filters.get('department'):
        query = query.join(User).filter(User.department_id == filters['department'])
    
    payrolls = query.all()
    
    total_payroll = sum(payroll.net_amount for payroll in payrolls)
    total_gross = sum(payroll.gross_amount for payroll in payrolls)
    total_deductions = sum((payroll.late_arrival_penalty or 0) + (payroll.other_deductions or 0) for payroll in payrolls)
    
    return {
        'total_payroll': total_payroll,
        'total_gross': total_gross,
        'total_deductions': total_deductions,
        'payroll_count': len(payrolls)
    }

def get_penalty_analysis(start_date, end_date, filters):
    """Get penalty analysis"""
    query = TutorLateArrival.query.filter(
        func.date(TutorLateArrival.recorded_at) >= start_date,
        func.date(TutorLateArrival.recorded_at) <= end_date
    )
    
    if filters.get('department'):
        query = query.join(User).filter(User.department_id == filters['department'])
    
    penalties = query.all()
    
    total_penalties = sum(penalty.penalty_amount for penalty in penalties)
    total_incidents = len(penalties)
    avg_late_minutes = sum(penalty.late_minutes for penalty in penalties) / total_incidents if total_incidents > 0 else 0
    
    return {
        'total_penalties': total_penalties,
        'total_incidents': total_incidents,
        'avg_late_minutes': round(avg_late_minutes, 1)
    }

def get_financial_trends(start_date, end_date):
    """Get financial trends month by month"""
    trends = []
    current = start_date.replace(day=1)
    end = end_date.replace(day=1)
    
    while current <= end:
        month_end = (current + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Revenue for month
        revenue = db.session.query(func.sum(StudentFee.paid_amount)).filter(
            StudentFee.payment_date >= current,
            StudentFee.payment_date <= month_end,
            StudentFee.payment_status.in_(['paid', 'partial'])
        ).scalar() or 0
        
        # Payroll for month
        payroll = db.session.query(func.sum(TutorPayroll.net_amount)).filter(
            TutorPayroll.year == current.year,
            TutorPayroll.month == current.month
        ).scalar() or 0
        
        trends.append({
            'month': current.strftime('%Y-%m'),
            'month_name': current.strftime('%B %Y'),
            'revenue': float(revenue),
            'payroll': float(payroll),
            'profit': float(revenue) - float(payroll)
        })
        
        current = (current + timedelta(days=32)).replace(day=1)
    
    return trends

def export_report_data(report_data, format='json'):
    """Export report data in specified format"""
    try:
        if format == 'json':
            import json
            return json.dumps(report_data, indent=2, default=str), "application/json"
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            
            # For CSV, we'll export the main data table
            if 'users' in report_data:
                # User report
                writer = csv.DictWriter(output, fieldnames=['username', 'full_name', 'email', 'role', 'department', 'is_approved', 'created_at'])
                writer.writeheader()
                writer.writerows(report_data['users'])
            
            elif 'students' in report_data:
                # Student report
                writer = csv.DictWriter(output, fieldnames=['student_id', 'full_name', 'grade', 'school', 'board', 'department', 'active_enrollments'])
                writer.writeheader()
                writer.writerows(report_data['students'])
            
            elif 'classes' in report_data:
                # Class report
                writer = csv.DictWriter(output, fieldnames=['subject', 'tutor_name', 'student_name', 'class_date', 'status', 'duration_minutes'])
                writer.writeheader()
                writer.writerows(report_data['classes'])
            
            return output.getvalue(), "text/csv"
        
        else:
            return None, "Unsupported format"
            
    except Exception as e:
        return None, f"Export failed: {str(e)}"