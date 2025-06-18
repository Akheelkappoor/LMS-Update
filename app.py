# Complete app.py with all routes connected to functions and HTML templates

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os, json, secrets
from flask_mail import Mail
from functions.auth_functions import create_superadmin
from config import Config
from email_utils import EmailService, mail

# Import all models
from models import *

# Import all functions
from functions import *

from dotenv import load_dotenv
load_dotenv(override=True)

# Define allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

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
    """User login - connects to auth_functions.py"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user, error = authenticate_user(email, password)
        
        if user:
            login_user_session(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash(error, 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout - connects to auth_functions.py"""
    logout_user_session()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - connects to auth_functions.py"""
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
    """Password reset request - connects to auth_functions.py"""
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
    """Password reset - connects to auth_functions.py"""
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
# DASHBOARD ROUTES
# ===================================

@app.route('/dashboard')
@login_required
@approved_required
@active_required
def dashboard():
    """Main dashboard - connects to user_functions.py"""
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

# ===================================
# USER MANAGEMENT ROUTES
# ===================================

@app.route('/users')
@login_required
@coordinator_required
def users():
    """View all users - connects to user_functions.py"""
    search_term = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    department_filter = request.args.get('department', '')
    
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

@app.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user_route():
    """Create new user - UPDATED with better error handling"""
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
    permissions = Permission.query.filter_by(is_active=True).all()
    available_permissions = get_available_permissions()
    
    return render_template('users/create.html', 
                         departments=departments,
                         permissions=permissions,
                         available_permissions=available_permissions)
@app.route('/users/<int:id>')
@login_required
def view_user(id):
    """View user details - connects to user_functions.py"""
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
    """Edit user - connects to user_functions.py"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user_data = dict(request.form)
        success, message = update_user(id, user_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('view_user', id=id))
        else:
            flash(message, 'danger')
    
    departments = Department.query.filter_by(is_active=True).all()
    permissions = Permission.query.filter_by(is_active=True).all()
    
    return render_template('users/edit.html',
                         user=user,
                         departments=departments,
                         permissions=permissions)

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user_route(id):
    """Delete user - connects to user_functions.py"""
    success, message = delete_user(id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('users'))

@app.route('/users/pending')
@login_required
@admin_required
def pending_users():
    """View pending approvals - connects to auth_functions.py"""
    pending = UserApproval.query.filter_by(status='pending').order_by(UserApproval.requested_at.desc()).all()
    return render_template('users/pending.html', approvals=pending)

@app.route('/users/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user_route(user_id):
    """Approve user - connects to auth_functions.py"""
    comments = request.form.get('comments', '')
    success, message = approve_user_account(user_id, current_user.id, comments)
    
    if success:
        user = User.query.get(user_id)
        temp_password = secrets.token_urlsafe(8)
        user.set_password(temp_password)
        db.session.commit()
        
        send_welcome_email(user, temp_password)
        send_approval_notification(user, True)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('pending_users'))

@app.route('/users/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user_route(user_id):
    """Reject user - connects to auth_functions.py"""
    reason = request.form.get('reason', '')
    success, message = reject_user_account(user_id, current_user.id, reason)
    
    if success:
        user = User.query.get(user_id)
        send_approval_notification(user, False, reason)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('pending_users'))

# ===================================
# STUDENT MANAGEMENT ROUTES
# ===================================

@app.route('/students')
@login_required
@coordinator_required
def students():
    """View all students - connects to student_functions.py"""
    search_term = request.args.get('search', '')
    grade_filter = request.args.get('grade', '')
    status_filter = request.args.get('status', '')
    
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
    
    # Get unique grades for filter
    all_students = Student.query.all()
    grades = list(set(s.grade for s in all_students if s.grade))
    
    student_stats = get_student_statistics()
    
    return render_template('students/list.html',
                         students=students_list,
                         grades=grades,
                         stats=student_stats,
                         current_search=search_term,
                         current_grade=grade_filter,
                         current_status=status_filter)

@app.route('/students/create', methods=['GET', 'POST'])
@login_required
@coordinator_required
def create_student_route():
    """Create new student with profile picture upload support"""
    if request.method == 'POST':
        try:
            # Get form data
            student_data = dict(request.form)
            
            # Handle profile picture upload
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Generate unique filename using student ID or timestamp
                    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    
                    # Save file path to student data
                    upload_path = handle_file_upload(file, unique_filename, 'profile_pictures')
                    if upload_path:
                        student_data['profile_picture_path'] = upload_path
            
            # Create student
            student, result = create_student(student_data)
            
            if isinstance(result, list):  # Success case - result contains parents
                flash(f'Student {student.full_name} created successfully!', 'success')
                if len(result) > 0:
                    flash(f'{len(result)} parent record(s) added.', 'info')
                
                # Handle post-creation actions
                if student_data.get('enroll_after_creation'):
                    return redirect(url_for('enroll_student_route', id=student.id))
                return redirect(url_for('view_student', id=student.id))
            else:  # Error case - result contains error message
                flash(f'Error creating student: {result}', 'danger')
                
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'danger')
            # Log the error for debugging
            current_app.logger.error(f"Error in create_student_route: {str(e)}")
    
    # GET request or form validation failed
    try:
        departments = Department.query.filter_by(is_active=True).all()
        return render_template(
            'students/create.html',
            departments=departments,
            max_file_size=current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)  # Default 5MB
        )
    except Exception as e:
        flash('Error loading departments. Please try again.', 'danger')
        current_app.logger.error(f"Error loading departments: {str(e)}")
        return redirect(url_for('dashboard'))

