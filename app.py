# app.py - FIXED VERSION with Complete End-to-End Functionality

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, secrets
from flask_mail import Mail
from config import Config
from email_utils import EmailService, mail

# Import all models
from models import *

# Import all functions
from functions import *

# If update_user is not in functions.py, define a stub here or import it directly:
from functions import update_user

# If delete_user is not in functions.py, define a stub here or import it directly:
from functions import delete_user

from dotenv import load_dotenv
load_dotenv(override=True)

# Define allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, filename, folder):
    """Handle file upload to a specific folder"""
    try:
        # Create upload folder if it doesn't exist
        upload_folder = os.path.join(app.static_folder, 'uploads', folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Return the relative path for database storage
        return f'uploads/{folder}/{filename}'
    except Exception as e:
        print(f"File upload error: {str(e)}")
        return None

# Initialize Flask app
app = Flask(__name__)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'akheel@i2global.co.in'
app.config['MAIL_PASSWORD'] = 'gvlk duto osfi lxub'
app.config['MAIL_DEFAULT_SENDER'] = 'akheel@i2global.co.in'

mail.init_app(app)
app.config.from_object(Config)
Config.init_app(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================================
# AUTHENTICATION ROUTES
# ===================================

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login - FIXED with proper session handling"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user, error = authenticate_user(email, password)
        
        if user:
            # Use Flask-Login's login_user function directly
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash(error, 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout - FIXED with proper session cleanup"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - FIXED with complete validation"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        form_data = dict(request.form)
        
        user, error = register_new_user(form_data)
        
        if user:
            flash('Registration successful! Please wait for admin approval.', 'success')
            return redirect(url_for('login'))
        else:
            flash(error, 'danger')
    
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('auth/register.html', departments=departments)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request - FIXED with proper token handling"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = generate_reset_token()
            save_reset_token(user, token)
            send_password_reset_email(user, token)
            flash('Password reset instructions sent to your email.', 'success')
        else:
            flash('If an account exists with that email, you will receive reset instructions.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset - FIXED with token verification"""
    user = verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        success, message = reset_user_password(user, password)
        
        if success:
            flash('Password reset successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/reset_password.html', token=token)

# ===================================
# DASHBOARD ROUTES - FIXED
# ===================================

@app.route('/dashboard')
@login_required
@approved_required
@active_required
def dashboard():
    """Main dashboard - FIXED with proper data binding"""
    try:
        dashboard_data = get_user_dashboard_data(current_user)
        
        if current_user.role == 'superadmin':
            return render_template('dashboard/superadmin.html', data=dashboard_data)
        elif current_user.role == 'admin':
            return render_template('dashboard/admin.html', stats=dashboard_data)
        elif current_user.role == 'coordinator':
            return render_template('dashboard/coordinator.html', stats=dashboard_data)
        elif current_user.role == 'tutor':
            return render_template('dashboard/tutor.html', stats=dashboard_data)
        elif current_user.role == 'finance_coordinator':
            return render_template('finance/dashboard.html', stats=dashboard_data)
        else:
            return render_template('dashboard.html', data=dashboard_data)
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'danger')
        return render_template('dashboard.html', data={})

# ===================================
# USER MANAGEMENT ROUTES - FIXED
# ===================================

@app.route('/users')
@login_required
@coordinator_required
def users():
    """View all users - FIXED with proper filtering"""
    search_term = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    department_filter = request.args.get('department', '')
    
    try:
        # Get users based on filters
        if search_term:
            users_list = search_users(search_term)
        elif role_filter:
            users_list = get_users_by_role(role_filter)
        elif department_filter:
            users_list = get_users_by_department(int(department_filter))
        else:
            # Base query with role-based filtering
            if current_user.role == 'coordinator':
                users_list = get_users_by_department(current_user.department_id)
            else:
                users_list = User.query.filter_by(is_active=True).all()
        
        departments = Department.query.filter_by(is_active=True).all()
        user_stats = get_user_statistics()
        
        return render_template('users/list.html', 
                             users=users_list, 
                             departments=departments,
                             stats=user_stats,
                             current_search=search_term,
                             current_role=role_filter,
                             current_department=department_filter)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'danger')
        return render_template('users/list.html', users=[], departments=[], stats={})

@app.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user_route():
    """Create new user - FIXED with complete functionality"""
    if request.method == 'POST':
        user_data = dict(request.form)
        
        # Handle multiple permissions from checkboxes
        permissions = request.form.getlist('permissions')
        if permissions:
            user_data['permissions'] = permissions
        
        user, password_or_error = create_user(user_data)
        
        if user:
            # Send welcome email
            try:
                send_welcome_email(user, password_or_error)
            except:
                pass  # Don't fail if email doesn't work
            
            flash(f'User {user.full_name} created successfully! Password: {password_or_error}', 'success')
            return redirect(url_for('users'))
        else:
            flash(password_or_error, 'danger')  # Contains error message
    
    departments = Department.query.filter_by(is_active=True).all()
    available_permissions = get_available_permissions()
    
    return render_template('users/create.html', 
                         departments=departments,
                         available_permissions=available_permissions)

@app.route('/users/<int:id>')
@login_required
def view_user(id):
    """View user details - FIXED with permission checking"""
    user = User.query.get_or_404(id)
    
    # Check permissions
    if current_user.role not in ['superadmin', 'admin']:
        if current_user.role == 'coordinator' and user.department_id != current_user.department_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('users'))
        elif current_user.id != id:
            flash('Access denied.', 'danger')
            return redirect(url_for('dashboard'))
    
    return render_template('users/view.html', user=user)

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit user - FIXED with proper update handling"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user_data = dict(request.form)
        
        # Handle permissions
        permissions = request.form.getlist('permissions')
        if permissions:
            user_data['permissions'] = permissions
        
        success, message = update_user(id, user_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('view_user', id=id))
        else:
            flash(message, 'danger')
    
    departments = Department.query.filter_by(is_active=True).all()
    available_permissions = get_available_permissions()
    
    return render_template('users/edit.html',
                         user=user,
                         departments=departments,
                         available_permissions=available_permissions)

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_route(id):
    """Delete user - FIXED with proper error handling"""
    success, message = delete_user(id)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('users'))

