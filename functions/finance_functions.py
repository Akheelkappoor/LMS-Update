# functions/finance_functions.py - COMPLETE IMPLEMENTATION

from models import db, StudentFee, FeeInstallment, TutorPayroll, ExpenseRecord, User, Student, TutorLateArrival, StudentEnrollment, Class
from flask_login import current_user
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract
import calendar

def get_financial_dashboard_data():
    """Get comprehensive financial dashboard data"""
    try:
        current_month = datetime.now().replace(day=1)
        current_year = datetime.now().year
        
        data = {
            # Revenue metrics
            'total_revenue': get_total_revenue(),
            'monthly_revenue': get_monthly_revenue(current_month),
            'pending_collections': get_pending_collections(),
            'collection_rate': get_collection_rate(),
            
            # Fee management
            'pending_fees': get_pending_fee_count(),
            'overdue_fees': get_overdue_fee_count(),
            'partial_payments': get_partial_payment_count(),
            'fee_breakdown': get_fee_breakdown(),
            
            # Payroll metrics
            'pending_payroll': get_pending_payroll_count(),
            'monthly_payroll_cost': get_monthly_payroll_cost(current_month),
            'tutor_payment_status': get_tutor_payment_status(),
            
            # Penalties and deductions
            'late_arrival_penalties': get_late_arrival_penalty_stats(current_month),
            'total_penalties_collected': get_total_penalties_collected(current_month),
            
            # Financial trends
            'revenue_trend': get_revenue_trend(6),  # Last 6 months
            'expense_trend': get_expense_trend(6),
            'profit_trend': get_profit_trend(6),
            
            # Quick stats
            'today_collections': get_today_collections(),
            'this_week_revenue': get_week_revenue(),
            'outstanding_amount': get_outstanding_amount(),
            
            # Recent transactions
            'recent_payments': get_recent_payments(10),
            'recent_expenses': get_recent_expenses(5),
            
            # Summary
            'financial_health': calculate_financial_health()
        }
        
        return data, "Financial dashboard data loaded successfully."
        
    except Exception as e:
        return {}, f"Error loading financial data: {str(e)}"

# Revenue Functions

def get_total_revenue():
    """Get total revenue from all paid fees"""
    total = db.session.query(func.sum(StudentFee.paid_amount)).filter(
        StudentFee.payment_status.in_(['paid', 'partial'])
    ).scalar()
    return float(total) if total else 0.0

def get_monthly_revenue(month_start):
    """Get revenue for specific month"""
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    total = db.session.query(func.sum(StudentFee.paid_amount)).filter(
        StudentFee.payment_date >= month_start.date(),
        StudentFee.payment_date <= month_end.date(),
        StudentFee.payment_status.in_(['paid', 'partial'])
    ).scalar()
    return float(total) if total else 0.0

def get_pending_collections():
    """Get total pending collections"""
    total = db.session.query(func.sum(StudentFee.pending_amount)).filter(
        StudentFee.payment_status.in_(['pending', 'partial'])
    ).scalar()
    return float(total) if total else 0.0

def get_collection_rate():
    """Calculate collection rate percentage"""
    total_fees = db.session.query(func.sum(StudentFee.amount)).scalar() or 0
    collected_fees = db.session.query(func.sum(StudentFee.paid_amount)).scalar() or 0
    
    if total_fees > 0:
        return round((collected_fees / total_fees) * 100, 2)
    return 0.0

def get_today_collections():
    """Get today's collections"""
    today = date.today()
    total = db.session.query(func.sum(StudentFee.paid_amount)).filter(
        StudentFee.payment_date == today,
        StudentFee.payment_status.in_(['paid', 'partial'])
    ).scalar()
    return float(total) if total else 0.0

