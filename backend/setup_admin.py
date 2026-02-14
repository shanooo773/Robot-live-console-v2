#!/usr/bin/env python3
"""
Admin Account Setup Script
Creates a new admin user for Robot Live Console
"""

import os
import sys
import getpass
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import DatabaseManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_password(password: str, confirm: str) -> bool:
    """Validate password meets requirements"""
    if password != confirm:
        print("❌ Passwords do not match!")
        return False
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long!")
        return False
    
    return True

def create_admin():
    """Create a new admin user"""
    print("=" * 60)
    print("Robot Live Console - Admin Account Setup")
    print("=" * 60)
    print()
    
    try:
        # Initialize database
        db = DatabaseManager()
        print("✅ Connected to database")
        print()
        
        # Get admin details
        name = input("Admin name: ").strip()
        if not name:
            print("❌ Name cannot be empty!")
            return
        
        email = input("Admin email: ").strip()
        if not email or '@' not in email:
            print("❌ Invalid email address!")
            return
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            print(f"⚠️  User with email {email} already exists!")
            update = input("Update existing user to admin? (y/n): ").strip().lower()
            if update == 'y':
                # Update role to admin
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET role = 'admin' WHERE email = %s", (email,))
                conn.close()
                print(f"✅ User {email} has been promoted to admin!")
                return
            else:
                print("Aborted.")
                return
        
        # Get password
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if not validate_password(password, confirm):
            return
        
        print()
        print("Creating admin account...")
        
        # Create user with admin role
        user = db.create_user(name, email, password, role="admin")
        
        # Activate the account (skip email confirmation for admin)
        db.activate_user_by_email(email)
        
        print()
        print("=" * 60)
        print("✅ Admin account created successfully!")
        print("=" * 60)
        print(f"Name:  {name}")
        print(f"Email: {email}")
        print(f"Role:  admin")
        print(f"ID:    {user['id']}")
        print()
        print("The account is active and ready to use.")
        print("You can now log in with these credentials.")
        print("=" * 60)
        
    except Exception as e:
        print()
        print(f"❌ Error creating admin account: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(0)