@app.route('/users/pending')
@login_required
@admin_required
def pending_users():
    """View pending approvals - FIXED with complete data"""
    pending = UserApproval.query.filter_by(status='pending').order_by(UserApproval.requested_at.desc()).all()
    return render_template('users/pending.html', approvals=pending)

@app.route('/users/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user_route(user_id):
    """Approve user - FIXED with complete workflow"""
    comments = request.form.get('comments', '')
    success, message = approve_user_account(user_id, current_user.id, comments)
    
    if success:
        user = User.query.get(user_id)
        temp_password = secrets.token_urlsafe(8)
        user.set_password(temp_password)
        db.session.commit()
        
        try:
            send_welcome_email(user, temp_password)
            send_approval_notification(user, True)
        except:
            pass  # Don't fail if email doesn't work
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('pending_users'))

@app.route('/users/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user_route(user_id):
    """Reject user - FIXED with notification"""
    reason = request.form.get('reason', '')
    success, message = reject_user_account(user_id, current_user.id, reason)
    
    if success:
        user = User.query.get(user_id)
        try:
            send_approval_notification(user, False, reason)
        except:
            pass  # Don't fail if email doesn't work
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('pending_users'))

# ===================================
# STUDENT MANAGEMENT ROUTES - FIXED
# ===================================