@app.route('/students/<int:id>')
@login_required
@coordinator_required
def view_student(id):
    """View student details - connects to student_functions.py"""
    student = Student.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    enrollments = get_student_enrollments(id)
    fees = get_student_fees(id)
    parents = get_student_parents(id)
    
    return render_template('students/view.html', 
                         student=student,
                         enrollments=enrollments,
                         fees=fees,
                         parents=parents)



@app.route('/students/<int:id>/enroll', methods=['GET', 'POST'])
@login_required
@coordinator_required
def enroll_student_route(id):
    """Enhanced student enrollment with tutor filtering"""
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Process multiple subjects enrollment
            subjects_data = []
            form_data = request.form
            
            # Extract subjects data from form
            subject_index = 0
            while f'subjects[{subject_index}].name' in form_data:
                subject_data = {
                    'student_id': id,
                    'subject': form_data.get(f'subjects[{subject_index}].name'),
                    'tutor_id': form_data.get(f'subjects[{subject_index}].tutor_id'),
                    'class_type': form_data.get('class_type', 'regular'),
                    'sessions_per_week': int(form_data.get(f'subjects[{subject_index}].sessions_per_week', 2)),
                    'session_duration': int(form_data.get(f'subjects[{subject_index}].session_duration', 60)),
                    'start_date': datetime.strptime(form_data.get('start_date'), '%Y-%m-%d').date(),
                    'end_date': datetime.strptime(form_data.get('end_date'), '%Y-%m-%d').date() if form_data.get('end_date') else None,
                    'created_by': current_user.id
                }
                
                # Extract schedule data
                schedule_data = []
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                    day_key = f'subjects[{subject_index}].schedule_days'
                    time_key = f'subjects[{subject_index}].schedule_times_{day}'
                    
                    if day in form_data.getlist(day_key) and form_data.get(time_key):
                        schedule_data.append({
                            'day': day,
                            'time': form_data.get(time_key)
                        })
                
                subject_data['schedule'] = schedule_data
                subjects_data.append(subject_data)
                subject_index += 1
            
            # Create enrollments for each subject
            created_enrollments = []
            for subject_data in subjects_data:
                enrollment, message = enroll_student(subject_data)
                if enrollment:
                    created_enrollments.append(enrollment)
                    
                    # Auto-generate classes for this enrollment
                    generate_success, gen_message = auto_schedule_enrollment(enrollment.id)
                    if generate_success:
                        flash(f'Classes auto-generated for {subject_data["subject"]}', 'info')
                else:
                    flash(f'Error enrolling in {subject_data["subject"]}: {message}', 'danger')
                    continue
            
            if created_enrollments:
                flash(f'Successfully enrolled in {len(created_enrollments)} subject(s)!', 'success')
                return redirect(url_for('view_student', id=id))
            else:
                flash('No enrollments were created. Please try again.', 'danger')
                
        except Exception as e:
            flash(f'Enrollment failed: {str(e)}', 'danger')
    
    # Get available tutors with their profiles
    tutors_query = User.query.filter_by(role='tutor', is_active=True, is_approved=True)
    
    # Filter by coordinator's department if applicable
    if current_user.role == 'coordinator':
        tutors_query = tutors_query.filter_by(department_id=current_user.department_id)
    
    tutors = tutors_query.all()
    
    return render_template('students/enroll.html', 
                         student=student,
                         tutors=tutors)

# ===================================
# CLASS MANAGEMENT ROUTES
# ===================================

@app.route('/classes')
@login_required
def classes():
    """View classes - connects to class_functions.py"""
    if current_user.role == 'tutor':
        classes_list = get_classes_by_tutor(current_user.id)
        return render_template('tutor/my_classes.html', classes=classes_list)
    else:
        # Admin/Coordinator view
        classes_list = Class.query.order_by(Class.class_date.desc()).all()
        return render_template('classes/list.html', classes=classes_list)

@app.route('/classes/create', methods=['GET', 'POST'])
@login_required
@coordinator_required
def create_class_route():
    """Create new class - connects to class_functions.py"""
    if request.method == 'POST':
        class_data = dict(request.form)
        
        class_obj, message = create_class(class_data)
        
        if class_obj:
            flash(message, 'success')
            return redirect(url_for('classes'))
        else:
            flash(message, 'danger')
    
    # Get enrollments for dropdown
    enrollments = StudentEnrollment.query.filter_by(status='active').all()
    tutors = get_users_by_role('tutor')
    
    return render_template('classes/create.html',
                         enrollments=enrollments,
                         tutors=tutors)