def get_week_revenue():
    """Get this week's revenue"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    total = db.session.query(func.sum(StudentFee.paid_amount)).filter(
        StudentFee.payment_date >= week_start,
        StudentFee.payment_date <= today,
        StudentFee.payment_status.in_(['paid', 'partial'])
    ).scalar()
    return float(total) if total else 0.0

# Fee Management Functions

def get_pending_fee_count():
    """Get count of pending fees"""
    return StudentFee.query.filter_by(payment_status='pending').count()

def get_overdue_fee_count():
    """Get count of overdue fees"""
    today = date.today()
    return StudentFee.query.filter(
        StudentFee.payment_status == 'pending',
        StudentFee.due_date < today
    ).count()

def get_partial_payment_count():
    """Get count of partial payments"""
    return StudentFee.query.filter_by(payment_status='partial').count()

def get_outstanding_amount():
    """Get total outstanding amount (overdue + pending)"""
    return get_pending_collections()

def get_fee_breakdown():
    """Get fee breakdown by type"""
    breakdown = db.session.query(
        StudentFee.fee_type,
        func.count(StudentFee.id).label('count'),
        func.sum(StudentFee.amount).label('total_amount'),
        func.sum(StudentFee.paid_amount).label('paid_amount'),
        func.sum(StudentFee.pending_amount).label('pending_amount')
    ).group_by(StudentFee.fee_type).all()
    
    return [
        {
            'fee_type': row.fee_type,
            'count': row.count,
            'total_amount': float(row.total_amount or 0),
            'paid_amount': float(row.paid_amount or 0),
            'pending_amount': float(row.pending_amount or 0),
            'collection_rate': round((row.paid_amount / row.total_amount * 100) if row.total_amount else 0, 2)
        }
        for row in breakdown
    ]

# Payroll Functions

def get_pending_payroll_count():
    """Get count of pending payroll records"""
    return TutorPayroll.query.filter_by(payment_status='pending').count()

def get_monthly_payroll_cost(month_start):
    """Get total payroll cost for month"""
    year = month_start.year
    month = month_start.month
    
    total = db.session.query(func.sum(TutorPayroll.net_amount)).filter(
        TutorPayroll.year == year,
        TutorPayroll.month == month
    ).scalar()
    return float(total) if total else 0.0

def get_tutor_payment_status():
    """Get tutor payment status breakdown"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    status_breakdown = db.session.query(
        TutorPayroll.payment_status,
        func.count(TutorPayroll.id).label('count'),
        func.sum(TutorPayroll.net_amount).label('total_amount')
    ).filter(
        TutorPayroll.year == current_year,
        TutorPayroll.month == current_month
    ).group_by(TutorPayroll.payment_status).all()
    
    return [
        {
            'status': row.payment_status,
            'count': row.count,
            'total_amount': float(row.total_amount or 0)
        }
        for row in status_breakdown
    ]

# Penalty and Deduction Functions

def get_late_arrival_penalty_stats(month_start):
    """Get late arrival penalty statistics"""
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    penalties = db.session.query(
        func.count(TutorLateArrival.id).label('incident_count'),
        func.sum(TutorLateArrival.penalty_amount).label('total_penalties'),
        func.avg(TutorLateArrival.late_minutes).label('avg_late_minutes')
    ).filter(
        TutorLateArrival.recorded_at >= month_start,
        TutorLateArrival.recorded_at <= month_end
    ).first()
    
    return {
        'incident_count': penalties.incident_count or 0,
        'total_penalties': float(penalties.total_penalties or 0),
        'avg_late_minutes': round(float(penalties.avg_late_minutes or 0), 1)
    }

def get_total_penalties_collected(month_start):
    """Get total penalties collected in month"""
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    total = db.session.query(func.sum(TutorLateArrival.penalty_amount)).filter(
        TutorLateArrival.recorded_at >= month_start,
        TutorLateArrival.recorded_at <= month_end,
        TutorLateArrival.penalty_applied == True
    ).scalar()
    return float(total) if total else 0.0

# Trend Analysis Functions

def get_revenue_trend(months):
    """Get revenue trend for last N months"""
    trends = []
    current_date = datetime.now().replace(day=1)
    
    for i in range(months):
        month_start = current_date - timedelta(days=32*i)
        month_start = month_start.replace(day=1)
        revenue = get_monthly_revenue(month_start)
        
        trends.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'revenue': revenue
        })
    
    return list(reversed(trends))

def get_expense_trend(months):
    """Get expense trend for last N months"""
    trends = []
    current_date = datetime.now().replace(day=1)
    
    for i in range(months):
        month_start = current_date - timedelta(days=32*i)
        month_start = month_start.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Calculate expenses (payroll + other expenses)
        payroll_cost = get_monthly_payroll_cost(month_start)
        
        other_expenses = db.session.query(func.sum(ExpenseRecord.amount)).filter(
            ExpenseRecord.expense_date >= month_start.date(),
            ExpenseRecord.expense_date <= month_end.date(),
            ExpenseRecord.approval_status == 'approved'
        ).scalar() or 0
        
        total_expenses = payroll_cost + float(other_expenses)
        
        trends.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'expenses': total_expenses,
            'payroll': payroll_cost,
            'other_expenses': float(other_expenses)
        })
    
    return list(reversed(trends))

def get_profit_trend(months):
    """Get profit trend for last N months"""
    revenue_trends = get_revenue_trend(months)
    expense_trends = get_expense_trend(months)
    
    profit_trends = []
    for i in range(months):
        revenue = revenue_trends[i]['revenue']
        expenses = expense_trends[i]['expenses']
        profit = revenue - expenses
        
        profit_trends.append({
            'month': revenue_trends[i]['month'],
            'month_name': revenue_trends[i]['month_name'],
            'profit': profit,
            'profit_margin': round((profit / revenue * 100) if revenue > 0 else 0, 2)
        })
    
    return profit_trends

