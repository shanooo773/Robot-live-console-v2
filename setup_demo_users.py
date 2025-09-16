#!/usr/bin/env python3
"""
Script to set up demo users in the MySQL database
This ensures demo users are properly stored in the database for authentication
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

def setup_demo_users():
    """Create demo users in the database"""
    try:
        # Initialize database manager
        db = DatabaseManager()
        
        print("🔄 Setting up demo users...")
        
        # Demo user credentials from .env
        demo_users = [
            {
                "name": "Demo User",
                "email": os.getenv('DEMO_USER_EMAIL', 'demo@user.com'),
                "password": os.getenv('DEMO_USER_PASSWORD', 'password'),
                "role": "user"
            },
            {
                "name": "Demo Admin",
                "email": os.getenv('DEMO_ADMIN_EMAIL', 'admin@demo.com'),
                "password": os.getenv('DEMO_ADMIN_PASSWORD', 'password'),
                "role": "admin"
            }
        ]
        
        for user_data in demo_users:
            try:
                # Check if user already exists
                existing_user = db.authenticate_user(user_data["email"], user_data["password"])
                if existing_user:
                    print(f"✅ Demo user {user_data['email']} already exists")
                    continue
                
                # Create the demo user
                user = db.create_user(
                    name=user_data["name"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"]
                )
                print(f"✅ Created demo user: {user_data['email']} (Role: {user_data['role']})")
                
            except ValueError as e:
                if "Email already exists" in str(e):
                    print(f"✅ Demo user {user_data['email']} already exists")
                else:
                    print(f"❌ Error creating user {user_data['email']}: {e}")
            except Exception as e:
                print(f"❌ Error creating user {user_data['email']}: {e}")
        
        print("\n✅ Demo user setup completed!")
        print("\nDemo user credentials:")
        print("  User: demo@user.com / password")
        print("  Admin: admin@demo.com / password")
        
    except Exception as e:
        print(f"❌ Failed to setup demo users: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_demo_users()