@app.route('/classes/<int:id>')
@login_required
def view_class(id):
    """View class details - connects to class_functions.py"""
    class_obj = Class.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'tutor' and class_obj.tutor_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('classes'))
    
    return render_template('classes/view.html', class_obj=class_obj)

@app.route('/classes/<int:id>/start', methods=['POST'])
@login_required
@tutor_required
def start_class_route(id):
    """Start class - connects to class_functions.py"""
    success, message = start_class(id)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_class', id=id))

@app.route('/classes/<int:id>/end', methods=['POST'])
@login_required
@tutor_required
def end_class_route(id):
    """End class - connects to class_functions.py"""
    success, message = end_class(id)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_class', id=id))

@app.route('/classes/<int:id>/attendance', methods=['GET', 'POST'])
@login_required
@tutor_required
def mark_attendance_route(id):
    """Mark attendance - connects to class_functions.py"""
    class_obj = Class.query.get_or_404(id)
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        attendance_data = dict(request.form)
        
        success, message = mark_student_attendance(id, student_id, attendance_data)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('view_class', id=id))
    
    return render_template('classes/attendance.html', class_obj=class_obj)

# ===================================
# DEPARTMENT MANAGEMENT ROUTES
# ===================================

@app.route('/departments')
@login_required
@admin_required
def departments():
    """View all departments - connects to department_functions.py"""
    departments_list = Department.query.filter_by(is_active=True).all()
    dept_hierarchy = get_department_hierarchy()
    
    return render_template('departments/list.html', 
                         departments=departments_list,
                         hierarchy=dept_hierarchy)

@app.route('/departments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_department_route():
    """Create department - connects to department_functions.py"""
    if request.method == 'POST':
        department_data = dict(request.form)
        
        department, message = create_department(department_data)
        
        if department:
            flash(message, 'success')
            return redirect(url_for('departments'))
        else:
            flash(message, 'danger')
    
    form_templates = FormTemplate.query.filter_by(is_active=True).all()
    
    return render_template('departments/create.html', 
                         form_templates=form_templates)

@app.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(id):
    """Edit department - connects to department_functions.py"""
    department = Department.query.get_or_404(id)
    
    if request.method == 'POST':
        department_data = dict(request.form)
        
        success, message = update_department(id, department_data)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('departments'))
    
    form_templates = FormTemplate.query.filter_by(is_active=True).all()
    
    return render_template('departments/edit.html',
                         department=department,
                         form_templates=form_templates)

# ===================================
# FORM MANAGEMENT ROUTES
# ===================================

@app.route('/forms')
@login_required
@admin_required
def forms():
    """View all forms - connects to form_functions.py"""
    forms_list = FormTemplate.query.order_by(FormTemplate.created_at.desc()).all()
    usage_stats = get_form_usage_statistics()
    
    return render_template('forms/list.html', 
                         forms=forms_list,
                         usage_stats=usage_stats)

