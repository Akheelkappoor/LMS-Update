# migrate_db.py - DATABASE MIGRATION SCRIPT

"""
Database Migration Script for LMS
This script creates/updates the database schema and handles migrations
"""

import os
import sys
from datetime import datetime
from flask import Flask
from config import Config

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    
    return app

def create_database_tables(app):
    """Create all database tables"""
    with app.app_context():
        from models import db
        
        print("🗄️  Creating database tables...")
        
        try:
            # Drop all tables (use with caution!)
            db.drop_all()
            print("  ✓ Dropped existing tables")
            
            # Create all tables
            db.create_all()
            print("  ✓ Created new tables")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"  ✓ Created {len(tables)} tables: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error creating tables: {str(e)}")
            return False

def create_default_permissions(app):
    """Create default system permissions"""
    with app.app_context():
        from models import db, Permission
        
        print("🔑 Creating default permissions...")
        
        default_permissions = [
            # User Management
            {'name': 'Create Users', 'code': 'create_users', 'description': 'Create new users', 'category': 'user'},
            {'name': 'Edit Users', 'code': 'edit_users', 'description': 'Edit user profiles', 'category': 'user'},
            {'name': 'Delete Users', 'code': 'delete_users', 'description': 'Delete users', 'category': 'user'},
            {'name': 'Approve Users', 'code': 'approve_users', 'description': 'Approve user registrations', 'category': 'user'},
            
            # Student Management
            {'name': 'Create Students', 'code': 'create_students', 'description': 'Create student records', 'category': 'student'},
            {'name': 'Edit Students', 'code': 'edit_students', 'description': 'Edit student information', 'category': 'student'},
            {'name': 'Delete Students', 'code': 'delete_students', 'description': 'Delete student records', 'category': 'student'},
            {'name': 'Manage Enrollments', 'code': 'manage_enrollments', 'description': 'Manage student enrollments', 'category': 'student'},
            
            # Class Management
            {'name': 'View Own Classes', 'code': 'view_own_classes', 'description': 'View own teaching classes', 'category': 'class'},
            {'name': 'View Department Classes', 'code': 'view_department_classes', 'description': 'View department classes', 'category': 'class'},
            {'name': 'View All Classes', 'code': 'view_all_classes', 'description': 'View all classes in system', 'category': 'class'},
            {'name': 'Create Classes', 'code': 'create_classes', 'description': 'Create new classes', 'category': 'class'},
            {'name': 'Mark Attendance', 'code': 'mark_attendance', 'description': 'Mark student attendance', 'category': 'class'},
            {'name': 'Upload Recordings', 'code': 'upload_recordings', 'description': 'Upload class recordings', 'category': 'class'},
            
            # Financial Management
            {'name': 'View Own Payroll', 'code': 'view_own_payroll', 'description': 'View personal payroll', 'category': 'finance'},
            {'name': 'Manage All Payroll', 'code': 'manage_all_payroll', 'description': 'Manage all payroll records', 'category': 'finance'},
            {'name': 'Process Payments', 'code': 'process_payments', 'description': 'Process fee payments', 'category': 'finance'},
            {'name': 'Manage Fees', 'code': 'manage_fees', 'description': 'Manage student fees', 'category': 'finance'},
            
            # Department Management
            {'name': 'Manage Departments', 'code': 'manage_departments', 'description': 'Create and manage departments', 'category': 'department'},
            {'name': 'View Department Analytics', 'code': 'view_department_analytics', 'description': 'View department performance', 'category': 'department'},
            
            # System Administration
            {'name': 'System Settings', 'code': 'system_settings', 'description': 'Manage system settings', 'category': 'system'},
            {'name': 'Manage Forms', 'code': 'manage_forms', 'description': 'Create and manage forms', 'category': 'system'},
            {'name': 'View All Reports', 'code': 'view_all_reports', 'description': 'Access all reports', 'category': 'system'},
        ]
        
        created_count = 0
        for perm_data in default_permissions:
            existing = Permission.query.filter_by(code=perm_data['code']).first()
            if not existing:
                permission = Permission(**perm_data)
                db.session.add(permission)
                created_count += 1
        
        try:
            db.session.commit()
            print(f"  ✓ Created {created_count} permissions")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error creating permissions: {str(e)}")
            return False

def create_default_departments(app):
    """Create default departments"""
    with app.app_context():
        from models import db, Department
        
        print("🏢 Creating default departments...")
        
        default_departments = [
            {
                'name': 'K12 Education',
                'code': 'K12',
                'description': 'Kindergarten through 12th grade education department'
            },
            {
                'name': 'Skill in Training (SIT)',
                'code': 'SIT',
                'description': 'Specialized skill training and certification programs'
            },
            {
                'name': 'Upskill Programs',
                'code': 'UPSKILL',
                'description': 'Professional development and upskilling courses'
            },
            {
                'name': 'Administration',
                'code': 'ADMIN',
                'description': 'Administrative and management department'
            }
        ]
        
        created_count = 0
        for dept_data in default_departments:
            existing = Department.query.filter_by(code=dept_data['code']).first()
            if not existing:
                department = Department(**dept_data)
                db.session.add(department)
                created_count += 1
        
        try:
            db.session.commit()
            print(f"  ✓ Created {created_count} departments")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error creating departments: {str(e)}")
            return False