# Transaction Management Functions

def get_recent_payments(limit=10):
    """Get recent fee payments"""
    recent = StudentFee.query.filter(
        StudentFee.payment_status.in_(['paid', 'partial']),
        StudentFee.payment_date.isnot(None)
    ).order_by(StudentFee.payment_date.desc(), StudentFee.updated_at.desc()).limit(limit).all()
    
    return [
        {
            'id': fee.id,
            'student_name': fee.student.full_name if fee.student else 'Unknown',
            'amount': fee.paid_amount,
            'fee_type': fee.fee_type,
            'payment_date': fee.payment_date.strftime('%Y-%m-%d') if fee.payment_date else None,
            'payment_method': fee.payment_method,
            'transaction_id': fee.transaction_id
        }
        for fee in recent
    ]

def get_recent_expenses(limit=5):
    """Get recent expenses"""
    recent = ExpenseRecord.query.filter_by(
        approval_status='approved'
    ).order_by(ExpenseRecord.expense_date.desc()).limit(limit).all()
    
    return [
        {
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'category': expense.category,
            'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
            'created_by': expense.creator.full_name if expense.creator else 'Unknown'
        }
        for expense in recent
    ]

# Financial Health Calculation

def calculate_financial_health():
    """Calculate overall financial health score"""
    try:
        # Collection rate (40% weight)
        collection_rate = get_collection_rate()
        collection_score = min(collection_rate / 90 * 40, 40)  # 90% = perfect score
        
        # Overdue ratio (30% weight)
        total_pending = get_pending_collections()
        overdue_amount = db.session.query(func.sum(StudentFee.pending_amount)).filter(
            StudentFee.payment_status.in_(['pending', 'partial']),
            StudentFee.due_date < date.today()
        ).scalar() or 0
        
        overdue_ratio = (overdue_amount / total_pending * 100) if total_pending > 0 else 0
        overdue_score = max(30 - (overdue_ratio / 100 * 30), 0)  # Lower overdue = higher score
        
        # Revenue growth (20% weight)
        current_month = datetime.now().replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        current_revenue = get_monthly_revenue(current_month)
        last_revenue = get_monthly_revenue(last_month)
        
        growth_rate = ((current_revenue - last_revenue) / last_revenue * 100) if last_revenue > 0 else 0
        growth_score = min(max(growth_rate / 10 * 20, 0), 20)  # 10% growth = perfect score
        
        # Profit margin (10% weight)
        current_expenses = get_monthly_payroll_cost(current_month)
        profit_margin = ((current_revenue - current_expenses) / current_revenue * 100) if current_revenue > 0 else 0
        profit_score = min(profit_margin / 20 * 10, 10)  # 20% margin = perfect score
        
        total_score = collection_score + overdue_score + growth_score + profit_score
        
        # Determine health status
        if total_score >= 80:
            status = 'Excellent'
            color = 'success'
        elif total_score >= 60:
            status = 'Good'
            color = 'info'
        elif total_score >= 40:
            status = 'Fair'
            color = 'warning'
        else:
            status = 'Poor'
            color = 'danger'
        
        return {
            'score': round(total_score, 1),
            'status': status,
            'color': color,
            'components': {
                'collection': round(collection_score, 1),
                'overdue': round(overdue_score, 1),
                'growth': round(growth_score, 1),
                'profit': round(profit_score, 1)
            }
        }
        
    except Exception as e:
        return {
            'score': 0,
            'status': 'Unknown',
            'color': 'secondary',
            'components': {'collection': 0, 'overdue': 0, 'growth': 0, 'profit': 0}
        }