@app.route('/students')
@login_required
@coordinator_required
def students():
    """View all students - FIXED with proper filtering"""
    search_term = request.args.get('search', '')
    grade_filter = request.args.get('grade', '')
    status_filter = request.args.get('status', '')
    
    try:
        # Get students based on role and filters
        if current_user.role == 'coordinator':
            students_list = get_students_by_department(current_user.department_id)
        else:
            students_list = Student.query.filter_by(status='active').all()
        
        # Apply search filter
        if search_term:
            students_list = search_students(search_term)
        
        # Apply other filters
        if grade_filter:
            students_list = [s for s in students_list if s.grade == grade_filter]
        
        if status_filter:
            students_list = [s for s in students_list if s.status == status_filter]
        
        return render_template('students/list.html', 
                             students=students_list,
                             current_search=search_term,
                             current_grade=grade_filter,
                             current_status=status_filter)
    except Exception as e:
        flash(f'Error loading students: {str(e)}', 'danger')
        return render_template('students/list.html', students=[])

@app.route('/students/create', methods=['GET', 'POST'])
@login_required
@coordinator_required
def create_student():
    """Create new student - FIXED with complete validation"""
    if request.method == 'POST':
        student_data = dict(request.form)
        
        student, message = create_student(student_data)
        
        if student:
            flash(f'Student {student.full_name} created successfully!', 'success')
            return redirect(url_for('students'))
        else:
            flash(message, 'danger')
    
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('students/create.html', departments=departments)

@app.route('/students/<int:id>')
@login_required
@coordinator_required
def view_student(id):
    """View student details - FIXED with complete information"""
    student = Student.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    # Get student's enrollments and classes
    enrollments = student.enrollments
    fees = StudentFee.query.filter_by(student_id=student.id).all()
    
    return render_template('students/view.html', 
                         student=student,
                         enrollments=enrollments,
                         fees=fees)

# ===================================
# CLASS MANAGEMENT ROUTES - FIXED
# ===================================

@app.route('/classes')
@login_required
def classes():
    """View classes - FIXED with role-based filtering"""
    try:
        if current_user.role == 'tutor':
            classes_list = get_classes_by_tutor(current_user.id)
        elif current_user.role == 'coordinator':
            # Get classes for coordinator's department
            classes_list = Class.query.join(StudentEnrollment).join(Student).filter(
                Student.department_id == current_user.department_id
            ).all()
        else:
            classes_list = Class.query.all()
        
        return render_template('classes/list.html', classes=classes_list)
    except Exception as e:
        flash(f'Error loading classes: {str(e)}', 'danger')
        return render_template('classes/list.html', classes=[])

@app.route('/schedule')
@login_required
def schedule():
    """Schedule view - FIXED with proper data loading"""
    try:
        if current_user.role == 'tutor':
            classes_list = get_classes_by_tutor(current_user.id)
        else:
            classes_list = Class.query.filter(
                Class.class_date >= datetime.now().date()
            ).order_by(Class.class_date, Class.start_time).all()
        
        return render_template('schedule/calendar.html', classes=classes_list)
    except Exception as e:
        flash(f'Error loading schedule: {str(e)}', 'danger')
        return render_template('schedule/calendar.html', classes=[])

# ===================================
# FINANCE ROUTES - FIXED
# ===================================

@app.route('/finance')
@login_required
@finance_required
def finance_dashboard():
    """Finance dashboard - FIXED with error handling"""
    try:
        dashboard_data, message = get_financial_dashboard_data()
        return render_template('finance/dashboard.html', stats=dashboard_data)
    except Exception as e:
        flash(f'Finance dashboard error: {str(e)}', 'danger')
        return render_template('finance/dashboard.html', stats={})

@app.route('/finance/fees')
@login_required
@finance_required
def student_fees():
    """View student fees - FIXED with proper data"""
    try:
        fees = StudentFee.query.order_by(StudentFee.due_date.desc()).all()
        return render_template('finance/fees.html', fees=fees)
    except Exception as e:
        flash(f'Error loading fees: {str(e)}', 'danger')
        return render_template('finance/fees.html', fees=[])

@app.route('/finance/fees/<int:id>/pay', methods=['POST'])
@login_required
@finance_required
def process_payment_route(id):
    """Process fee payment - FIXED with validation"""
    payment_data = dict(request.form)
    
    success, message = process_fee_payment(id, payment_data)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('student_fees'))