def create_sample_forms(app):
    """Create sample form templates"""
    with app.app_context():
        from models import db, FormTemplate
        
        print("📝 Creating sample forms...")
        
        # Sample tutor registration form
        tutor_form_fields = [
            {'name': 'qualification', 'label': 'Educational Qualification', 'type': 'text', 'required': True},
            {'name': 'experience_years', 'label': 'Years of Experience', 'type': 'number', 'required': True},
            {'name': 'specialization', 'label': 'Subject Specialization', 'type': 'select', 'required': True, 
             'options': ['Mathematics', 'Science', 'English', 'Social Studies', 'Computer Science']},
            {'name': 'teaching_mode', 'label': 'Preferred Teaching Mode', 'type': 'radio', 'required': True,
             'options': ['Online', 'Offline', 'Both']},
            {'name': 'resume', 'label': 'Upload Resume', 'type': 'file', 'required': True},
            {'name': 'languages', 'label': 'Languages Known', 'type': 'checkbox', 'required': True,
             'options': ['English', 'Hindi', 'Tamil', 'Telugu', 'Kannada']},
        ]
        
        # Sample student registration form  
        student_form_fields = [
            {'name': 'grade', 'label': 'Grade/Class', 'type': 'select', 'required': True,
             'options': ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th']},
            {'name': 'school', 'label': 'School Name', 'type': 'text', 'required': True},
            {'name': 'board', 'label': 'Educational Board', 'type': 'select', 'required': True,
             'options': ['CBSE', 'ICSE', 'State Board', 'IB', 'Other']},
            {'name': 'subjects_of_interest', 'label': 'Subjects of Interest', 'type': 'checkbox', 'required': True,
             'options': ['Mathematics', 'Science', 'English', 'Social Studies', 'Computer Science']},
            {'name': 'learning_style', 'label': 'Learning Style', 'type': 'radio', 'required': False,
             'options': ['Visual', 'Auditory', 'Kinesthetic', 'Reading/Writing']},
            {'name': 'special_needs', 'label': 'Special Learning Needs', 'type': 'textarea', 'required': False},
        ]
        
        sample_forms = [
            {
                'name': 'Tutor Registration Form',
                'description': 'Registration form for new tutors',
                'form_type': 'tutor',
                'form_fields': tutor_form_fields
            },
            {
                'name': 'Student Registration Form',
                'description': 'Registration form for new students',
                'form_type': 'student', 
                'form_fields': student_form_fields
            }
        ]
        
        created_count = 0
        for form_data in sample_forms:
            existing = FormTemplate.query.filter_by(name=form_data['name']).first()
            if not existing:
                form_template = FormTemplate(
                    name=form_data['name'],
                    description=form_data['description'],
                    form_type=form_data['form_type']
                )
                form_template.set_fields(form_data['form_fields'])
                db.session.add(form_template)
                created_count += 1
        
        try:
            db.session.commit()
            print(f"  ✓ Created {created_count} sample forms")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error creating forms: {str(e)}")
            return False

def verify_database_integrity(app):
    """Verify database integrity and relationships"""
    with app.app_context():
        from models import db
        
        print("🔍 Verifying database integrity...")
        
        try:
            # Test basic queries on each model
            from models import User, Department, Permission, FormTemplate, Student
            
            # Check if tables exist and are accessible
            user_count = User.query.count()
            dept_count = Department.query.count()
            perm_count = Permission.query.count()
            form_count = FormTemplate.query.count()
            
            print(f"  ✓ Users table: {user_count} records")
            print(f"  ✓ Departments table: {dept_count} records")
            print(f"  ✓ Permissions table: {perm_count} records")
            print(f"  ✓ Forms table: {form_count} records")
            
            # Test relationships by creating a simple query
            if dept_count > 0:
                dept = Department.query.first()
                member_count = len(dept.members)
                print(f"  ✓ Department relationships working: {member_count} members")
            
            print("  ✓ Database integrity check passed")
            return True
            
        except Exception as e:
            print(f"  ❌ Database integrity check failed: {str(e)}")
            return False

def main():
    """Main migration function"""
    print("🚀 Starting LMS Database Migration")
    print("=" * 50)
    
    # Create Flask app
    app = create_app()
    
    # Step 1: Create database tables
    if not create_database_tables(app):
        print("❌ Migration failed at table creation")
        return False
    
    # Step 2: Create default permissions
    if not create_default_permissions(app):
        print("❌ Migration failed at permissions creation")
        return False
    
    # Step 3: Create default departments
    if not create_default_departments(app):
        print("❌ Migration failed at departments creation")
        return False
    
    # Step 4: Create sample forms
    if not create_sample_forms(app):
        print("❌ Migration failed at forms creation")
        return False
    
    # Step 5: Verify database integrity
    if not verify_database_integrity(app):
        print("❌ Migration failed at integrity check")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Database migration completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Run: python app.py")
    print("2. Visit: http://localhost:5000/setup")
    print("3. Create your superadmin account")
    print("4. Start using the LMS!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)