# Fee Processing Functions

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
            return False, f"Payment amount (₹{amount_paid}) cannot exceed pending amount (₹{fee.pending_amount})."
        
        # Process payment
        fee.mark_paid(
            amount_paid=amount_paid,
            payment_method=payment_method,
            transaction_id=transaction_id,
            processed_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.commit()
        
        # Send payment confirmation (if email system is set up)
        # send_payment_confirmation_email(fee, amount_paid)
        
        status_msg = "paid" if fee.payment_status == 'paid' else "partially paid"
        return True, f"Payment of ₹{amount_paid} processed successfully. Fee is now {status_msg}."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Payment processing failed: {str(e)}"

def apply_late_fee(fee_id, late_fee_amount, reason=""):
    """Apply late fee to student fee"""
    try:
        fee = StudentFee.query.get(fee_id)
        if not fee:
            return False, "Fee record not found."
        
        if late_fee_amount <= 0:
            return False, "Late fee amount must be greater than zero."
        
        fee.apply_late_fee(late_fee_amount)
        
        if reason:
            fee.notes = f"{fee.notes or ''}\nLate fee applied: {reason}".strip()
        
        db.session.commit()
        return True, f"Late fee of ₹{late_fee_amount} applied successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Late fee application failed: {str(e)}"

def apply_discount(fee_id, discount_amount, reason):
    """Apply discount to student fee"""
    try:
        fee = StudentFee.query.get(fee_id)
        if not fee:
            return False, "Fee record not found."
        
        if discount_amount <= 0:
            return False, "Discount amount must be greater than zero."
        
        if discount_amount > fee.pending_amount:
            return False, "Discount cannot exceed pending amount."
        
        fee.apply_discount(discount_amount, reason)
        db.session.commit()
        
        return True, f"Discount of ₹{discount_amount} applied successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Discount application failed: {str(e)}"

# Payroll Functions

def generate_tutor_payroll(tutor_id, month, year):
    """Generate payroll for a tutor for specific month/year"""
    try:
        # Check if payroll already exists
        existing = TutorPayroll.query.filter_by(
            tutor_id=tutor_id, month=month, year=year
        ).first()
        
        if existing:
            return False, "Payroll for this period already exists."
        
        tutor = User.query.get(tutor_id)
        if not tutor or tutor.role != 'tutor':
            return False, "Invalid tutor."
        
        # Get tutor's hourly rate
        tutor_profile = getattr(tutor, 'tutor_profile', None)
        hourly_rate = tutor_profile.hourly_rate if tutor_profile else 500.0  # Default rate
        
        # Calculate classes and hours for the month
        month_start = datetime(year, month, 1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        classes = Class.query.filter(
            Class.tutor_id == tutor_id,
            Class.class_date >= month_start.date(),
            Class.class_date <= month_end.date(),
            Class.status == 'completed'
        ).all()
        
        total_classes = len(classes)
        total_hours = sum([
            (datetime.combine(date.today(), class_obj.end_time) - 
             datetime.combine(date.today(), class_obj.start_time)).total_seconds() / 3600
            for class_obj in classes
        ])
        
        gross_amount = total_hours * hourly_rate
        
        # Calculate late arrival penalties
        penalties = db.session.query(func.sum(TutorLateArrival.penalty_amount)).filter(
            TutorLateArrival.tutor_id == tutor_id,
            extract('month', TutorLateArrival.recorded_at) == month,
            extract('year', TutorLateArrival.recorded_at) == year
        ).scalar() or 0
        
        # Create payroll record
        payroll = TutorPayroll(
            tutor_id=tutor_id,
            month=month,
            year=year,
            total_classes=total_classes,
            total_hours=total_hours,
            hourly_rate=hourly_rate,
            gross_amount=gross_amount,
            late_arrival_penalty=float(penalties),
            net_amount=gross_amount - float(penalties)
        )
        
        db.session.add(payroll)
        db.session.commit()
        
        return True, f"Payroll generated: ₹{payroll.net_amount} for {total_classes} classes."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Payroll generation failed: {str(e)}"

def process_tutor_payment(payroll_id, payment_data):
    """Process tutor payroll payment"""
    try:
        payroll = TutorPayroll.query.get(payroll_id)
        if not payroll:
            return False, "Payroll record not found."
        
        if payroll.payment_status == 'paid':
            return False, "Payroll already paid."
        
        payment_method = payment_data.get('payment_method')
        transaction_reference = payment_data.get('transaction_reference', '')
        
        payroll.mark_paid(
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            processed_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.commit()
        return True, f"Payment of ₹{payroll.net_amount} processed successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Payment processing failed: {str(e)}"

# Expense Management

def create_expense_record(expense_data):
    """Create new expense record"""
    try:
        expense = ExpenseRecord(
            category=expense_data['category'],
            subcategory=expense_data.get('subcategory'),
            description=expense_data['description'],
            amount=float(expense_data['amount']),
            expense_date=datetime.strptime(expense_data['expense_date'], '%Y-%m-%d').date(),
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(expense)
        db.session.commit()
        
        return expense, "Expense record created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Expense creation failed: {str(e)}"

def approve_expense(expense_id, approved_by_id):
    """Approve expense record"""
    try:
        expense = ExpenseRecord.query.get(expense_id)
        if not expense:
            return False, "Expense record not found."
        
        expense.approval_status = 'approved'
        expense.approved_by = approved_by_id
        expense.approved_at = datetime.utcnow()
        
        db.session.commit()
        return True, "Expense approved successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Expense approval failed: {str(e)}"