@app.route('/forms/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_form():
    """Create form template - connects to form_functions.py"""
    if request.method == 'POST':
        form_data = request.get_json() if request.is_json else dict(request.form)
        
        form_template, message = create_form_template(form_data)
        
        if form_template:
            if request.is_json:
                return jsonify({'success': True, 'message': message, 'form_id': form_template.id})
            else:
                flash(message, 'success')
                return redirect(url_for('forms'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': message})
            else:
                flash(message, 'danger')
    
    return render_template('forms/create.html')

@app.route('/forms/<int:id>/preview')
@login_required
@admin_required
def preview_form(id):
    """Preview form - connects to form_functions.py"""
    form_template = FormTemplate.query.get_or_404(id)
    form_html, message = generate_form_html(id)
    
    return render_template('forms/preview.html', 
                         form_template=form_template,
                         form_html=form_html)

# ===================================
# FINANCE ROUTES
# ===================================

@app.route('/finance')
@login_required
@finance_required
def finance_dashboard():
    """Finance dashboard - connects to finance_functions.py"""
    dashboard_data, message = get_financial_dashboard_data()
    
    return render_template('finance/dashboard.html', 
                         stats=dashboard_data)

@app.route('/finance/fees')
@login_required
@finance_required
def student_fees():
    """View student fees - connects to finance_functions.py"""
    fees = StudentFee.query.order_by(StudentFee.due_date.desc()).all()
    
    return render_template('finance/fees.html', fees=fees)

@app.route('/finance/fees/<int:id>/pay', methods=['POST'])
@login_required
@finance_required
def process_payment_route(id):
    """Process fee payment - connects to finance_functions.py"""
    payment_data = dict(request.form)
    
    success, message = process_fee_payment(id, payment_data)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('student_fees'))

# ===================================
# REPORTS ROUTES
# ===================================

@app.route('/reports')
@login_required
def reports():
    """Reports dashboard - connects to report_functions.py"""
    return render_template('reports/index.html')

@app.route('/reports/users')
@login_required
@admin_required
def user_report():
    """User report - connects to report_functions.py"""
    filters = dict(request.args)
    report_data, message = generate_user_report(filters)
    
    return render_template('reports/users.html', 
                         report=report_data)

@app.route('/reports/classes')
@login_required
@coordinator_required
def class_report():
    """Class performance report - connects to report_functions.py"""
    date_range = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date')
    }
    filters = dict(request.args)
    
    report_data, message = generate_class_performance_report(date_range, filters)
    
    return render_template('reports/classes.html', 
                         report=report_data)

# ===================================
# PROFILE ROUTES
# ===================================

@app.route('/profile')
@login_required
def profile():
    """User profile - connects to user_functions.py"""
    return render_template('users/profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit profile - connects to user_functions.py"""
    if request.method == 'POST':
        profile_data = dict(request.form)
        
        success, message = update_user_profile(current_user.id, profile_data)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('profile'))
    
    return render_template('users/edit_profile.html')

@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password - connects to auth_functions.py"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        success, message = change_user_password(current_user, current_password, new_password)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('profile'))
    
    return render_template('users/change_password.html')

# ===================================
# SCHEDULE ROUTES
# ===================================

@app.route('/schedule')
@login_required
def schedule():
    """Schedule view - connects to class_functions.py"""
    if current_user.role == 'tutor':
        classes_list = get_classes_by_tutor(current_user.id)
    else:
        classes_list = Class.query.filter(
            Class.class_date >= datetime.now().date()
        ).order_by(Class.class_date, Class.start_time).all()
    
    return render_template('schedule/calendar.html', classes=classes_list)

# ===================================
# API ENDPOINTS
# ===================================

@app.route('/api/forms/<int:form_id>/preview')
@login_required
def api_preview_form(form_id):
    """API endpoint for form preview - connects to form_functions.py"""
    form_template = FormTemplate.query.get_or_404(form_id)
    fields = form_template.get_fields()
    
    return jsonify({
        'form': {
            'name': form_template.name,
            'description': form_template.description,
            'fields': fields
        }
    })

@app.route('/api/students/search')
@login_required
def api_search_students():
    """API endpoint for student search - connects to student_functions.py"""
    search_term = request.args.get('q', '')
    students_list = search_students(search_term)
    
    return jsonify([{
        'id': s.id,
        'name': s.full_name,
        'student_id': s.student_id,
        'grade': s.grade
    } for s in students_list])

# ===================================
# privacy-policy/terms-of-service
# ===================================

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

# ===================================
# ERROR HANDLERS
# ===================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ===================================
# STUDENT MANAGEMENT ROUTES
# ===================================

@app.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@coordinator_required
def edit_student(id):
    """Edit student - connects to student_functions.py"""
    student = Student.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        student_data = dict(request.form)
        
        # Handle profile picture upload if present
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"student_{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                upload_path = handle_file_upload(file, unique_filename, 'profile_pictures')
                if upload_path:
                    student_data['profile_picture_path'] = upload_path
        
        success, message = update_student(id, student_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('view_student', id=id))
        else:
            flash(message, 'danger')
    
    departments = Department.query.filter_by(is_active=True).all()
    parents = get_student_parents(id)
    
    return render_template('students/edit.html',
                         student=student,
                         departments=departments,
                         parents=parents)

@app.route('/students/<int:id>/delete', methods=['POST'])
@login_required
@coordinator_required
def delete_student_route(id):
    """Delete student - connects to student_functions.py"""
    student = Student.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    success, message = delete_student(id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('students'))

@app.route('/students/<int:id>/fees', methods=['GET', 'POST'])
@login_required
@coordinator_required
def student_fees_route(id):
    """Manage student fees - connects to finance_functions.py"""
    student = Student.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        fee_data = dict(request.form)
        fee_data['student_id'] = id
        
        fee, message = create_student_fee(fee_data)
        
        if fee:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('student_fees_route', id=id))
    
    fees = get_student_fees(id)
    total_fees = sum(fee.amount for fee in fees)
    paid_fees = sum(fee.paid_amount for fee in fees)
    pending_fees = total_fees - paid_fees
    
    return render_template('students/fees.html',
                         student=student,
                         fees=fees,
                         total_fees=total_fees,
                         paid_fees=paid_fees,
                         pending_fees=pending_fees)

@app.route('/students/<int:student_id>/parents/<int:parent_id>/edit', methods=['GET', 'POST'])
@login_required
@coordinator_required
def edit_parent(student_id, parent_id):
    """Edit parent information - connects to student_functions.py"""
    student = Student.query.get_or_404(student_id)
    parent = Parent.query.get_or_404(parent_id)
    
    # Verify parent belongs to student
    if parent.student_id != student_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('view_student', id=student_id))
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        parent_data = dict(request.form)
        
        success, message = update_parent(parent_id, parent_data)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('view_student', id=student_id))
    
    return render_template('students/edit_parent.html',
                         student=student,
                         parent=parent)

@app.route('/students/<int:student_id>/parents/<int:parent_id>/delete', methods=['POST'])
@login_required
@coordinator_required
def delete_parent_route(student_id, parent_id):
    """Delete parent record - connects to student_functions.py"""
    student = Student.query.get_or_404(student_id)
    parent = Parent.query.get_or_404(parent_id)
    
    # Verify parent belongs to student
    if parent.student_id != student_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('view_student', id=student_id))
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    success, message = delete_parent(parent_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('view_student', id=student_id))

