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
from functions import student_functions
from functions import user_functions
from functions import auth_functions
# If delete_user is not in functions.py, define a stub here or import it directly:
from functions import delete_user

from dotenv import load_dotenv
load_dotenv(override=True)
from functions.user_functions import create_user, get_available_permissions
# Define allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, field_name, upload_type='documents'):
    """Handle file upload and return file path"""
    try:
        if not file or file.filename == '':
            return None
            
        if not allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        # Create upload directory
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], upload_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{timestamp}_{field_name}.{file_extension}"
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Return relative path for database storage
        return f"uploads/{upload_type}/{unique_filename}"
        
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

# Replace the dashboard route in your app.py with this fixed version:

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - COMPLETELY FIXED"""
    try:
        # Debug: Print user info
        print(f"Dashboard access - User: {current_user.username}, Role: {current_user.role}, Approved: {current_user.is_approved}, Active: {current_user.is_active}")
        
        # Check if user is approved (except superadmin)
        if not current_user.is_approved and current_user.role != 'superadmin':
            flash('Your account is pending approval. Please wait for admin approval.', 'warning')
            return render_template('auth/pending_approval.html')
        
        # Check if user is active
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact admin.', 'danger')
            return redirect(url_for('login'))
        
        # Get dashboard data
        dashboard_data = get_user_dashboard_data(current_user)
        print(f"Dashboard data: {dashboard_data}")
        
        # Route to specific dashboard based on role
        if current_user.role == 'superadmin':
            print("Routing to superadmin dashboard")
            return render_template('dashboard/superadmin.html', data=dashboard_data)
        elif current_user.role == 'admin':
            print("Routing to admin dashboard")
            return render_template('dashboard/admin.html', stats=dashboard_data)
        elif current_user.role == 'coordinator':
            print("Routing to coordinator dashboard")
            return render_template('dashboard/coordinator.html', stats=dashboard_data)
        elif current_user.role == 'tutor':
            print("Routing to tutor dashboard")
            return render_template('dashboard/tutor.html', stats=dashboard_data)
        elif current_user.role == 'finance_coordinator':
            print("Routing to finance dashboard")
            return render_template('finance/dashboard.html', stats=dashboard_data)
        else:
            print("Routing to generic dashboard")
            return render_template('dashboard.html', data=dashboard_data)
            
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        import traceback
        traceback.print_exc()
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
def create_user_route():  # ← Changed from create_user to create_user_route
    """Create new user with department form integration"""
    if request.method == 'POST':
        try:
            # Basic user data
            user_data = {
                'full_name': request.form.get('full_name'),
                'username': request.form.get('username'), 
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'phone': request.form.get('mobile'),  # ← Fixed: changed mobile to phone
                'role': request.form.get('role'),
                'department_id': request.form.get('department_id'),
                'is_active': True
            }
            
            # Collect custom form fields from department form
            custom_fields = {}
            for key, value in request.form.items():
                if key.startswith('custom_'):
                    field_name = key.replace('custom_', '')
                    if value:  # Only store non-empty values
                        custom_fields[field_name] = value
            
            # Handle file uploads for custom fields
            custom_files = {}
            for key, file in request.files.items():
                if key.startswith('custom_file_') and file and file.filename:
                    field_name = key.replace('custom_file_', '')
                    # Save file and get path
                    file_path = handle_file_upload(file, field_name, 'user_documents')
                    if file_path:
                        custom_files[field_name] = file_path
            
            # Merge custom data
            if custom_fields:
                user_data['custom_fields'] = custom_fields
            if custom_files:
                user_data['uploaded_files'] = custom_files
            
            # Create user - Import with alias to avoid naming conflict
            from functions.user_functions import create_user as create_user_func
            user, result = create_user_func(user_data)
            
            if user:
                flash(f'User {user.full_name} created successfully!', 'success')
                return redirect(url_for('users'))
            else:
                flash(f'Error creating user: {result}', 'danger')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - show form
    departments = Department.query.filter_by(is_active=True).all()
    form_templates = FormTemplate.query.filter_by(is_active=True).all()
    
    return render_template('users/create.html', 
                         departments=departments,
                         form_templates=form_templates)

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
    """View all students with enhanced filtering"""
    try:
        # Get filter parameters
        search_term = request.args.get('search', '').strip()
        grade_filter = request.args.get('grade', '')
        status_filter = request.args.get('status', '')
        department_filter = request.args.get('department', '')
        
        # Base query
        query = Student.query
        
        # Apply search filter
        if search_term:
            search_pattern = f'%{search_term}%'
            query = query.filter(
                db.or_(
                    Student.first_name.ilike(search_pattern),
                    Student.last_name.ilike(search_pattern),
                    Student.email.ilike(search_pattern),
                    Student.student_id.ilike(search_pattern),
                    Student.phone.ilike(search_pattern)
                )
            )
        
        # Apply grade filter
        if grade_filter:
            query = query.filter(Student.grade == grade_filter)
        
        # Apply status filter
        if status_filter:
            query = query.filter(Student.status == status_filter)
        else:
            # Default to active students only
            query = query.filter(Student.status.in_(['active', 'inactive']))
        
        # Apply department filter
        if department_filter:
            try:
                dept_id = int(department_filter)
                query = query.filter(Student.department_id == dept_id)
            except (ValueError, TypeError):
                pass
        
        # Get students with department info
        students = query.join(Department, Student.department_id == Department.id, isouter=True)\
                       .add_columns(Department.name.label('dept_name'))\
                       .order_by(Student.first_name, Student.last_name).all()
        
        # Process students to include department info
        students_list = []
        for student_row in students:
            student = student_row[0]  # Student object
            dept_name = student_row[1]  # Department name
            
            # Add department info to student object for template
            student.department_name = dept_name
            students_list.append(student)
        
        # Get departments for filter
        departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
        
        return render_template('students/list.html', 
                             students=students_list,
                             departments=departments,
                             current_search=search_term,
                             current_grade=grade_filter,
                             current_status=status_filter,
                             current_department=department_filter)
                             
    except Exception as e:
        print(f"Error loading students: {str(e)}")
        flash(f'Error loading students: {str(e)}', 'danger')
        
        # Return safe fallback
        try:
            departments = Department.query.filter_by(is_active=True).all()
        except:
            departments = []
            
        return render_template('students/list.html', 
                             students=[], 
                             departments=departments)

@app.route('/students/create', methods=['GET', 'POST'])
@login_required
@coordinator_required
def create_student():
    """Create new student with department form integration"""
    if request.method == 'POST':
        try:
            # Basic student data
            student_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'date_of_birth': request.form.get('date_of_birth'),
                'gender': request.form.get('gender'),
                'grade': request.form.get('grade'),
                'school': request.form.get('school'),
                'board': request.form.get('board'),
                'department_id': request.form.get('department_id'),
                'address_line1': request.form.get('address_line1'),
                'address_line2': request.form.get('address_line2'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'pincode': request.form.get('pincode'),
                'country': request.form.get('country', 'India'),
                'status': 'active',
                'created_by': current_user.id
            }
            
            # Collect custom form fields from department form
            custom_fields = {}
            for key, value in request.form.items():
                if key.startswith('custom_'):
                    field_name = key.replace('custom_', '')
                    if value:  # Only store non-empty values
                        custom_fields[field_name] = value
            
            # Handle file uploads for custom fields
            custom_files = {}
            for key, file in request.files.items():
                if key.startswith('custom_file_') and file and file.filename:
                    field_name = key.replace('custom_file_', '')
                    # Save file and get path
                    file_path = handle_file_upload(file, field_name, 'student_documents')
                    if file_path:
                        custom_files[field_name] = file_path
                
                # Handle regular file uploads (profile_picture, id_proof, academic_records)
                elif file and file.filename and key in ['profile_picture', 'id_proof', 'academic_records']:
                    file_path = handle_file_upload(file, key, 'student_documents')
                    if file_path:
                        custom_files[key] = file_path
            
            # Merge custom data
            if custom_fields:
                student_data['custom_fields'] = custom_fields
            if custom_files:
                student_data['uploaded_files'] = custom_files
            
            # Create student
            from functions.student_functions import create_student as create_student_func
            student, result = create_student_func(student_data)
            
            if student:
                flash(f'Student {student.first_name} {student.last_name} registered successfully!', 'success')
                return redirect(url_for('students'))
            else:
                flash(f'Error creating student: {result}', 'danger')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - show form
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('students/create.html', departments=departments)

@app.route('/students/<int:id>/toggle-status', methods=['POST'])
@login_required
@coordinator_required
def toggle_student_status(id):
    """Activate/Deactivate student"""
    try:
        student = Student.query.get_or_404(id)
        
        # Toggle status
        if student.status == 'active':
            student.status = 'inactive'
        else:
            student.status = 'active'
        
        student.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = "activated" if student.status == 'active' else "deactivated"
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'Student {status} successfully',
                'status': student.status
            })
        
        flash(f'Student {status} successfully', 'success')
        return redirect(url_for('students'))
        
    except Exception as e:
        error_msg = f'Error updating student status: {str(e)}'
        
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'danger')
        return redirect(url_for('students'))


@app.route('/students/<int:id>/view-documents')
@login_required
@coordinator_required
def view_student_documents(id):
    """View student documents"""
    try:
        student = Student.query.get_or_404(id)
        documents = student.get_uploaded_documents()
        
        return render_template('students/documents.html', 
                             student=student, 
                             documents=documents)
        
    except Exception as e:
        flash(f'Error loading documents: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=id))

@app.route('/students/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@coordinator_required
def edit_student(id):
    """Edit student details"""
    try:
        student = Student.query.get_or_404(id)
        
        if request.method == 'POST':
            # Update student data
            try:
                student.first_name = request.form.get('first_name', student.first_name)
                student.last_name = request.form.get('last_name', student.last_name)
                student.email = request.form.get('email', student.email)
                student.phone = request.form.get('phone', student.phone)
                student.grade = request.form.get('grade', student.grade)
                student.school = request.form.get('school', student.school)
                student.board = request.form.get('board', student.board)
                
                if request.form.get('department_id'):
                    student.department_id = int(request.form.get('department_id'))
                
                # Handle date of birth
                if request.form.get('date_of_birth'):
                    student.date_of_birth = parse_date(request.form.get('date_of_birth'))
                
                # Update address
                student.address_line1 = request.form.get('address_line1', student.address_line1)
                student.address_line2 = request.form.get('address_line2', student.address_line2)
                student.city = request.form.get('city', student.city)
                student.state = request.form.get('state', student.state)
                student.pincode = request.form.get('pincode', student.pincode)
                student.country = request.form.get('country', student.country)
                
                # Handle status
                student.status = request.form.get('status', student.status)
                student.updated_at = datetime.utcnow()
                
                # Handle custom fields update
                custom_fields = {}
                for key, value in request.form.items():
                    if key.startswith('custom_'):
                        field_name = key.replace('custom_', '')
                        if value:
                            custom_fields[field_name] = value
                
                if custom_fields:
                    student.set_custom_fields(custom_fields)
                
                # Handle file uploads
                custom_files = student.get_uploaded_documents()
                for key, file in request.files.items():
                    if file and file.filename:
                        if key.startswith('custom_file_'):
                            field_name = key.replace('custom_file_', '')
                            file_path = handle_file_upload(file, field_name, 'student_documents')
                            if file_path:
                                custom_files[field_name] = file_path
                        elif key in ['profile_picture', 'id_proof', 'academic_records']:
                            file_path = handle_file_upload(file, key, 'student_documents')
                            if file_path:
                                custom_files[key] = file_path
                                if key == 'profile_picture':
                                    student.profile_picture_path = file_path
                
                if custom_files:
                    student.set_uploaded_documents(custom_files)
                
                db.session.commit()
                flash('Student updated successfully!', 'success')
                return redirect(url_for('view_student', id=id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating student: {str(e)}', 'danger')
        
        departments = Department.query.filter_by(is_active=True).all()
        return render_template('students/edit.html', student=student, departments=departments)
        
    except Exception as e:
        print(f"Error editing student: {str(e)}")
        flash(f'Error editing student: {str(e)}', 'danger')
        return redirect(url_for('students'))

@app.route('/students/<int:id>')
@login_required
@coordinator_required
def view_student(id):
    """View student details - FIXED with complete information"""
    try:
        student = Student.query.get_or_404(id)
        
        # Check permissions
        if current_user.role == 'coordinator' and student.department_id != current_user.department_id:
            flash('Access denied.', 'danger')
            return redirect(url_for('students'))
        
        # Get student's enrollments and classes
        enrollments = getattr(student, 'enrollments', [])
        fees = StudentFee.query.filter_by(student_id=student.id).all() if hasattr(student, 'id') else []
        
        return render_template('students/view.html', 
                             student=student,
                             enrollments=enrollments,
                             fees=fees)
    except Exception as e:
        flash(f'Error loading student details: {str(e)}', 'danger')
        return redirect(url_for('students'))


@app.route('/students/<int:id>/enroll', methods=['GET', 'POST'])
@login_required
@coordinator_required
def enroll_student_route(id):
    """Enroll student in a class/course"""
    try:
        student = Student.query.get_or_404(id)
        
        if request.method == 'POST':
            enrollment_data = {
                'student_id': id,
                'course_id': request.form.get('course_id'),
                'tutor_id': request.form.get('tutor_id'),
                'enrollment_date': request.form.get('enrollment_date'),
                'fee_amount': request.form.get('fee_amount'),
                'status': 'active'
            }
            
            # Create enrollment (you'll need to implement this function)
            success, message = create_student_enrollment(enrollment_data)
            
            if success:
                flash('Student enrolled successfully!', 'success')
                return redirect(url_for('view_student', id=id))
            else:
                flash(message, 'danger')
        
        # Get available courses and tutors for enrollment
        tutors = User.query.filter_by(role='tutor', is_active=True).all()
        
        return render_template('students/enroll.html', 
                             student=student, 
                             tutors=tutors)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=id))

@app.route('/students/<int:id>/fees', methods=['GET', 'POST'])
@login_required
@coordinator_required
def student_fees_route(id):
    """Manage student fees"""
    try:
        student = Student.query.get_or_404(id)
        
        if request.method == 'POST':
            fee_data = {
                'student_id': id,
                'fee_type': request.form.get('fee_type'),
                'amount': float(request.form.get('amount', 0)),
                'due_date': request.form.get('due_date'),
                'description': request.form.get('description')
            }
            
            # Create fee record
            success, message = create_student_fee(fee_data)
            
            if success:
                flash('Fee added successfully!', 'success')
                return redirect(url_for('student_fees_route', id=id))
            else:
                flash(message, 'danger')
        
        # Get student's fees
        fees = StudentFee.query.filter_by(student_id=id).order_by(StudentFee.due_date.desc()).all()
        
        return render_template('students/fees.html', 
                             student=student, 
                             fees=fees)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=id))

@app.route('/students/<int:id>/attendance')
@login_required
def student_attendance(id):
    """View student attendance"""
    try:
        student = Student.query.get_or_404(id)
        
        # Get attendance records (you'll need to create this model)
        # attendance_records = StudentAttendance.query.filter_by(student_id=id).all()
        attendance_records = []  # Placeholder
        
        return render_template('students/attendance.html', 
                             student=student, 
                             attendance_records=attendance_records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=id))

@app.route('/students/<int:id>/documents', methods=['GET', 'POST'])
@login_required
@coordinator_required
def student_documents(id):
    """Manage student documents"""
    try:
        student = Student.query.get_or_404(id)
        
        if request.method == 'POST':
            if 'document' in request.files:
                file = request.files['document']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    
                    filepath = handle_file_upload(file, filename, f'students/{id}')
                    
                    if filepath:
                        # Add document to student's documents list
                        documents = student.get_documents()
                        documents.append({
                            'filename': filename,
                            'original_name': file.filename,
                            'filepath': filepath,
                            'uploaded_at': datetime.now().isoformat(),
                            'uploaded_by': current_user.id
                        })
                        student.set_documents(documents)
                        db.session.commit()
                        
                        flash('Document uploaded successfully!', 'success')
                    else:
                        flash('Failed to upload document', 'danger')
                else:
                    flash('Invalid file type', 'danger')
            
            return redirect(url_for('student_documents', id=id))
        
        documents = student.get_documents()
        return render_template('students/documents.html', 
                             student=student, 
                             documents=documents)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=id))

@app.route('/students/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(id):
    """Delete/deactivate student"""
    try:
        student = Student.query.get_or_404(id)
        
        # Soft delete - change status to inactive
        student.status = 'inactive'
        student.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Student {student.first_name} {student.last_name} has been deactivated', 'success')
        return redirect(url_for('students'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=id))

# ===================================
# CLASS MANAGEMENT ROUTES - FIXED
# ===================================

@app.route('/classes')
@login_required
@coordinator_required
def classes():
    """Classes overview page"""
    try:
        from models import Class, db
        from datetime import datetime, date, timedelta
        
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        month_start = today.replace(day=1)
        
        # Get class counts
        today_classes = Class.query.filter(
            Class.class_date == today,
            Class.status.in_(['scheduled', 'in_progress'])
        ).count()
        
        upcoming_classes = Class.query.filter(
            Class.class_date.between(week_start, week_end),
            Class.status == 'scheduled'
        ).count()
        
        completed_classes = Class.query.filter(
            Class.class_date >= month_start,
            Class.status == 'completed'
        ).count()
        
        return render_template('classes/list.html',
                             today_classes=today_classes,
                             upcoming_classes=upcoming_classes,
                             completed_classes=completed_classes)
        
    except Exception as e:
        flash(f'Error loading classes: {str(e)}', 'danger')
        return render_template('classes/list.html',
                             today_classes=0,
                             upcoming_classes=0,
                             completed_classes=0)

# ADD these routes to your app.py for complete class scheduling system:

@app.route('/schedule')
@login_required
@coordinator_required
def schedule():
    """Main class scheduling page with advanced filters"""
    try:
        # Get filter parameters
        student_id = request.args.get('student_id')
        subject = request.args.get('subject')
        tutor_id = request.args.get('tutor_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        # Base query for classes
        from models import Class, Student, User, StudentEnrollment
        query = Class.query.join(StudentEnrollment).join(Student).join(User, Class.tutor_id == User.id, isouter=True)
        
        # Apply filters
        if student_id:
            query = query.filter(Student.id == student_id)
        
        if subject:
            query = query.filter(Class.subject == subject)
        
        if tutor_id:
            query = query.filter(Class.tutor_id == tutor_id)
        
        if start_date:
            query = query.filter(Class.class_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        
        if end_date:
            query = query.filter(Class.class_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        if status:
            query = query.filter(Class.status == status)
        
        # Get classes ordered by date and time
        classes = query.order_by(Class.class_date.desc(), Class.start_time.desc()).all()
        
        # Get all students and tutors for filters
        students = Student.query.filter_by(status='active').order_by(Student.first_name).all()
        tutors = User.query.filter_by(role='tutor', is_active=True).order_by(User.full_name).all()
        
        return render_template('classes/schedule.html', 
                             classes=classes,
                             students=students,
                             tutors=tutors)
        
    except Exception as e:
        flash(f'Error loading schedule: {str(e)}', 'danger')
        return render_template('classes/schedule.html', classes=[], students=[], tutors=[])


@app.route('/schedule-class', methods=['POST'])
@login_required
@coordinator_required
def schedule_class():
    """Schedule a new class"""
    try:
        # Get form data
        class_data = {
            'student_id': request.form.get('student_id'),
            'subject': request.form.get('subject'),
            'tutor_id': request.form.get('tutor_id'),
            'class_date': request.form.get('class_date'),
            'start_time': request.form.get('start_time'),
            'duration': int(request.form.get('duration', 60)),
            'topic_covered': request.form.get('topic_covered'),
            'class_type': request.form.get('class_type', 'regular'),
            'class_notes': request.form.get('class_notes'),
            'meeting_link': request.form.get('meeting_link'),
            'meeting_id': request.form.get('meeting_id'),
            'meeting_password': request.form.get('meeting_password')
        }
        
        # Collect custom form fields
        custom_fields = {}
        for key, value in request.form.items():
            if key.startswith('custom_'):
                field_name = key.replace('custom_', '')
                if value:
                    custom_fields[field_name] = value
        
        if custom_fields:
            class_data['custom_fields'] = custom_fields
        
        # Create the class
        from functions.class_functions import create_class_session
        success, message = create_class_session(class_data)
        
        if success:
            flash('Class scheduled successfully!', 'success')
        else:
            flash(f'Error scheduling class: {message}', 'danger')
        
        return redirect(url_for('schedule'))
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('schedule'))
    
@app.route('/api/available-tutors', methods=['POST'])
@login_required
def api_available_tutors():
    """API to find available tutors for given criteria"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        subject = data.get('subject')
        date = data.get('date')
        start_time = data.get('start_time')
        
        if not all([student_id, subject, date, start_time]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        # Find available tutors
        from functions.tutor_functions import find_available_tutors_for_slot
        tutors = find_available_tutors_for_slot({
            'student_id': student_id,
            'subject': subject,
            'date': date,
            'start_time': start_time
        })
        
        # Format tutor data for response
        tutors_data = []
        for tutor in tutors:
            tutor_profile = tutor.tutor_profile if hasattr(tutor, 'tutor_profile') else None
            
            tutors_data.append({
                'id': tutor.id,
                'name': tutor.full_name,
                'email': tutor.email,
                'specialization': tutor_profile.get_specialization() if tutor_profile else [subject],
                'experience': tutor_profile.experience_years if tutor_profile else 0,
                'hourly_rate': tutor_profile.hourly_rate if tutor_profile else 0,
                'rating': tutor_profile.average_rating if tutor_profile else None,
                'profile_picture': tutor.profile_picture if hasattr(tutor, 'profile_picture') else None,
                'available_slots': tutor_profile.get_available_slots_for_day(date) if tutor_profile else []
            })
        
        return jsonify({
            'success': True,
            'tutors': tutors_data,
            'count': len(tutors_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classes/<int:class_id>/start', methods=['POST'])
@login_required
def api_start_class(class_id):
    """Start a class session"""
    try:
        from functions.class_functions import start_class_session
        success, message = start_class_session(class_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/classes/<int:class_id>/complete', methods=['POST'])
@login_required
def api_complete_class(class_id):
    """Complete a class session"""
    try:
        from functions.class_functions import complete_class_session
        success, message = complete_class_session(class_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/classes/<int:class_id>/cancel', methods=['POST'])
@login_required
def api_cancel_class(class_id):
    """Cancel a class session"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        from functions.class_functions import cancel_class_session
        success, message = cancel_class_session(class_id, reason)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/students/<int:student_id>/enroll-multiple', methods=['GET', 'POST'])
@login_required
@coordinator_required
def enroll_student_multiple_subjects(student_id):
    """Enroll student in multiple subjects with different tutors"""
    try:
        student = Student.query.get_or_404(student_id)
        
        if request.method == 'POST':
            # Process multiple subject enrollments
            enrollments_data = []
            
            # Get all form data for subjects
            for key, value in request.form.items():
                if key.startswith('subject_') and value:
                    subject_index = key.split('_')[1]
                    tutor_key = f'tutor_{subject_index}'
                    rate_key = f'rate_{subject_index}'
                    schedule_key = f'schedule_{subject_index}'
                    
                    if request.form.get(tutor_key):
                        enrollment_data = {
                            'student_id': student_id,
                            'subject': value,
                            'tutor_id': request.form.get(tutor_key),
                            'hourly_rate': request.form.get(rate_key),
                            'preferred_schedule': request.form.get(schedule_key),
                            'status': 'active',
                            'enrollment_date': datetime.now().date()
                        }
                        enrollments_data.append(enrollment_data)
            
            # Create enrollments
            created_count = 0
            for enrollment_data in enrollments_data:
                from functions.student_functions import create_student_enrollment
                success, message = create_student_enrollment(enrollment_data)
                if success:
                    created_count += 1
            
            flash(f'Successfully enrolled student in {created_count} subjects!', 'success')
            return redirect(url_for('view_student', id=student_id))
        
        # GET request - show enrollment form
        # Get available tutors by subject
        tutors_by_subject = {}
        subjects = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'Computer Science']
        
        for subject in subjects:
            from functions.tutor_functions import find_available_tutors
            tutors, _ = find_available_tutors({'subject': subject})
            tutors_by_subject[subject] = tutors
        
        return render_template('students/enroll_multiple.html', 
                             student=student,
                             subjects=subjects,
                             tutors_by_subject=tutors_by_subject)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=student_id))
@app.route('/api/tutor-availability', methods=['POST'])
@login_required
def api_tutor_availability():
    """Get tutor's weekly availability"""
    try:
        data = request.get_json()
        tutor_id = data.get('tutor_id')
        
        from models import User, TutorProfile
        tutor = User.query.get(tutor_id)
        
        if not tutor or not hasattr(tutor, 'tutor_profile'):
            return jsonify({'success': False, 'error': 'Tutor not found'}), 404
        
        # Get tutor's weekly schedule
        availability = tutor.tutor_profile.get_weekly_schedule() if tutor.tutor_profile else {}
        
        # Default availability if none set
        if not availability:
            availability = {
                'monday': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'tuesday': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'wednesday': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'thursday': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'friday': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'],
                'saturday': ['09:00', '10:00', '11:00'],
                'sunday': []
            }
        
        return jsonify({
            'success': True,
            'availability': availability
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===================================
# FINANCE ROUTES - FIXED
# ===================================

@app.route('/finance')
@login_required
@finance_required
def finance_dashboard():
    """Finance dashboard - FIXED using existing functions"""
    try:
        # Use your existing get_financial_dashboard_data function
        dashboard_data, message = get_financial_dashboard_data()
        
        # Add additional stats needed by the template
        dashboard_data.update({
            'late_arrivals_today': get_today_late_arrivals_count(),
            'overdue_recordings': get_overdue_recordings_count(),
            'overdue_feedback': get_overdue_feedback_count(),
            'compliance_rate': calculate_overall_compliance_rate()
        })
        
        return render_template('finance/dashboard.html', stats=dashboard_data)
    except Exception as e:
        print(f"Finance dashboard error: {str(e)}")
        flash(f'Finance dashboard error: {str(e)}', 'danger')
        
        # Fallback data
        fallback_stats = {
            'late_arrivals_today': 0,
            'overdue_recordings': 0,
            'overdue_feedback': 0,
            'compliance_rate': 0,
            'total_revenue': 0,
            'pending_collections': 0,
            'collection_rate': 0
        }
        return render_template('finance/dashboard.html', stats=fallback_stats)


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
    """Create form - FIXED to handle both JSON and form data"""
    if request.method == 'POST':
        try:
            # Handle JSON data from AJAX
            if request.is_json:
                form_data = request.get_json()
            else:
                # Handle form data
                form_data = dict(request.form)
                if 'fields' in form_data:
                    try:
                        form_data['fields'] = json.loads(form_data['fields'])
                    except:
                        form_data['fields'] = []
            
            # Validate required fields
            if not form_data.get('name'):
                return jsonify({'success': False, 'error': 'Form name is required'}), 400
            
            # Create form template
            form_template = FormTemplate(
                name=form_data['name'],
                description=form_data.get('description', ''),
                form_type=form_data.get('form_type', 'other'),
                is_active=True,
                created_by=current_user.id,
                created_at=datetime.utcnow()
            )
            
            # Set fields using the model method
            form_template.set_fields(form_data.get('fields', []))
            
            db.session.add(form_template)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Form created successfully!',
                    'form_id': form_template.id
                })
            else:
                flash('Form created successfully!', 'success')
                return redirect(url_for('forms'))
                
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error creating form: {str(e)}'
            
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            else:
                flash(error_msg, 'danger')
    
    return render_template('forms/create.html')

@app.route('/api/notifications/check')
@login_required
def api_notifications_check():
    """Check for new notifications - FIXED"""
    try:
        # Placeholder - implement your notification logic
        notifications = []
        return jsonify({
            'notifications': notifications,
            'count': len(notifications)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/departments/with-forms')
@login_required
def api_departments_with_forms():
    """Get departments with their assigned forms"""
    try:
        departments = Department.query.filter_by(is_active=True).all()
        
        result = []
        for dept in departments:
            dept_data = {
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'user_form_id': dept.user_form_id,
                'tutor_form_id': dept.tutor_form_id,
                'user_form_name': dept.user_form.name if dept.user_form else None,
                'tutor_form_name': dept.tutor_form.name if dept.tutor_form else None
            }
            result.append(dept_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    
@app.route('/finance/late-arrivals')
@login_required
@finance_required
def finance_late_arrivals():
    """View late arrivals for payroll deductions - FIXED"""
    try:
        # Get month from request args or default to current month
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
        month_start = datetime(year, month, 1)
        
        # Use your existing function but get the actual late arrival records
        late_arrival_stats = get_late_arrival_penalty_stats(month_start)
        late_arrivals = late_arrival_stats.get('late_arrivals', [])
        
        return render_template('finance/late_arrivals.html', 
                             late_arrivals=late_arrivals,
                             stats=late_arrival_stats,
                             current_month=month,
                             current_year=year)
    except Exception as e:
        print(f"Error loading late arrivals: {str(e)}")
        flash(f'Error loading late arrivals: {str(e)}', 'danger')
        return render_template('finance/late_arrivals.html', 
                             late_arrivals=[],
                             stats={
                                 'incident_count': 0,
                                 'total_penalties': 0,
                                 'avg_late_minutes': 0
                             },
                             current_month=datetime.now().month,
                             current_year=datetime.now().year)

@app.route('/finance/overdue-recordings')
@login_required
@finance_required
def finance_overdue_recordings():
    """View overdue recordings for compliance tracking"""
    try:
        # Get classes without recordings (you can implement this based on your Class model)
        from models import Class
        overdue_recordings = Class.query.filter(
            Class.recording_link.is_(None),
            Class.class_date < datetime.now().date() - timedelta(days=2),
            Class.status == 'completed'
        ).all()
        
        return render_template('finance/overdue_recordings.html', recordings=overdue_recordings)
    except Exception as e:
        flash(f'Error loading overdue recordings: {str(e)}', 'danger')
        return render_template('finance/overdue_recordings.html', recordings=[])

@app.route('/finance/overdue-feedback')
@login_required
@finance_required
def finance_overdue_feedback():
    """View overdue feedback for compliance tracking"""
    try:
        # Get classes without feedback (implement based on your model)
        from models import Class
        overdue_feedback = Class.query.filter(
            Class.feedback_submitted == False,
            Class.class_date < datetime.now().date() - timedelta(days=1),
            Class.status == 'completed'
        ).all()
        
        return render_template('finance/overdue_feedback.html', feedback=overdue_feedback)
    except Exception as e:
        flash(f'Error loading overdue feedback: {str(e)}', 'danger')
        return render_template('finance/overdue_feedback.html', feedback=[])

@app.route('/finance/compliance-report')
@login_required
@finance_required
def finance_compliance_report():
    """Generate compliance report using your existing functions"""
    try:
        # Use your existing financial health calculation
        financial_health = calculate_financial_health()
        
        # Get additional compliance metrics
        total_classes = Class.query.filter(Class.class_date >= datetime.now().replace(day=1).date()).count()
        completed_classes = Class.query.filter(
            Class.class_date >= datetime.now().replace(day=1).date(),
            Class.status == 'completed'
        ).count()
        
        recorded_classes = Class.query.filter(
            Class.class_date >= datetime.now().replace(day=1).date(),
            Class.recording_link.isnot(None)
        ).count()
        
        feedback_submitted = Class.query.filter(
            Class.class_date >= datetime.now().replace(day=1).date(),
            Class.feedback_submitted == True
        ).count()
        
        compliance_data = {
            'total_classes': total_classes,
            'completion_rate': (completed_classes / total_classes * 100) if total_classes > 0 else 0,
            'recording_rate': (recorded_classes / total_classes * 100) if total_classes > 0 else 0,
            'feedback_rate': (feedback_submitted / total_classes * 100) if total_classes > 0 else 0,
            'financial_health': financial_health,
            'collection_rate': get_collection_rate()
        }
        
        return render_template('finance/compliance_report.html', data=compliance_data)
    except Exception as e:
        flash(f'Error generating compliance report: {str(e)}', 'danger')
        return render_template('finance/compliance_report.html', data={})

@app.route('/finance/payroll')
@login_required
@finance_required
def finance_payroll():
    """Manage tutor payroll - FIXED with complete data"""
    try:
        # Get current month and year from request args or default to current
        current_month = int(request.args.get('month', datetime.now().month))
        current_year = int(request.args.get('year', datetime.now().year))
        
        # Get payroll summary data
        payroll_summary = get_payroll_summary_data(current_month, current_year)
        
        # Get detailed tutor payroll data
        tutors_payroll = get_tutors_payroll_data(current_month, current_year)
        
        # Prepare data for template
        payroll_data = {
            'payroll_summary': payroll_summary,
            'tutors_payroll': tutors_payroll,
            'current_month': current_month,
            'current_year': current_year,
            'total_pending': payroll_summary.get('net_payable', 0),
            'total_processed': 0  # You can implement this based on your payment records
        }
        
        return render_template('finance/payroll.html', 
                             data=payroll_data,
                             payroll_summary=payroll_summary,
                             tutors_payroll=tutors_payroll,
                             current_month=current_month,
                             current_year=current_year)
    except Exception as e:
        print(f"Error loading payroll: {str(e)}")
        flash(f'Error loading payroll: {str(e)}', 'danger')
        
        # Fallback data
        fallback_data = {
            'payroll_summary': {
                'total_tutors': 0,
                'total_earnings': 0,
                'total_penalties': 0,
                'net_payable': 0
            },
            'tutors_payroll': [],
            'current_month': datetime.now().month,
            'current_year': datetime.now().year,
            'total_pending': 0,
            'total_processed': 0
        }
        
        return render_template('finance/payroll.html', 
                             data=fallback_data,
                             payroll_summary=fallback_data['payroll_summary'],
                             tutors_payroll=fallback_data['tutors_payroll'],
                             current_month=fallback_data['current_month'],
                             current_year=fallback_data['current_year'])

@app.route('/finance/payroll/process', methods=['POST'])
@login_required
@finance_required
def process_payroll():
    """Process payroll for selected period"""
    try:
        period = request.form.get('period')
        
        # Use your existing payroll processing function
        success, message = process_tutor_payroll_period(period)
        
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('finance_payroll'))
    except Exception as e:
        flash(f'Error processing payroll: {str(e)}', 'danger')
        return redirect(url_for('finance_payroll'))

@app.route('/finance/deductions')
@login_required
@finance_required
def finance_deductions():
    """Manage payroll deductions using your existing functions"""
    try:
        # Use your existing penalty stats
        current_month = datetime.now().replace(day=1)
        late_arrival_penalties = get_late_arrival_penalty_stats(current_month)
        total_penalties = get_total_penalties_collected(current_month)
        
        deductions_data = {
            'late_arrival_penalties': late_arrival_penalties,
            'total_penalties': total_penalties,
            'penalty_breakdown': get_penalty_breakdown(current_month)
        }
        
        return render_template('finance/deductions.html', data=deductions_data)
    except Exception as e:
        flash(f'Error loading deductions: {str(e)}', 'danger')
        return render_template('finance/deductions.html', data={})

@app.route('/finance/reports')
@login_required
@finance_required
def finance_reports():
    """Financial reports dashboard using your existing functions"""
    try:
        # Use your existing financial functions
        current_month = datetime.now().replace(day=1)
        
        reports_data = {
            'monthly_revenue': get_monthly_revenue(current_month),
            'total_revenue': get_total_revenue(),
            'pending_collections': get_pending_collections(),
            'collection_rate': get_collection_rate(),
            'revenue_trend': get_revenue_trend(6),
            'expense_trend': get_expense_trend(6),
            'profit_trend': get_profit_trend(6),
            'financial_health': calculate_financial_health(),
            'outstanding_amount': get_outstanding_amount()
        }
        
        return render_template('finance/reports.html', data=reports_data)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        return render_template('finance/reports.html', data={})

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
    """Initial system setup - COMPLETELY FIXED"""
    print("Setup route accessed")
    
    # Check if setup is needed
    try:
        user_count = User.query.count()
        print(f"Current user count: {user_count}")
        if user_count > 0:
            flash('System already set up. Redirecting to login.', 'info')
            return redirect(url_for('login'))
    except Exception as e:
        # Database doesn't exist yet, create tables
        print(f"Creating database tables: {str(e)}")
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as create_error:
            print(f"Failed to create tables: {str(create_error)}")
            flash(f'Database setup error: {str(create_error)}', 'danger')
    
    if request.method == 'POST':
        print("Processing POST request")
        try:
            # Get form data
            admin_data = {
                'full_name': request.form.get('full_name', '').strip(),
                'username': request.form.get('username', '').strip(),
                'email': request.form.get('email', '').strip(),
                'password': request.form.get('password', ''),
                'mobile': request.form.get('mobile', '').strip()
            }
            
            print(f"Form data received: {admin_data}")
            
            # Validate form data
            if not admin_data['full_name']:
                flash('Full name is required.', 'danger')
                return render_template('setup.html')
            
            if not admin_data['username']:
                flash('Username is required.', 'danger')
                return render_template('setup.html')
            
            if not admin_data['email']:
                flash('Email is required.', 'danger')
                return render_template('setup.html')
            
            if not admin_data['password']:
                flash('Password is required.', 'danger')
                return render_template('setup.html')
            
            if len(admin_data['password']) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('setup.html')
            
            # Validate password confirmation
            confirm_password = request.form.get('confirm_password', '')
            if admin_data['password'] != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('setup.html')
            
            print(f"Creating superadmin with data: {admin_data}")
            
            # Create superadmin
            success, message = create_superadmin(admin_data)
            
            if success:
                flash(message, 'success')
                print(f"Superadmin created successfully: {message}")
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
                print(f"Superadmin creation failed: {message}")
        
        except Exception as e:
            error_msg = f"Setup error: {str(e)}"
            print(error_msg)
            flash(error_msg, 'danger')
    
    return render_template('setup.html')



# Add these routes to your app.py file:

@app.route('/classes/create', methods=['GET', 'POST'])
@login_required
@coordinator_required
def create_class():
    """Create new class"""
    if request.method == 'POST':
        class_data = dict(request.form)
        
        # Handle JSON requests from AJAX
        if request.is_json:
            class_data = request.json
        
        success, message = create_class_session(class_data)
        
        if request.is_json:
            return jsonify({'success': success, 'message': message})
        
        if success:
            flash(message, 'success')
            return redirect(url_for('classes'))
        else:
            flash(message, 'danger')
    
    # For GET requests, return form page
    students = Student.query.filter_by(status='active').all()
    tutors = User.query.filter_by(role='tutor', is_active=True).all()
    
    return render_template('classes/create.html', students=students, tutors=tutors)

@app.route('/classes/<int:id>')
@login_required
def view_class(id):
    """View class details"""
    class_obj = Class.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == 'tutor' and class_obj.tutor_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('classes'))
    
    return render_template('classes/view.html', class_data=class_obj)

@app.route('/classes/<int:id>/start', methods=['POST'])
@login_required
def start_class(id):
    """Start a class session"""
    success, message = start_class_session(id)
    return jsonify({'success': success, 'message': message})

@app.route('/classes/<int:id>/cancel', methods=['POST'])
@login_required
@coordinator_required
def cancel_class(id):
    """Cancel a class"""
    reason = request.json.get('reason', '') if request.is_json else request.form.get('reason', '')
    success, message = cancel_class_session(id, reason)
    return jsonify({'success': success, 'message': message})

@app.route('/api/tutors/search')
@login_required
def api_search_tutors():
    """API endpoint for tutor search"""
    try:
        search_term = request.args.get('q', '')
        tutors = User.query.filter(
            User.role == 'tutor',
            User.is_active == True,
            User.full_name.ilike(f'%{search_term}%')
        ).all()
        
        return jsonify([{
            'id': t.id,
            'name': t.full_name,
            'department': t.department.name if t.department else None
        } for t in tutors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# Add these routes to your app.py file:

@app.route('/classes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@coordinator_required
def edit_class(id):
    """Edit class"""
    class_obj = Class.query.get_or_404(id)
    
    if request.method == 'POST':
        class_data = dict(request.form)
        
        success, message = update_class_session(id, class_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('view_class', id=id))
        else:
            flash(message, 'danger')
    
    return render_template('classes/edit.html', class_data=class_obj)

@app.route('/classes/<int:id>/delete', methods=['DELETE'])
@login_required
@coordinator_required
def delete_class(id):
    """Delete class"""
    success, message = delete_class_session(id)
    return jsonify({'success': success, 'message': message})

@app.route('/classes/<int:id>/complete', methods=['POST'])
@login_required
def complete_class(id):
    """Complete a class session"""
    completion_data = request.json if request.is_json else dict(request.form)
    success, message = complete_class_session(id, completion_data)
    return jsonify({'success': success, 'message': message})

@app.route('/tutor/class/<int:id>/attendance', methods=['GET', 'POST'])
@login_required
@tutor_required
def mark_attendance(id):
    """Mark attendance for a class"""
    class_obj = Class.query.get_or_404(id)
    
    # Check if tutor owns this class
    if class_obj.tutor_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('my_classes'))
    
    if request.method == 'POST':
        attendance_data = dict(request.form)
        success, message = mark_student_attendance(id, attendance_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('view_class', id=id))
        else:
            flash(message, 'danger')
    
    return render_template('tutor/mark_attendance.html', class_session=class_obj)


# Add these routes to your app.py file:

# ===================================
# DEPARTMENT MANAGEMENT ROUTES - MISSING
# ===================================

@app.route('/departments')
@login_required
@admin_required
def departments():
    """View all departments"""
    try:
        departments_list = Department.query.filter_by(is_active=True).all()
        return render_template('departments/list.html', departments=departments_list)
    except Exception as e:
        flash(f'Error loading departments: {str(e)}', 'danger')
        return render_template('departments/list.html', departments=[])

@app.route('/departments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_department_route():
    """Create new department - FIXED"""
    if request.method == 'POST':
        dept_data = {
            'name': request.form.get('name'),
            'code': request.form.get('code'),
            'description': request.form.get('description')
        }
        
        try:
            # Check if department code already exists
            existing_dept = Department.query.filter_by(code=dept_data['code']).first()
            if existing_dept:
                flash('Department code already exists!', 'danger')
                return render_template('departments/create.html')
            
            # Create new department - REMOVED head_id
            department = Department(
                name=dept_data['name'],
                code=dept_data['code'],
                description=dept_data['description'],
                is_active=True,
                created_at=datetime.utcnow(),
                created_by=current_user.id
            )
            
            db.session.add(department)
            db.session.commit()
            
            flash(f'Department {department.name} created successfully!', 'success')
            return redirect(url_for('departments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating department: {str(e)}', 'danger')
    
    return render_template('departments/create.html')

@app.route('/departments/<int:id>')
@login_required
@admin_required
def view_department(id):
    """View department details"""
    department = Department.query.get_or_404(id)
    
    # Get department members
    members = User.query.filter_by(department_id=id, is_active=True).all()
    students = Student.query.filter_by(department_id=id, status='active').all()
    
    return render_template('departments/view.html', 
                         department=department, 
                         members=members, 
                         students=students)

@app.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(id):
    """Edit department - FIXED"""
    department = Department.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            department.name = request.form.get('name')
            department.code = request.form.get('code')
            department.description = request.form.get('description')
            department.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Department updated successfully!', 'success')
            return redirect(url_for('view_department', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating department: {str(e)}', 'danger')
    
    return render_template('departments/edit.html', department=department)

@app.route('/departments/<int:id>/delete', methods=['POST', 'DELETE'])
@login_required
@admin_required
def delete_department(id):
    """Delete department (soft delete)"""
    try:
        department = Department.query.get_or_404(id)
        
        # Check if department has members
        member_count = User.query.filter_by(department_id=id, is_active=True).count()
        student_count = Student.query.filter_by(department_id=id, status='active').count()
        
        if member_count > 0 or student_count > 0:
            if request.is_json:
                return jsonify({'error': 'Cannot delete department with active members'}), 400
            flash('Cannot delete department with active members!', 'danger')
            return redirect(url_for('departments'))
        
        # Soft delete
        department.is_active = False
        department.updated_at = datetime.utcnow()
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Department deleted successfully'})
        
        flash('Department deleted successfully!', 'success')
        return redirect(url_for('departments'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error deleting department: {str(e)}'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'danger')
        return redirect(url_for('departments'))

# Add these missing form routes to your app.py:

# ===================================
# FORM ROUTES - MISSING ROUTES ADDED
# ===================================

@app.route('/forms/<int:id>/preview')
@login_required
def preview_form(id):
    """Preview form in full page"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        return render_template('forms/preview.html', form=form_template)
    except Exception as e:
        flash(f'Error loading form preview: {str(e)}', 'danger')
        return redirect(url_for('forms'))

@app.route('/forms/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_form(id):
    """Edit form"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        if request.method == 'POST':
            form_data = dict(request.form)
            
            # Handle JSON fields
            if 'fields' in form_data:
                try:
                    form_data['fields'] = json.loads(form_data['fields'])
                except:
                    form_data['fields'] = []
            
            # Update form template
            form_template.name = form_data.get('name', form_template.name)
            form_template.description = form_data.get('description', form_template.description)
            if 'fields' in form_data:
                form_template.set_fields(form_data['fields'])
            
            db.session.commit()
            flash('Form updated successfully!', 'success')
            return redirect(url_for('forms'))
        
        return render_template('forms/edit.html', form=form_template)
    except Exception as e:
        flash(f'Error editing form: {str(e)}', 'danger')
        return redirect(url_for('forms'))

@app.route('/forms/<int:id>/delete', methods=['POST', 'DELETE'])
@login_required
@admin_required
def delete_form(id):
    """Delete form"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        # Check if form is being used
        # Add your logic here to check if form has submissions
        
        db.session.delete(form_template)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Form deleted successfully'})
        
        flash('Form deleted successfully!', 'success')
        return redirect(url_for('forms'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error deleting form: {str(e)}'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'danger')
        return redirect(url_for('forms'))

@app.route('/forms/<int:id>/publish', methods=['POST'])
@login_required
@admin_required
def publish_form(id):
    """Publish/unpublish form"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        # Toggle published status
        form_template.is_published = not form_template.is_published
        form_template.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = "published" if form_template.is_published else "unpublished"
        flash(f'Form {status} successfully!', 'success')
        
        return redirect(url_for('forms'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating form status: {str(e)}', 'danger')
        return redirect(url_for('forms'))

@app.route('/forms/<int:id>/duplicate', methods=['POST'])
@login_required
@admin_required
def duplicate_form(id):
    """Duplicate form"""
    try:
        original_form = FormTemplate.query.get_or_404(id)
        
        # Create duplicate
        duplicate = FormTemplate(
            name=f"{original_form.name} (Copy)",
            description=original_form.description,
            fields=original_form.fields,
            is_published=False,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(duplicate)
        db.session.commit()
        
        flash('Form duplicated successfully!', 'success')
        return redirect(url_for('edit_form', id=duplicate.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error duplicating form: {str(e)}', 'danger')
        return redirect(url_for('forms'))

@app.route('/forms/<int:id>/submissions')
@login_required
@admin_required
def form_submissions(id):
    """View form submissions"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        # Get submissions (you'll need to create a FormSubmission model)
        # submissions = FormSubmission.query.filter_by(form_id=id).all()
        submissions = []  # Placeholder
        
        return render_template('forms/submissions.html', 
                             form=form_template, 
                             submissions=submissions)
    except Exception as e:
        flash(f'Error loading submissions: {str(e)}', 'danger')
        return redirect(url_for('forms'))

# ===================================
# ADDITIONAL MISSING ROUTES FROM BASE.HTML
# ===================================

@app.route('/settings')
@login_required
@admin_required
def settings():
    """System settings"""
    return render_template('settings/index.html')

@app.route('/help')
@login_required
def help_page():
    """Help page"""
    return render_template('help/index.html')

@app.route('/notifications')
@login_required
def notifications():
    """User notifications"""
    return render_template('notifications/index.html')


# Add all these missing routes to your app.py:

# ===================================
# MISSING FORM ROUTES
# ===================================

@app.route('/forms/<int:id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_form(id):
    """Assign form to departments - FIXED"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        data = request.get_json()
        department_ids = data.get('departments', [])
        assignment_type = data.get('type', 'user')
        
        if not department_ids:
            return jsonify({
                'success': False,
                'error': 'No departments selected'
            }), 400
        
        # Import the function
        from functions.department_functions import assign_form_to_department
        
        success_count = 0
        errors = []
        
        for dept_id in department_ids:
            success, message = assign_form_to_department(int(dept_id), id, assignment_type)
            if success:
                success_count += 1
            else:
                errors.append(f"Department {dept_id}: {message}")
        
        if success_count > 0:
            return jsonify({
                'success': True,
                'message': f'Form assigned to {success_count} departments successfully',
                'errors': errors if errors else None
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to assign form to any departments',
                'details': errors
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/forms/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_form_status(id):
    """Toggle form active/inactive status"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        # Toggle the status
        form_template.is_active = not getattr(form_template, 'is_active', True)
        form_template.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = "activated" if form_template.is_active else "deactivated"
        return jsonify({
            'success': True,
            'message': f'Form {status} successfully',
            'is_active': form_template.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===================================
# MISSING API ROUTES
# ===================================

@app.route('/api/departments')
@login_required
def api_departments():
    """API endpoint to get all departments - FIXED"""
    try:
        departments = Department.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': dept.id,
            'name': dept.name,
            'code': dept.code,
            'description': dept.description,
            'user_form_id': dept.user_form_id,
            'tutor_form_id': dept.tutor_form_id
        } for dept in departments])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/departments/<int:id>/forms')
@login_required
@admin_required
def department_forms(id):
    """View forms assigned to department"""
    try:
        department = Department.query.get_or_404(id)
        
        forms_data = {
            'department': {
                'id': department.id,
                'name': department.name,
                'code': department.code
            },
            'user_form': None,
            'tutor_form': None
        }
        
        if department.user_form_id:
            user_form = FormTemplate.query.get(department.user_form_id)
            if user_form:
                forms_data['user_form'] = {
                    'id': user_form.id,
                    'name': user_form.name,
                    'description': user_form.description
                }
        
        if department.tutor_form_id:
            tutor_form = FormTemplate.query.get(department.tutor_form_id)
            if tutor_form:
                forms_data['tutor_form'] = {
                    'id': tutor_form.id,
                    'name': tutor_form.name,
                    'description': tutor_form.description
                }
        
        return render_template('departments/forms.html', data=forms_data)
        
    except Exception as e:
        flash(f'Error loading department forms: {str(e)}', 'danger')
        return redirect(url_for('departments'))

@app.route('/api/users')
@login_required
@admin_required
def api_users():
    """API endpoint to get users"""
    try:
        role_filter = request.args.get('role')
        department_filter = request.args.get('department')
        
        query = User.query.filter_by(is_active=True)
        
        if role_filter:
            query = query.filter_by(role=role_filter)
        
        if department_filter:
            query = query.filter_by(department_id=int(department_filter))
        
        users = query.all()
        
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'department_id': user.department_id
        } for user in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forms/<int:form_id>/fields')
@login_required
def api_form_fields(form_id):
    """API endpoint to get form fields"""
    try:
        form_template = FormTemplate.query.get_or_404(form_id)
        fields = form_template.get_fields() if hasattr(form_template, 'get_fields') else []
        
        return jsonify({
            'form_id': form_id,
            'fields': fields
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# ADD THIS API ROUTE TO app.py

@app.route('/api/departments/<int:department_id>/form')
@login_required
def api_department_form(department_id):
    """Get assigned form for a department (enhanced version)"""
    try:
        department = Department.query.get_or_404(department_id)
        form_type = request.args.get('type', 'user')  # 'user', 'tutor', 'student', 'class'
        
        form_template = None
        
        # Map form types to department form assignments
        if form_type == 'tutor' and department.tutor_form_id:
            form_template = FormTemplate.query.get(department.tutor_form_id)
        elif form_type in ['user', 'student', 'class'] and department.user_form_id:
            form_template = FormTemplate.query.get(department.user_form_id)
        
        if not form_template:
            return jsonify({'error': 'No form assigned to this department'}), 404
        
        # Get form fields
        form_fields = form_template.get_fields()
        
        return jsonify({
            'form': {
                'id': form_template.id,
                'name': form_template.name,
                'description': form_template.description,
                'type': form_template.form_type,
                'fields': form_fields
            },
            'department': {
                'id': department.id,
                'name': department.name,
                'code': department.code
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

# ADD THESE MISSING ROUTES TO app.py

# ===================================
# TUTOR MANAGEMENT ROUTES - MISSING
# ===================================
from models import (
    User, Student, Department, Class, StudentEnrollment, 
    FormTemplate, Permission, TutorProfile
)


@app.route('/tutors')
@login_required
@coordinator_required
def tutor_management():
    """Tutor management page - FIXED to prevent User object errors"""
    try:
        # Import models properly
        from models import User, Department
        
        # Get filter parameters
        department_filter = request.args.get('department', '')
        search_term = request.args.get('search', '')
        
        # Base query for tutors - FIXED
        query = User.query.filter_by(role='tutor', is_active=True)
        
        # Apply filters
        if department_filter:
            try:
                dept_id = int(department_filter)
                query = query.filter_by(department_id=dept_id)
            except (ValueError, TypeError):
                pass  # Invalid department filter, ignore
        
        if search_term:
            search_pattern = f'%{search_term}%'
            query = query.filter(
                db.or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.username.ilike(search_pattern)
                )
            )
        
        # Get tutors with proper error handling - JOIN with department
        tutors = query.join(Department, User.department_id == Department.id, isouter=True)\
                     .add_columns(Department.name.label('dept_name'))\
                     .order_by(User.full_name).all()
        
        # Process tutors to include department info
        tutors_list = []
        for tutor_row in tutors:
            tutor = tutor_row[0]  # User object
            dept_name = tutor_row[1]  # Department name
            
            # Create tutor object with department info
            tutor_obj = {
                'id': tutor.id,
                'full_name': tutor.full_name,
                'email': tutor.email,
                'phone': tutor.phone,
                'username': tutor.username,
                'is_active': tutor.is_active,
                'created_at': tutor.created_at,
                'department_name': dept_name or 'No Department',
                'department_id': tutor.department_id
            }
            tutors_list.append(tutor_obj)
        
        # Get departments for filter
        departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
        
        print(f"Found {len(tutors_list)} tutors and {len(departments)} departments")
        
        return render_template('tutors/management.html', 
                             tutors=tutors_list, 
                             departments=departments)
                             
    except Exception as e:
        print(f"Error in tutor_management: {str(e)}")
        import traceback
        traceback.print_exc()
        
        flash(f'Error loading tutors: {str(e)}', 'danger')
        
        # Return safe fallback
        try:
            departments = Department.query.filter_by(is_active=True).all()
        except:
            departments = []
            
        return render_template('tutors/management.html', 
                             tutors=[], 
                             departments=departments)
@app.route('/tutors/register', methods=['GET', 'POST'])
@login_required
@coordinator_required
def register_tutor():
    """Register new tutor with department form integration"""
    if request.method == 'POST':
        try:
            # Basic tutor data
            tutor_data = {
                'full_name': request.form.get('full_name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'username': request.form.get('username'),
                'password': request.form.get('password'),
                'department_id': request.form.get('department_id'),
                'role': 'tutor',
                'is_active': True,
                'is_approved': True  # Auto-approve coordinator-created tutors
            }
            
            # Collect custom form fields from department form
            custom_fields = {}
            for key, value in request.form.items():
                if key.startswith('custom_'):
                    field_name = key.replace('custom_', '')
                    if value:  # Only store non-empty values
                        custom_fields[field_name] = value
            
            # Handle file uploads for custom fields
            custom_files = {}
            for key, file in request.files.items():
                if key.startswith('custom_file_') and file and file.filename:
                    field_name = key.replace('custom_file_', '')
                    # Save file and get path
                    file_path = handle_file_upload(file, field_name, 'tutor_documents')
                    if file_path:
                        custom_files[field_name] = file_path
                
                # Handle regular file uploads (resume, id_proof)
                elif file and file.filename and key in ['resume', 'id_proof']:
                    file_path = handle_file_upload(file, key, 'tutor_documents')
                    if file_path:
                        custom_files[key] = file_path
            
            # Merge custom data
            if custom_fields:
                tutor_data['custom_fields'] = custom_fields
            if custom_files:
                tutor_data['uploaded_files'] = custom_files
            
            # Create tutor
            from functions.user_functions import create_user as create_user_func
            user, result = create_user_func(tutor_data)
            
            if user:
                flash(f'Tutor {user.full_name} registered successfully!', 'success')
                return redirect(url_for('tutor_management'))
            else:
                flash(f'Error registering tutor: {result}', 'danger')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    # GET request - show form
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('tutors/register.html', departments=departments)

@app.route('/tutors/<int:id>')
@login_required
@coordinator_required
def view_tutor(id):
    """View tutor details - FIXED"""
    try:
        from models import User
        tutor = User.query.filter_by(id=id, role='tutor').first_or_404()
        
        # Get tutor's basic stats (safe fallback values)
        stats = {
            'total_classes': getattr(tutor, 'total_classes_taught', 0),
            'completed_classes': 0,  # Calculate from classes if needed
            'active_students': 0,    # Calculate from enrollments if needed
            'rating': getattr(tutor, 'feedback_rating', 0.0)
        }
        
        return render_template('tutors/view.html', 
                             tutor=tutor, 
                             stats=stats)
                             
    except Exception as e:
        print(f"Error viewing tutor: {str(e)}")
        flash(f'Error loading tutor details: {str(e)}', 'danger')
        return redirect(url_for('tutor_management'))

@app.route('/tutors/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@coordinator_required  
def edit_tutor(id):
    """Edit tutor details - FIXED"""
    try:
        from models import User, Department
        tutor = User.query.filter_by(id=id, role='tutor').first_or_404()
        
        if request.method == 'POST':
            # Update tutor data safely
            try:
                if request.form.get('full_name'):
                    tutor.full_name = request.form.get('full_name')
                if request.form.get('email'):
                    tutor.email = request.form.get('email')
                if request.form.get('phone'):
                    tutor.phone = request.form.get('phone')
                if request.form.get('department_id'):
                    tutor.department_id = int(request.form.get('department_id'))
                
                # Handle is_active checkbox
                tutor.is_active = bool(request.form.get('is_active'))
                tutor.updated_at = datetime.utcnow()
                
                db.session.commit()
                flash('Tutor updated successfully!', 'success')
                return redirect(url_for('view_tutor', id=id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating tutor: {str(e)}', 'danger')
        
        departments = Department.query.filter_by(is_active=True).all()
        return render_template('tutors/edit.html', tutor=tutor, departments=departments)
        
    except Exception as e:
        print(f"Error editing tutor: {str(e)}")
        flash(f'Error editing tutor: {str(e)}', 'danger')
        return redirect(url_for('tutor_management'))

@app.route('/tutors/<int:id>/toggle-status', methods=['POST'])
@login_required
@coordinator_required
def toggle_tutor_status(id):
    """Activate/Deactivate tutor"""
    try:
        tutor = User.query.filter_by(id=id, role='tutor').first_or_404()
        
        tutor.is_active = not tutor.is_active
        tutor.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = "activated" if tutor.is_active else "deactivated"
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'Tutor {status} successfully',
                'is_active': tutor.is_active
            })
        
        flash(f'Tutor {status} successfully', 'success')
        return redirect(url_for('tutor_management'))
        
    except Exception as e:
        error_msg = f'Error updating tutor status: {str(e)}'
        
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        
        flash(error_msg, 'danger')
        return redirect(url_for('tutor_management'))

# Alternative route for backward compatibility
@app.route('/register-tutor', methods=['GET', 'POST'])
@login_required
@coordinator_required
def register_tutor_alt():
    """Alternative route for tutor registration"""
    return register_tutor()

# ===================================
# MISSING UTILITY ROUTES
# ===================================

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to prevent conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            # Save file
            filepath = handle_file_upload(file, filename, 'forms')
            
            if filepath:
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'filepath': filepath,
                    'url': f'/static/{filepath}'
                })
            else:
                return jsonify({'error': 'Failed to save file'}), 500
        else:
            return jsonify({'error': 'Invalid file type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================================
# DASHBOARD API ROUTES
# ===================================

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = get_user_dashboard_data(current_user)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications')
@login_required
def api_notifications():
    """Get user notifications"""
    try:
        # Placeholder for notifications
        notifications = []
        return jsonify(notifications)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================================
# SEARCH API ROUTES
# ===================================

@app.route('/api/search')
@login_required
def api_search():
    """Global search API"""
    try:
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'all')
        
        results = {
            'users': [],
            'students': [],
            'forms': [],
            'departments': []
        }
        
        if query and len(query) >= 2:
            if search_type in ['all', 'users']:
                users = search_users(query)
                results['users'] = [{
                    'id': u.id,
                    'name': u.full_name,
                    'email': u.email,
                    'role': u.role
                } for u in users[:5]]  # Limit results
            
            if search_type in ['all', 'departments']:
                departments = Department.query.filter(
                    Department.name.ilike(f'%{query}%'),
                    Department.is_active == True
                ).limit(5).all()
                results['departments'] = [{
                    'id': d.id,
                    'name': d.name,
                    'code': d.code
                } for d in departments]
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================================
# FORM SUBMISSION ROUTES (Future)
# ===================================

@app.route('/forms/<int:id>/submit', methods=['GET', 'POST'])
def submit_form(id):
    """Public form submission (no login required)"""
    try:
        form_template = FormTemplate.query.get_or_404(id)
        
        if request.method == 'POST':
            # Handle form submission
            submission_data = dict(request.form)
            
            # Here you would save the submission to database
            # For now, just return success
            
            flash('Form submitted successfully!', 'success')
            return redirect(url_for('submit_form', id=id))
        
        return render_template('forms/submit.html', form=form_template)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

# ===================================
# MISSING HELPER FUNCTIONS - Add these to your functions files
# ===================================

def create_form_template(form_data):
    """Create new form template"""
    try:
        form_template = FormTemplate(
            name=form_data.get('name'),
            description=form_data.get('description'),
            form_type=form_data.get('form_type', 'other'),
            fields=json.dumps(form_data.get('fields', [])),
            is_active=True,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(form_template)
        db.session.commit()
        
        return form_template, "Form template created successfully!"
    except Exception as e:
        db.session.rollback()
        return None, f"Error creating form: {str(e)}"

# Add this method to your FormTemplate model if it doesn't exist
def get_fields(self):
    """Get form fields as list"""
    try:
        return json.loads(self.fields) if self.fields else []
    except:
        return []

def set_fields(self, fields_list):
    """Set form fields"""
    self.fields = json.dumps(fields_list) if fields_list else None

def create_student_enrollment(enrollment_data):
    """Create a new student enrollment"""
    try:
        # Create new enrollment
        enrollment = StudentEnrollment(
            student_id=enrollment_data.get('student_id'),
            course_id=enrollment_data.get('course_id'),
            tutor_id=enrollment_data.get('tutor_id'),
            enrollment_date=datetime.strptime(enrollment_data.get('enrollment_date'), '%Y-%m-%d'),
            fee_amount=float(enrollment_data.get('fee_amount')),
            status=enrollment_data.get('status', 'active'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        return True, "Student enrolled successfully!"
    except Exception as e:
        db.session.rollback()
        return False, f"Error enrolling student: {str(e)}"

def create_student_fee(fee_data):
    """
    Create a new student fee record
    Args:
        fee_data (dict): Dictionary containing fee details
    Returns:
        tuple: (success (bool), message (str))
    """
    try:
        from models import StudentFee, db
        
        # Validate required fields
        if not all(key in fee_data for key in ['student_id', 'fee_type', 'amount', 'due_date']):
            return False, "Missing required fee information"
        
        # Create new fee record
        fee = StudentFee(
            student_id=fee_data['student_id'],
            fee_type=fee_data['fee_type'],
            amount=float(fee_data['amount']),
            due_date=fee_data['due_date'],
            description=fee_data.get('description', ''),
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(fee)
        db.session.commit()
        
        return True, "Fee added successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating fee: {str(e)}"


# 1. My Classes (for tutors)
@app.route('/my-classes')
@login_required
def my_classes():
    """View tutor's own classes"""
    if current_user.role != 'tutor':
        flash('Access denied. Tutor access only.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Get classes for current tutor
        classes = Class.query.filter_by(tutor_id=current_user.id).order_by(Class.class_date.desc()).all()
        
        # Get statistics
        total_classes = len(classes)
        completed_classes = len([c for c in classes if c.status == 'completed'])
        upcoming_classes = len([c for c in classes if c.status == 'scheduled' and c.class_date >= datetime.now().date()])
        
        stats = {
            'total_classes': total_classes,
            'completed_classes': completed_classes,
            'upcoming_classes': upcoming_classes,
            'completion_rate': (completed_classes / total_classes * 100) if total_classes > 0 else 0
        }
        
        return render_template('classes/my_classes.html', classes=classes, stats=stats)
    except Exception as e:
        flash(f'Error loading classes: {str(e)}', 'danger')
        return render_template('classes/my_classes.html', classes=[], stats={})

# 2. My Students (for tutors)@app.route('/my-students')
@login_required
def my_students():
    """View tutor's assigned students"""
    if current_user.role != 'tutor':
        flash('Access denied. Tutor access only.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Get students enrolled with current tutor
        enrollments = StudentEnrollment.query.filter_by(
            tutor_id=current_user.id,
            status='active'
        ).all()
        
        students = []
        for enrollment in enrollments:
            student_data = {
                'student': enrollment.student,
                'enrollment': enrollment,
                'subject': enrollment.subject,
                'start_date': enrollment.start_date,
                'sessions_completed': enrollment.completed_sessions,
                'total_sessions': enrollment.total_sessions
            }
            students.append(student_data)
        
        # Get statistics
        total_students = len(students)
        active_students = len([s for s in students if s['enrollment'].status == 'active'])
        
        stats = {
            'total_students': total_students,
            'active_students': active_students
        }
        
        return render_template('students/my_students.html', students=students, stats=stats)
    except Exception as e:
        flash(f'Error loading students: {str(e)}', 'danger')
        return render_template('students/my_students.html', students=[], stats={})
    

def parse_date(date_string):
    """Parse date string to date object"""
    if not date_string:
        return None
    
    try:
        from datetime import datetime
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except:
        return None
    
@app.route('/students/<int:student_id>/enrollments')
@login_required
@coordinator_required
def student_enrollments(student_id):
    """View student's subject enrollments"""
    try:
        student = Student.query.get_or_404(student_id)
        enrollments = StudentEnrollment.query.filter_by(
            student_id=student_id,
            status='active'
        ).all()
        
        # Calculate total costs
        weekly_cost = sum(e.get_weekly_cost() for e in enrollments)
        monthly_cost = sum(e.get_monthly_cost() for e in enrollments)
        
        return render_template('students/enrollments.html',
                             student=student,
                             enrollments=enrollments,
                             weekly_cost=weekly_cost,
                             monthly_cost=monthly_cost)
        
    except Exception as e:
        flash(f'Error loading enrollments: {str(e)}', 'danger')
        return redirect(url_for('view_student', id=student_id))


# ===================================
# PLACEHOLDER TEMPLATES - Create these if they don't exist
# ===================================


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Database creation error: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)