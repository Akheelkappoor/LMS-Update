# Create this file as: reset_and_migrate.py

import os
import shutil
from app import app, db
from datetime import datetime

def reset_database():
    """Completely reset and recreate the database with new schema"""
    
    print("=" * 60)
    print("DATABASE RESET AND MIGRATION")
    print("=" * 60)
    print("\n🔄 This will recreate the database with the new schema...")
    
    with app.app_context():
        # Drop all tables
        print("\n🗑️ Dropping all existing tables...")
        db.drop_all()
        
        # Create all tables with new schema
        print("📦 Creating new tables with updated schema...")
        db.create_all()
        
        print("\n✨ Database recreated successfully!")
        print("\n📋 New tables created:")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        for table in sorted(tables):
            print(f"  ✓ {table}")
        
        print(f"\n📊 Total tables: {len(tables)}")
        
        # Create default permissions if they don't exist
        create_default_permissions()
        
        print("\n🎯 Database is ready! You can now:")
        print("1. Run the application: python app.py")
        print("2. Visit /setup to create your superadmin account")
        print("3. Start using the system!")

def create_default_permissions():
    """Create default system permissions"""
    from models import Permission
    
    default_permissions = [
        {
            'name': 'User Management',
            'code': 'user_management',
            'description': 'Create, edit, and manage users',
            'category': 'user'
        },
        {
            'name': 'Student Management',
            'code': 'student_management',
            'description': 'Manage student enrollments and records',
            'category': 'student'
        },
        {
            'name': 'Schedule Management',
            'code': 'schedule_management',
            'description': 'Manage class schedules and timetables',
            'category': 'schedule'
        },
        {
            'name': 'Report Generation',
            'code': 'report_generation',
            'description': 'Generate and view reports',
            'category': 'reports'
        },
        {
            'name': 'Payroll Management',
            'code': 'payroll_management',
            'description': 'Manage tutor payments and payroll',
            'category': 'finance'
        }
    ]
    
    for perm_data in default_permissions:
        existing = Permission.query.filter_by(code=perm_data['code']).first()
        if not existing:
            permission = Permission(**perm_data)
            db.session.add(permission)
    
    db.session.commit()
    print(f"  ✓ Created {len(default_permissions)} default permissions")

def create_sample_data():
    """Create sample data for testing (optional)"""
    from models import Department
    print("\n🔧 Creating sample data...")
    
    # Create sample department
    dept = Department(
        name='Computer Science',
        code='CS',
        description='Computer Science Department',
        created_by=1  # Will be created after superadmin is set up
    )
    db.session.add(dept)
    db.session.commit()
    
    print("  ✓ Created sample department")
    print("\n📝 Sample data created!")

if __name__ == "__main__":
    print("\n🗄️  LMS Database Reset & Migration")
    print("=" * 40)
    print("This will:")
    print("1. Delete the existing database")
    print("2. Create new tables with updated schema")
    print("3. Set up default permissions")
    print("4. Prepare the system for first use")
    print("\n⚠️  ALL EXISTING DATA WILL BE LOST!")
    
    confirm = input("\nType 'RESET' to continue: ")
    
    if confirm == 'RESET':
        reset_database()
        
        # Ask if user wants sample data
        sample = input("\nCreate sample data for testing? (y/n): ")
        if sample.lower() == 'y':
            with app.app_context():
                create_sample_data()
        
        print("\n🎉 Setup complete! Run 'python app.py' to start the application.")
    else:
        print("\n❌ Operation cancelled.")