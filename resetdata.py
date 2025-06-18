import os
import shutil
from app import app, db, User
from datetime import datetime

def reset_database():
    """Completely reset the database - deletes all data"""
    
    print("=" * 60)
    print("DATABASE RESET UTILITY")
    print("=" * 60)
    print("\n⚠️  WARNING: This will DELETE ALL DATA! ⚠️\n")
    
    # Ask for confirmation
    confirm = input("Are you sure you want to delete all data? Type 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("\n❌ Operation cancelled.")
        return
        
    with app.app_context():
        print("\n🗑️ Dropping all tables...")
        db.drop_all()
        
        print("📦 Creating new tables...")
        db.create_all()
        
        print("\n✨ Database reset complete!")

def delete_specific_user():
    """Delete a specific user by email or username"""
    
    with app.app_context():
        identifier = input("\nEnter user email or username: ")
        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()
        
        if not user:
            print("\n❌ User not found!")
            return
            
        print(f"\nUser found: {user.username} ({user.email})")
        confirm = input("Type 'YES' to delete this user: ")
        
        if confirm == 'YES':
            db.session.delete(user)
            db.session.commit()
            print("\n✅ User deleted successfully!")
        else:
            print("\n❌ Operation cancelled.")

def clear_specific_table():
    """Clear all data from a specific table"""
    
    with app.app_context():
        print("\n📊 Available tables:")
        print("1. User (all users)")
        print("2. Cancel")
        
        choice = input("\nWhich table to clear? (1-2): ")
        
        if choice == '1':
            confirm = input("\n⚠️  Delete ALL users? Type 'CLEAR' to confirm: ")
            if confirm == 'CLEAR':
                User.query.delete()
                db.session.commit()
                print("\n✅ All users deleted!")
            else:
                print("\n❌ Operation cancelled.")
        else:
            print("\n❌ Operation cancelled.")

def delete_database_file():
    """Completely delete the database file"""
    
    db_path = os.path.join('instance', 'lms.db')
    
    if os.path.exists(db_path):
        print("\n⚠️  This will delete the entire database file!")
        confirm = input("Type 'DELETE FILE' to confirm: ")
        
        if confirm == 'DELETE FILE':
            os.remove(db_path)
            print("\n✅ Database file deleted!")
            print("📌 Run the app again to create a fresh database.")
        else:
            print("\n❌ Operation cancelled.")
    else:
        print("\n❌ Database file not found!")

if __name__ == "__main__":
    print("\n🗄️  LMS Database Management")
    print("=" * 40)
    print("1. Reset entire database (delete all data)")
    print("2. Delete specific user")
    print("3. Clear specific table")
    print("4. Delete database file completely")
    print("5. Exit")
    
    choice = input("\nChoose an option (1-5): ")
    
    if choice == '1':
        reset_database()
    elif choice == '2':
        delete_specific_user()
    elif choice == '3':
        clear_specific_table()
    elif choice == '4':
        delete_database_file()
    elif choice == '5':
        print("\nGoodbye!")
    else:
        print("\n❌ Invalid choice!")