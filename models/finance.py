# models/finance.py - FIXED FINANCE MODELS WITH PROPER RELATIONSHIPS

from datetime import datetime, date
import json
from . import db

class StudentFee(db.Model):
    """Student fee management model"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('student_enrollment.id'))
    
    # Fee details
    fee_type = db.Column(db.String(50), nullable=False)  # tuition, registration, material, etc.
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    
    # Due dates and payment
    due_date = db.Column(db.Date, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, waived
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))  # cash, card, upi, bank_transfer
    transaction_id = db.Column(db.String(100))
    
    # Additional charges
    late_fee = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    discount_reason = db.Column(db.String(200))
    
    # Payment tracking
    paid_amount = db.Column(db.Float, default=0.0)
    pending_amount = db.Column(db.Float)
    
    # Metadata
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships - FIXED
    enrollment = db.relationship('StudentEnrollment', backref='fees')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_fees')
    processor = db.relationship('User', foreign_keys=[processed_by], backref='processed_fees')
    installments = db.relationship('FeeInstallment', backref='student_fee', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.pending_amount is None:
            self.pending_amount = self.amount
    
    @property
    def total_amount(self):
        """Calculate total amount including late fees minus discount"""
        return self.amount + (self.late_fee or 0) - (self.discount or 0)
    
    @property
    def is_overdue(self):
        """Check if fee is overdue"""
        return self.payment_status == 'pending' and self.due_date < date.today()
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0
    
    def mark_paid(self, amount_paid, payment_method, transaction_id=None, processed_by=None):
        """Mark fee as paid"""
        self.paid_amount += amount_paid
        self.pending_amount = max(0, self.total_amount - self.paid_amount)
        
        if self.pending_amount <= 0:
            self.payment_status = 'paid'
            self.payment_date = date.today()
        else:
            self.payment_status = 'partial'
        
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.processed_by = processed_by
        self.updated_at = datetime.utcnow()
    
    def apply_late_fee(self, late_fee_amount):
        """Apply late fee"""
        self.late_fee = (self.late_fee or 0) + late_fee_amount
        self.pending_amount = self.total_amount - self.paid_amount
        self.updated_at = datetime.utcnow()
    
    def apply_discount(self, discount_amount, reason):
        """Apply discount"""
        self.discount = (self.discount or 0) + discount_amount
        self.discount_reason = reason
        self.pending_amount = self.total_amount - self.paid_amount
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<StudentFee {self.fee_type}: ₹{self.amount}>'


class FeeInstallment(db.Model):
    """Fee installment for split payments"""
    id = db.Column(db.Integer, primary_key=True)
    student_fee_id = db.Column(db.Integer, db.ForeignKey('student_fee.id'), nullable=False)
    
    # Installment details
    installment_number = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    # Payment status
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, overdue
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    processor = db.relationship('User', foreign_keys=[processed_by])
    
    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        return self.payment_status == 'pending' and self.due_date < date.today()
    
    def mark_paid(self, payment_method, transaction_id=None, processed_by=None):
        """Mark installment as paid"""
        self.payment_status = 'paid'
        self.payment_date = date.today()
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.processed_by = processed_by
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<FeeInstallment {self.installment_number}: ₹{self.amount}>'


class TutorPayroll(db.Model):
    """Tutor payroll management"""
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Payroll period
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    
    # Earnings breakdown
    total_classes = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Float, default=0.0)
    hourly_rate = db.Column(db.Float, nullable=False)
    gross_amount = db.Column(db.Float, default=0.0)
    
    # Deductions
    late_arrival_penalty = db.Column(db.Float, default=0.0)
    other_deductions = db.Column(db.Float, default=0.0)
    deduction_notes = db.Column(db.Text)
    
    # Bonuses and additions
    bonus_amount = db.Column(db.Float, default=0.0)
    bonus_reason = db.Column(db.String(200))
    
    # Final calculation
    net_amount = db.Column(db.Float, default=0.0)
    
    # Payment details
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, on_hold
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    transaction_reference = db.Column(db.String(100))
    
    # Tax information
    tax_deducted = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.0)
    
    # Metadata
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    
    # Relationships
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='payroll_records')
    processor = db.relationship('User', foreign_keys=[processed_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def calculate_net_amount(self):
        """Calculate net payroll amount"""
        self.net_amount = (
            self.gross_amount + 
            (self.bonus_amount or 0) - 
            (self.late_arrival_penalty or 0) - 
            (self.other_deductions or 0) - 
            (self.tax_deducted or 0)
        )
        return self.net_amount
    
    def mark_paid(self, payment_method, transaction_reference, processed_by):
        """Mark payroll as paid"""
        self.payment_status = 'paid'
        self.payment_date = date.today()
        self.payment_method = payment_method
        self.transaction_reference = transaction_reference
        self.processed_by = processed_by
    
    @property
    def payroll_period(self):
        """Get formatted payroll period"""
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return f"{months[self.month - 1]} {self.year}"
    
    def __repr__(self):
        return f'<TutorPayroll {self.tutor.full_name}: {self.payroll_period}>'


class ExpenseRecord(db.Model):
    """System expense tracking"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Expense details
    category = db.Column(db.String(50), nullable=False)  # infrastructure, salaries, marketing, etc.
    subcategory = db.Column(db.String(50))
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    
    # Date and approval
    expense_date = db.Column(db.Date, nullable=False)
    approval_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    
    # Payment tracking
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, reimbursed
    payment_method = db.Column(db.String(50))
    receipt_number = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='expense_records')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<ExpenseRecord {self.category}: ₹{self.amount}>'