# ===================================
# REPORTS ROUTES - FIXED
# ===================================

@app.route('/reports')
@login_required
def reports():
    """Reports dashboard - FIXED with role-based access"""
    return render_template('reports/index.html')

@app.route('/reports/users')
@login_required
@admin_required
def user_report():
    """User report - FIXED with proper data generation"""
    try:
        filters = dict(request.args)
        report_data, message = generate_user_report(filters)
        return render_template('reports/users.html', report=report_data)
    except Exception as e:
        flash(f'Report generation error: {str(e)}', 'danger')
        return render_template('reports/users.html', report={})

# ===================================
# PROFILE ROUTES - FIXED
# ===================================

@app.route('/profile')
@login_required
def profile():
    """User profile - FIXED with complete data"""
    return render_template('users/profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit profile - FIXED with validation"""
    if request.method == 'POST':
        profile_data = dict(request.form)
        
        success, message = update_user_profile(current_user.id, profile_data)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('profile'))
    
    return render_template('users/edit_profile.html')

@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password - FIXED with proper validation"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        success, message = change_user_password(current_user, current_password, new_password)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('profile'))
    
    return render_template('users/change_password.html')

# ===================================
# FORM ROUTES - FIXED
# ===================================

@app.route('/forms')
@login_required
@admin_required
def forms():
    """View forms - FIXED with proper data loading"""
    try:
        forms_list = FormTemplate.query.order_by(FormTemplate.created_at.desc()).all()
        return render_template('forms/list.html', forms=forms_list)
    except Exception as e:
        flash(f'Error loading forms: {str(e)}', 'danger')
        return render_template('forms/list.html', forms=[])

@app.route('/forms/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_form():
    """Create form - FIXED with complete functionality"""
    if request.method == 'POST':
        form_data = dict(request.form)
        
        # Handle JSON fields
        if 'fields' in form_data:
            try:
                form_data['fields'] = json.loads(form_data['fields'])
            except:
                form_data['fields'] = []
        
        form_template, message = create_form_template(form_data)
        
        if form_template:
            flash(message, 'success')
            return redirect(url_for('forms'))
        else:
            flash(message, 'danger')
    
    return render_template('forms/create.html')

# ===================================
# API ENDPOINTS - FIXED
# ===================================

@app.route('/api/forms/<int:form_id>/preview')
@login_required
def api_preview_form(form_id):
    """API endpoint for form preview - FIXED"""
    try:
        form_template = FormTemplate.query.get_or_404(form_id)
        fields = form_template.get_fields()
        
        return jsonify({
            'form': {
                'name': form_template.name,
                'description': form_template.description,
                'fields': fields
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/search')
@login_required
def api_search_students():
    """API endpoint for student search - FIXED"""
    try:
        search_term = request.args.get('q', '')
        students_list = search_students(search_term)
        
        return jsonify([{
            'id': s.id,
            'name': s.full_name,
            'student_id': s.student_id,
            'grade': s.grade
        } for s in students_list])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================================
# PRIVACY & TERMS
# ===================================

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

# ===================================
# ERROR HANDLERS - FIXED
# ===================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# ===================================
# SETUP ROUTE - FIXED
# ===================================

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial system setup - FIXED with complete validation"""
    # Check if setup is needed
    try:
        user_count = User.query.count()
        if user_count > 0:
            flash('System already set up. Redirecting to login.', 'info')
            return redirect(url_for('login'))
    except:
        # Database doesn't exist yet, create tables
        db.create_all()
    
    if request.method == 'POST':
        admin_data = {
            'full_name': request.form.get('full_name'),
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'mobile': request.form.get('mobile')
        }
        
        # Create superadmin
        success, message = create_superadmin(admin_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    
    return render_template('setup.html')

# ===================================
# DATABASE INITIALIZATION
# ===================================



if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Database creation error: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)