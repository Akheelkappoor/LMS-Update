# test_end_to_end.py - Comprehensive End-to-End Testing Script

import unittest
import tempfile
import os
from app import app, db
from models import User, Department, Student, Class, StudentFee, FormTemplate
from functions.auth_functions import create_superadmin, authenticate_user
from functions.user_functions import create_user, get_user_dashboard_data
from functions.student_functions import create_student
from datetime import datetime, date

class EndToEndTestCase(unittest.TestCase):
    """Comprehensive end-to-end testing"""
    
    def setUp(self):
        """Set up test database and application context"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Create test superadmin
        self.create_test_superadmin()
        
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def create_test_superadmin(self):
        """Create test superadmin user"""
        admin_data = {
            'full_name': 'Test Superadmin',
            'username': 'superadmin',
            'email': 'superadmin@test.com',
            'password': 'password123',
            'mobile': '1234567890'
        }
        success, message = create_superadmin(admin_data)
        self.assertTrue(success, f"Failed to create superadmin: {message}")
        
    def create_test_department(self):
        """Create test department"""
        department = Department(
            name='Computer Science',
            code='CS',
            description='Computer Science Department',
            is_active=True
        )
        db.session.add(department)
        db.session.commit()
        return department
    
    def test_01_authentication_workflow(self):
        """Test complete authentication workflow"""
        print("\n=== Testing Authentication Workflow ===")
        
        # Test login page loads
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)
        
        # Test valid login
        response = self.app.post('/login', data={
            'email': 'superadmin@test.com',
            'password': 'password123',
            'remember': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
        
        # Test dashboard access
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Test logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logged out', response.data)
        
        print("✓ Authentication workflow working correctly")
    
    def test_02_user_management_workflow(self):
        """Test complete user management workflow"""
        print("\n=== Testing User Management Workflow ===")
        
        # Login as superadmin
        self.app.post('/login', data={
            'email': 'superadmin@test.com',
            'password': 'password123'
        })
        
        # Create department first
        department = self.create_test_department()
        
        # Test user creation
        user_data = {
            'username': 'testuser',
            'email': 'testuser@test.com',
            'full_name': 'Test User',
            'phone': '9876543210',
            'role': 'tutor',
            'department_id': department.id,
            'permissions': ['view_own_classes', 'mark_attendance']
        }
        
        user, password = create_user(user_data)
        self.assertIsNotNone(user, "Failed to create user")
        self.assertTrue(user.is_approved, "User should be auto-approved when created by admin")
        
        # Test user list page
        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
        
        # Test user view page
        response = self.app.get(f'/users/{user.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
        
        # Test user edit
        response = self.app.post(f'/users/{user.id}/edit', data={
            'full_name': 'Updated Test User',
            'email': 'testuser@test.com',
            'phone': '9876543210',
            'role': 'tutor',
            'department_id': department.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify user was updated
        updated_user = User.query.get(user.id)
        self.assertEqual(updated_user.full_name, 'Updated Test User')
        
        print("✓ User management workflow working correctly")
    
    def test_03_student_management_workflow(self):
        """Test complete student management workflow"""
        print("\n=== Testing Student Management Workflow ===")
        
        # Login as superadmin
        self.app.post('/login', data={
            'email': 'superadmin@test.com',
            'password': 'password123'
        })
        
        # Create department
        department = self.create_test_department()
        
        # Test student creation
        student_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'phone': '9876543210',
            'grade': '5th',
            'school': 'Test School',
            'department_id': department.id,
            'date_of_birth': '2010-01-01'
        }
        
        student, message = create_student(student_data)
        self.assertIsNotNone(student, f"Failed to create student: {message}")
        
        # Test students list page
        response = self.app.get('/students')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'John Doe', response.data)
        
        # Test student view page
        response = self.app.get(f'/students/{student.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'John Doe', response.data)
        
        print("✓ Student management workflow working correctly")
    
    def test_04_dashboard_data_binding(self):
        """Test dashboard data binding for all roles"""
        print("\n=== Testing Dashboard Data Binding ===")
        
        # Create test users for each role
        department = self.create_test_department()
        
        # Test superadmin dashboard
        superadmin = User.query.filter_by(role='superadmin').first()
        dashboard_data = get_user_dashboard_data(superadmin)
        self.assertIn('total_users', dashboard_data)
        self.assertIn('total_departments', dashboard_data)
        
        # Create and test admin user
        admin_data = {
            'username': 'admin',
            'email': 'admin@test.com',
            'full_name': 'Test Admin',
            'role': 'admin',
            'department_id': department.id
        }
        admin, _ = create_user(admin_data)
        admin_dashboard = get_user_dashboard_data(admin)
        self.assertIn('total_users', admin_dashboard)
        
        # Create and test coordinator
        # Create and test coordinator
        coordinator_data = {
            'username': 'coordinator',
            'email': 'coordinator@test.com',
            'full_name': 'Test Coordinator',
            'role': 'coordinator',
            'department_id': department.id
        }
        coordinator, _ = create_user(coordinator_data)
        coord_dashboard = get_user_dashboard_data(coordinator)
        self.assertIn('department_users', coord_dashboard)
        self.assertIn('department_name', coord_dashboard)
        
        # Create and test tutor
        tutor_data = {
            'username': 'tutor',
            'email': 'tutor@test.com',
            'full_name': 'Test Tutor',
            'role': 'tutor',
            'department_id': department.id
        }
        tutor, _ = create_user(tutor_data)
        tutor_dashboard = get_user_dashboard_data(tutor)
        self.assertIn('classes_today', tutor_dashboard)
        self.assertIn('total_students', tutor_dashboard)
        
        print("✓ Dashboard data binding working for all roles")
    
    def test_05_permissions_system(self):
        """Test role-based permissions system"""
        print("\n=== Testing Permissions System ===")
        
        department = self.create_test_department()
        
        # Create users with different roles
        tutor_data = {
            'username': 'tutor_perm',
            'email': 'tutor_perm@test.com',
            'full_name': 'Tutor Permission Test',
            'role': 'tutor',
            'department_id': department.id
        }
        tutor, _ = create_user(tutor_data)
        
        # Test tutor permissions
        self.assertTrue(tutor.has_permission('view_own_classes'))
        self.assertTrue(tutor.has_permission('mark_attendance'))
        self.assertFalse(tutor.has_permission('manage_all_users'))
        
        # Create coordinator
        coord_data = {
            'username': 'coord_perm',
            'email': 'coord_perm@test.com',
            'full_name': 'Coordinator Permission Test',
            'role': 'coordinator',
            'department_id': department.id
        }
        coordinator, _ = create_user(coord_data)
        
        # Test coordinator permissions
        self.assertTrue(coordinator.has_permission('view_department_users'))
        self.assertTrue(coordinator.has_permission('create_students'))
        self.assertFalse(coordinator.has_permission('manage_all_users'))
        
        # Test superadmin permissions
        superadmin = User.query.filter_by(role='superadmin').first()
        self.assertTrue(superadmin.has_permission('manage_all_users'))
        self.assertTrue(superadmin.has_permission('system_settings'))
        
        print("✓ Permissions system working correctly")
    
    def test_06_finance_workflow(self):
        """Test finance management workflow"""
        print("\n=== Testing Finance Workflow ===")
        
        # Login as superadmin
        self.app.post('/login', data={
            'email': 'superadmin@test.com',
            'password': 'password123'
        })
        
        # Create student and fee
        department = self.create_test_department()
        student_data = {
            'first_name': 'Finance',
            'last_name': 'Test',
            'email': 'finance@test.com',
            'department_id': department.id,
            'grade': '5th'
        }
        student, _ = create_student(student_data)
        
        # Create student fee
        fee = StudentFee(
            student_id=student.id,
            fee_type='tuition',
            amount=1000.0,
            due_date=date(2024, 12, 31),
            payment_status='pending',
            pending_amount=1000.0
        )
        db.session.add(fee)
        db.session.commit()
        
        # Test finance dashboard access
        response = self.app.get('/finance')
        self.assertIn(response.status_code, [200, 403])  # May require finance role
        
        print("✓ Finance workflow structure working")
    
    def test_07_error_handling(self):
        """Test error handling and edge cases"""
        print("\n=== Testing Error Handling ===")
        
        # Test 404 error
        response = self.app.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
        
        # Test accessing protected route without login
        response = self.app.get('/users')
        self.assertIn(response.status_code, [302, 401])  # Should redirect to login
        
        # Test invalid login
        response = self.app.post('/login', data={
            'email': 'invalid@test.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Returns to login page
        
        print("✓ Error handling working correctly")
    
    def test_08_template_rendering(self):
        """Test template rendering and data binding"""
        print("\n=== Testing Template Rendering ===")
        
        # Login as superadmin
        self.app.post('/login', data={
            'email': 'superadmin@test.com',
            'password': 'password123'
        })
        
        # Test various template pages
        test_pages = [
            '/dashboard',
            '/users',
            '/students',
            '/profile',
            '/reports'
        ]
        
        for page in test_pages:
            response = self.app.get(page)
            self.assertIn(response.status_code, [200, 302])  # 302 for redirects
            if response.status_code == 200:
                self.assertNotIn(b'Error', response.data)
        
        print("✓ Template rendering working correctly")

def run_manual_validation():
    """Manual validation checklist"""
    print("\n" + "="*50)
    print("MANUAL VALIDATION CHECKLIST")
    print("="*50)
    
    checklist = [
        "1. Navigate to /setup and create superadmin",
        "2. Login with superadmin credentials",
        "3. Create department from admin panel",
        "4. Create coordinator user",
        "5. Create tutor user",
        "6. Test role-based navigation visibility",
        "7. Create student as coordinator",
        "8. Test student enrollment workflow",
        "9. Test class creation and management",
        "10. Test finance dashboard access",
        "11. Test form builder functionality",
        "12. Test reports generation",
        "13. Test user profile editing",
        "14. Test password change workflow",
        "15. Test logout and session cleanup"
    ]
    
    for item in checklist:
        print(f"☐ {item}")
    
    print("\n" + "="*50)

if __name__ == '__main__':
    print("Starting End-to-End Testing...")
    print("="*50)
    
    # Run automated tests
    unittest.main(verbosity=2, exit=False)
    
    # Show manual validation checklist
    run_manual_validation()