@app.route('/students/bulk-action', methods=['POST'])
@login_required
@coordinator_required
def bulk_student_action():
    """Handle bulk actions on students - connects to student_functions.py"""
    action = request.form.get('action')
    student_ids = request.form.getlist('student_ids[]')
    
    if not student_ids:
        flash('No students selected.', 'warning')
        return redirect(url_for('students'))
    
    # Convert to integers
    student_ids = [int(id) for id in student_ids]
    
    if action == 'promote':
        new_grade = request.form.get('new_grade')
        if not new_grade:
            flash('Please specify the new grade.', 'warning')
            return redirect(url_for('students'))
        
        success, message = promote_students(student_ids, new_grade)
        
    elif action == 'update_status':
        new_status = request.form.get('new_status')
        if not new_status:
            flash('Please specify the new status.', 'warning')
            return redirect(url_for('students'))
        
        update_data = {'status': new_status}
        success, message = bulk_update_students(student_ids, update_data)
        
    elif action == 'transfer_department':
        new_department_id = request.form.get('new_department_id')
        if not new_department_id:
            flash('Please specify the target department.', 'warning')
            return redirect(url_for('students'))
        
        update_data = {'department_id': int(new_department_id)}
        success, message = bulk_update_students(student_ids, update_data)
        
    else:
        flash('Invalid action selected.', 'warning')
        return redirect(url_for('students'))
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('students'))

# Helper functions for file uploads
def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, filename, subfolder='uploads'):
    """Handle file upload and return file path"""
    try:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', subfolder)
        
        # Create directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return f"uploads/{subfolder}/{filename}"
        
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return None




# ============================================
# calendar functionality
# ============================================

# Add these API routes for calendar functionality
@app.route('/api/schedule/week')
@login_required
def api_schedule_week():
    """API endpoint for weekly schedule data"""
    week_start = request.args.get('week_start')
    
    if not week_start:
        return jsonify({'error': 'week_start parameter required'}), 400
    
    try:
        week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        week_end_date = week_start_date + timedelta(days=6)
        
        # Get classes for the week based on user role
        if current_user.role == 'tutor':
            classes = Class.query.filter(
                Class.tutor_id == current_user.id,
                Class.class_date >= week_start_date,
                Class.class_date <= week_end_date
            ).all()
        elif current_user.role == 'coordinator':
            # Get classes for coordinator's department
            classes = Class.query.join(User).filter(
                User.department_id == current_user.department_id,
                Class.class_date >= week_start_date,
                Class.class_date <= week_end_date
            ).all()
        else:
            # Admin/Superadmin see all classes
            classes = Class.query.filter(
                Class.class_date >= week_start_date,
                Class.class_date <= week_end_date
            ).all()
        
        # Convert to JSON format
        schedule_data = []
        for cls in classes:
            schedule_data.append({
                'id': cls.id,
                'subject': cls.subject,
                'date': cls.class_date.isoformat(),
                'start_time': cls.start_time.strftime('%H:%M'),
                'end_time': cls.end_time.strftime('%H:%M'),
                'student_name': cls.enrollment.student.full_name,
                'tutor_name': cls.tutor.full_name,
                'status': cls.status,
                'meeting_link': cls.meeting_link
            })
        
        return jsonify(schedule_data)
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@app.route('/api/tutor/today-classes')
@login_required
@tutor_required
def api_tutor_today_classes():
    """API endpoint for tutor's today classes"""
    today = datetime.now().date()
    
    classes = Class.query.filter(
        Class.tutor_id == current_user.id,
        Class.class_date == today
    ).order_by(Class.start_time).all()
    
    classes_data = []
    for cls in classes:
        classes_data.append({
            'id': cls.id,
            'subject': cls.subject,
            'student': cls.enrollment.student.full_name,
            'time': f"{cls.start_time.strftime('%I:%M %p')} - {cls.end_time.strftime('%I:%M %p')}",
            'status': cls.status,
            'meeting_link': cls.meeting_link
        })
    
    return jsonify(classes_data)

# Add route to generate classes from enrollment
@app.route('/generate-classes-from-enrollment/<int:enrollment_id>', methods=['POST'])
@login_required
@coordinator_required
def generate_classes_from_enrollment(enrollment_id):
    """Generate class sessions from enrollment schedule"""
    enrollment = StudentEnrollment.query.get_or_404(enrollment_id)
    
    # Get schedule data
    schedule = enrollment.get_schedule()
    if not schedule:
        flash('No schedule data found for this enrollment.', 'warning')
        return redirect(url_for('view_student', id=enrollment.student_id))
    
    # Generate classes for next 4 weeks (or until end_date)
    from datetime import datetime, timedelta
    import calendar
    
    start_date = enrollment.start_date
    end_date = enrollment.end_date or (start_date + timedelta(weeks=12))  # Default 12 weeks
    
    classes_created = 0
    current_date = start_date
    
    while current_date <= end_date:
        # Check if this day matches any schedule entry
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
    
    try:
        db.session.commit()
        flash(f'Successfully created {classes_created} class sessions!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating classes: {str(e)}', 'danger')
    
    return redirect(url_for('view_student', id=enrollment.student_id))

# Add this route for missing student fees detail
@app.route('/students/<int:id>/fees')
@login_required
@coordinator_required
def student_fees_detail(id):
    """View student fee details"""
    student = Student.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('students'))
    
    fees = get_student_fees(id)
    
    return render_template('finance/student_fees_detail.html', 
                         student=student, 
                         fees=fees)



# ============================================
# DEPARTMENT
# ============================================

@app.route('/departments/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_department_route(id):
    """Delete department - connects to department_functions.py"""
    success, message = delete_department(id)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@app.route('/departments/<int:id>')
@login_required
@admin_required
def view_department(id):
    """View department details - connects to department_functions.py"""
    department = Department.query.get_or_404(id)
    
    # Get department statistics
    stats = get_department_statistics(id)
    users = get_department_users(id)
    
    return render_template('departments/view.html', 
                         department=department,
                         stats=stats,
                         users=users)



# ============================================
# USER Permission Management
# ============================================

@app.route('/users/<int:id>/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user_permissions(id):
    """Manage user permissions"""
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        permissions = request.form.getlist('permissions')
        success, message = update_user_permissions(id, permissions)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('view_user', id=id))
    
    available_permissions = get_available_permissions()
    user_permissions = user.get_permissions()
    
    return render_template('users/permissions.html',
                         user=user,
                         available_permissions=available_permissions,
                         user_permissions=user_permissions)

@app.route('/api/user-permissions/<int:user_id>')
@login_required
@admin_required
def api_user_permissions(user_id):
    """API endpoint to get user permissions"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'permissions': user.get_permissions(),
        'role': user.role
    })

@app.route('/demo-requests')
@login_required
@permission_required('view_demo_requests')
def demo_requests():
    """View demo requests - uses permission decorator"""
    # Your demo request logic here
    return render_template('demos/list.html')

@app.route('/demo-requests/<int:id>/approve', methods=['POST'])
@login_required
@permission_required('approve_demo_requests')
def approve_demo_request(id):
    """Approve demo request - uses permission decorator"""
    # Your approval logic here
    flash('Demo request approved!', 'success')
    return redirect(url_for('demo_requests'))

# ===================================
# Setup
# ===================================
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial system setup"""
    # Check if setup is needed
    try:
        user_count = User.query.count()
        if user_count > 0:
            flash('System already set up. Redirecting to login.', 'info')
            return redirect(url_for('login'))
    except:
        # Database doesn't exist yet
        pass
    
    if request.method == 'POST':
        admin_data = {
            'full_name': request.form.get('full_name'),
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'mobile': request.form.get('mobile')
        }
        
        # Create superadmin
        from functions.auth_functions import create_superadmin
        success, message = create_superadmin(admin_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    
    return render_template('setup.html')

# ============================================
# TUTOR REGISTRATION ROUTES
# ============================================

@app.route('/tutors/register', methods=['GET', 'POST'])
@login_required
@coordinator_required
def register_tutor():
    """Tutor registration by coordinators"""
    if request.method == 'POST':
        try:
            # Create user account first
            user_data = {
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'full_name': request.form.get('full_name'),
                'phone': request.form.get('phone'),
                'role': 'tutor',
                'department_id': request.form.get('department_id'),
                'password': request.form.get('password'),
                'is_approved': True,  # Auto-approved by coordinator
                'is_active': True
            }
            
            user, error = register_new_user(user_data)
            if not user:
                flash(error, 'danger')
                return redirect(url_for('register_tutor'))
            
            # Create tutor profile
            tutor_profile = TutorProfile(
                user_id=user.id,
                employee_id=generate_employee_id(),
                qualification=request.form.get('qualification'),
                experience_years=int(request.form.get('experience_years', 0)),
                teaching_mode=request.form.get('teaching_mode'),
                max_students_per_day=int(request.form.get('max_students_per_day', 8)),
                preferred_duration=int(request.form.get('preferred_duration', 60)),
                hourly_rate=float(request.form.get('hourly_rate', 0)),
                payment_mode=request.form.get('payment_mode'),
                bank_account_number=request.form.get('bank_account_number'),
                ifsc_code=request.form.get('ifsc_code'),
                upi_id=request.form.get('upi_id'),
                application_status='approved',
                approved_by=current_user.id,
                approved_date=datetime.utcnow()
            )
            
            # Set specialization, languages, and grades
            if request.form.getlist('specialization'):
                tutor_profile.set_specialization(request.form.getlist('specialization'))
            
            if request.form.getlist('languages'):
                tutor_profile.set_languages(request.form.getlist('languages'))
            
            if request.form.getlist('preferred_grades'):
                tutor_profile.set_preferred_grades(request.form.getlist('preferred_grades'))
            
            # Handle file uploads
            if 'resume' in request.files:
                resume_file = request.files['resume']
                if resume_file.filename:
                    resume_path = handle_file_upload(resume_file, f"resume_{user.id}_{resume_file.filename}", 'tutor_documents')
                    tutor_profile.resume_path = resume_path
            
            db.session.add(tutor_profile)
            db.session.commit()
            
            flash(f'Tutor {user.full_name} registered successfully!', 'success')
            return redirect(url_for('tutor_management'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('tutors/register.html', departments=departments)

@app.route('/tutors/management')
@login_required
@coordinator_required
def tutor_management():
    """Tutor management dashboard"""
    # Get filters
    department_filter = request.args.get('department')
    subject_filter = request.args.get('subject')
    availability_filter = request.args.get('availability')
    experience_filter = request.args.get('experience')
    
    # Build query
    query = TutorProfile.query.join(User)
    
    # Apply filters
    if current_user.role == 'coordinator':
        query = query.filter(User.department_id == current_user.department_id)
    
    if department_filter:
        query = query.filter(User.department_id == department_filter)
    
    if subject_filter:
        query = query.filter(TutorProfile.specialization.contains(subject_filter))
    
    if availability_filter:
        query = query.filter(TutorProfile.availability_status == availability_filter)
    
    if experience_filter:
        if experience_filter == '0-2':
            query = query.filter(TutorProfile.experience_years <= 2)
        elif experience_filter == '3-5':
            query = query.filter(TutorProfile.experience_years.between(3, 5))
        elif experience_filter == '5+':
            query = query.filter(TutorProfile.experience_years >= 5)
    
    tutors = query.all()
    departments = Department.query.filter_by(is_active=True).all()
    
    return render_template('tutors/management.html', 
                         tutors=tutors, 
                         departments=departments)

@app.route('/tutors/<int:id>/availability', methods=['GET', 'POST'])
@login_required
def tutor_availability(id):
    """Manage tutor availability"""
    tutor_profile = TutorProfile.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'tutor' and tutor_profile.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Update availability schedule
        schedule_data = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            day_slots = request.form.getlist(f'{day}_slots')
            if day_slots:
                schedule_data[day] = day_slots
        
        tutor_profile.set_weekly_schedule(schedule_data)
        tutor_profile.availability_status = request.form.get('availability_status', 'available')
        
        db.session.commit()
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('tutor_availability', id=id))
    
    return render_template('tutors/availability.html', tutor_profile=tutor_profile)

@app.route('/api/tutors/search')
@login_required
def api_search_tutors():
    """API endpoint for tutor search with filters"""
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    day = request.args.get('day')
    time_slot = request.args.get('time_slot')
    department_id = request.args.get('department_id')
    
    query = TutorProfile.query.join(User).filter(
        TutorProfile.application_status == 'approved',
        TutorProfile.availability_status == 'available',
        TutorProfile.is_active_for_new_students == True
    )
    
    # Apply filters
    if department_id:
        query = query.filter(User.department_id == department_id)
    
    if subject:
        query = query.filter(TutorProfile.specialization.contains(f'"{subject}"'))
    
    if grade:
        query = query.filter(TutorProfile.preferred_grades.contains(f'"{grade}"'))
    
    tutors = query.all()
    
    # Filter by availability if day and time provided
    if day and time_slot:
        available_tutors = []
        for tutor in tutors:
            if tutor.is_available_at(day, time_slot):
                available_tutors.append(tutor)
        tutors = available_tutors
    
    # Convert to JSON
    tutors_data = []
    for tutor in tutors:
        tutors_data.append({
            'id': tutor.id,
            'user_id': tutor.user_id,
            'name': tutor.user.full_name,
            'email': tutor.user.email,
            'phone': tutor.user.phone,
            'employee_id': tutor.employee_id,
            'qualification': tutor.qualification,
            'experience_years': tutor.experience_years,
            'specialization': tutor.get_specialization(),
            'languages': tutor.get_languages(),
            'preferred_grades': tutor.get_preferred_grades(),
            'hourly_rate': tutor.hourly_rate,
            'average_rating': tutor.average_rating,
            'total_students_taught': tutor.total_students_taught,
            'availability_status': tutor.availability_status
        })
    
    return jsonify(tutors_data)



@app.route('/api/tutors/filter')
@login_required
def api_filter_tutors():
    """API endpoint for filtering tutors based on criteria"""
    try:
        # Get filter parameters
        subject = request.args.get('subject', '').lower()
        grade = request.args.get('grade', '').lower()
        min_rate = request.args.get('min_rate', type=float)
        max_rate = request.args.get('max_rate', type=float)
        min_experience = request.args.get('min_experience', type=int)
        max_experience = request.args.get('max_experience', type=int)
        search_term = request.args.get('search', '').lower()
        department_id = request.args.get('department_id', type=int)
        
        # Base query - get tutors with profiles
        query = db.session.query(User, TutorProfile).join(
            TutorProfile, User.id == TutorProfile.user_id, isouter=True
        ).filter(
            User.role == 'tutor',
            User.is_active == True,
            User.is_approved == True
        )
        
        # Filter by coordinator's department if applicable
        if current_user.role == 'coordinator':
            query = query.filter(User.department_id == current_user.department_id)
        elif department_id:
            query = query.filter(User.department_id == department_id)
        
        results = query.all()
        
        # Apply filters
        filtered_tutors = []
        for user, tutor_profile in results:
            # Skip if no profile and we need profile data for filtering
            if not tutor_profile and (subject or grade or min_rate or max_rate or min_experience or max_experience):
                continue
                
            # Search filter (name, qualification, subjects)
            if search_term:
                searchable_text = f"{user.full_name} {user.email}".lower()
                if tutor_profile:
                    searchable_text += f" {tutor_profile.qualification or ''} {' '.join(tutor_profile.get_specialization())}".lower()
                
                if search_term not in searchable_text:
                    continue
            
            # Subject filter
            if subject and tutor_profile:
                specializations = [s.lower() for s in tutor_profile.get_specialization()]
                if subject not in specializations:
                    continue
            
            # Grade filter
            if grade and tutor_profile:
                preferred_grades = [g.lower() for g in tutor_profile.get_preferred_grades()]
                if grade not in preferred_grades:
                    continue
            
            # Rate filters
            if tutor_profile and tutor_profile.hourly_rate:
                if min_rate and tutor_profile.hourly_rate < min_rate:
                    continue
                if max_rate and tutor_profile.hourly_rate > max_rate:
                    continue
            
            # Experience filters
            if tutor_profile and tutor_profile.experience_years is not None:
                if min_experience and tutor_profile.experience_years < min_experience:
                    continue
                if max_experience and tutor_profile.experience_years > max_experience:
                    continue
            
            # Add to filtered results
            filtered_tutors.append((user, tutor_profile))
        
        # Convert to JSON response
        tutors_data = []
        for user, tutor_profile in filtered_tutors:
            tutor_data = {
                'id': user.id,
                'name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'department': user.department.name if user.department else None
            }
            
            if tutor_profile:
                tutor_data.update({
                    'employee_id': tutor_profile.employee_id,
                    'qualification': tutor_profile.qualification,
                    'experience_years': tutor_profile.experience_years or 0,
                    'specialization': tutor_profile.get_specialization(),
                    'languages': tutor_profile.get_languages(),
                    'preferred_grades': tutor_profile.get_preferred_grades(),
                    'hourly_rate': tutor_profile.hourly_rate or 0,
                    'average_rating': tutor_profile.average_rating or 0,
                    'total_students_taught': tutor_profile.total_students_taught or 0,
                    'availability_status': tutor_profile.availability_status
                })
            else:
                # Default values for tutors without profiles
                tutor_data.update({
                    'employee_id': None,
                    'qualification': None,
                    'experience_years': 0,
                    'specialization': [],
                    'languages': [],
                    'preferred_grades': [],
                    'hourly_rate': 0,
                    'average_rating': 0,
                    'total_students_taught': 0,
                    'availability_status': 'available'
                })
            
            tutors_data.append(tutor_data)
        
        return jsonify({
            'success': True,
            'tutors': tutors_data,
            'total': len(tutors_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tutors/<int:tutor_id>/availability')
@login_required
def api_tutor_availability(tutor_id):
    """Check tutor availability for specific days/times"""
    try:
        day = request.args.get('day', '').lower()
        time_slot = request.args.get('time')
        date_str = request.args.get('date')
        
        tutor_profile = TutorProfile.query.filter_by(user_id=tutor_id).first()
        if not tutor_profile:
            return jsonify({
                'available': False,
                'reason': 'Tutor profile not found'
            })
        
        # Check general weekly availability
        if day and time_slot:
            is_available = tutor_profile.is_available_at(day, time_slot)
            
            if not is_available:
                return jsonify({
                    'available': False,
                    'reason': f'Tutor not available on {day.title()} at {time_slot}'
                })
        
        # Check specific date availability (if classes already scheduled)
        if date_str:
            try:
                check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                existing_classes = Class.query.filter(
                    Class.tutor_id == tutor_id,
                    Class.class_date == check_date
                ).all()
                
                if time_slot:
                    # Check if specific time slot is free
                    for cls in existing_classes:
                        class_start = cls.start_time
                        class_end = cls.end_time
                        check_time = datetime.strptime(time_slot, '%H:%M').time()
                        
                        if class_start <= check_time <= class_end:
                            return jsonify({
                                'available': False,
                                'reason': f'Tutor has a class at {time_slot} on {check_date}'
                            })
                
                return jsonify({
                    'available': True,
                    'existing_classes': len(existing_classes),
                    'schedule': [
                        {
                            'start_time': cls.start_time.strftime('%H:%M'),
                            'end_time': cls.end_time.strftime('%H:%M'),
                            'subject': cls.subject
                        } for cls in existing_classes
                    ]
                })
                
            except ValueError:
                return jsonify({
                    'available': False,
                    'reason': 'Invalid date format'
                })
        
        return jsonify({
            'available': True,
            'weekly_schedule': tutor_profile.get_weekly_schedule()
        })
        
    except Exception as e:
        return jsonify({
            'available': False,
            'reason': str(e)
        }), 500

# ===================================
# MAIN
# ===================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)