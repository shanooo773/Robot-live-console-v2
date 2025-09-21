#!/usr/bin/env python3
"""
Comprehensive test script for the Robot Console database layer
Tests MySQL connectivity, schema validity, and app functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import DatabaseManager
from dotenv import load_dotenv
import pymysql

load_dotenv()

def test_mysql_connection():
    """Test MySQL connection and configuration"""
    print("🔍 Testing MySQL connection...")
    
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'robot_console'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'robot_console'),
        'charset': 'utf8mb4'
    }
    
    try:
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        print("✅ MySQL connection successful!")
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def test_database_schema():
    """Test database schema and table structure"""
    print("\n🔍 Testing database schema...")
    
    try:
        db = DatabaseManager()
        print(f"✅ DatabaseManager initialized with type: {db.db_type}")
        
        if db.db_type != 'mysql':
            print(f"❌ Expected MySQL, but got: {db.db_type}")
            return False
        
        # Test connection
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if all required tables exist
        required_tables = ['users', 'bookings', 'sessions', 'messages', 'announcements']
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📋 Existing tables: {existing_tables}")
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
                
                # Get table structure
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"  Columns: {[col[0] for col in columns]}")
            else:
                print(f"❌ Table '{table}' missing")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_crud_operations():
    """Test basic CRUD operations"""
    print("\n🔍 Testing CRUD operations...")
    
    try:
        db = DatabaseManager()
        
        # Test user creation (use unique email with timestamp)
        print("  Testing user creation...")
        import time
        unique_email = f"test_{int(time.time())}@example.com"
        
        try:
            test_user = db.create_user(
                name="Test User",
                email=unique_email,
                password="testpass123",
                role="user"
            )
            print(f"✅ User created: {test_user['email']}")
        except ValueError as e:
            if "Email already exists" in str(e):
                # User already exists, just get it for testing
                print(f"ℹ️  User already exists, using existing user for test")
                unique_email = "test@example.com"  # Use the existing test user
            else:
                raise
        
        # Test user authentication
        print("  Testing user authentication...")
        auth_user = db.authenticate_user(unique_email, "testpass123")
        if auth_user and auth_user['email'] == unique_email:
            print("✅ User authentication successful")
        else:
            print("❌ User authentication failed")
            return False
        
        # Test booking creation
        print("  Testing booking creation...")
        booking = db.create_booking(
            user_id=auth_user['id'],
            robot_type="turtlebot",
            date="2024-01-15",
            start_time="10:00",
            end_time="11:00"
        )
        print(f"✅ Booking created: {booking['id']}")
        
        # Test message creation
        print("  Testing message creation...")
        message = db.create_message(
            name="Test User",
            email="test@example.com",
            message="This is a test message"
        )
        print(f"✅ Message created: {message['id']}")
        
        # Test announcement creation (admin only)
        print("  Testing announcement creation...")
        announcement = db.create_announcement(
            title="Test Announcement",
            content="This is a test announcement",
            priority="normal",
            created_by=auth_user['id']
        )
        print(f"✅ Announcement created: {announcement['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        return False

def test_demo_users():
    """Test demo user functionality"""
    print("\n🔍 Testing demo users...")
    
    try:
        db = DatabaseManager()
        
        # Test demo user credentials from .env
        demo_credentials = [
            (os.getenv('DEMO_USER_EMAIL', 'demo@user.com'), 
             os.getenv('DEMO_USER_PASSWORD', 'password')),
            (os.getenv('DEMO_ADMIN_EMAIL', 'admin@demo.com'), 
             os.getenv('DEMO_ADMIN_PASSWORD', 'password'))
        ]
        
        for email, password in demo_credentials:
            user = db.authenticate_user(email, password)
            if user:
                print(f"✅ Demo user authentication successful: {email} (Role: {user['role']})")
            else:
                print(f"❌ Demo user authentication failed: {email}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Demo user test failed: {e}")
        return False

def test_app_features():
    """Test that database supports all app features"""
    print("\n🔍 Testing app feature compatibility...")
    
    try:
        db = DatabaseManager()
        
        # Test user management (login, roles)
        users = db.get_all_users()
        print(f"✅ User management: {len(users)} users found")
        
        # Test booking system
        bookings = db.get_all_bookings()
        print(f"✅ Booking system: {len(bookings)} bookings found")
        
        # Test messaging system
        messages = db.get_all_messages()
        print(f"✅ Messaging system: {len(messages)} messages found")
        
        # Test announcements
        announcements = db.get_all_announcements()
        print(f"✅ Announcements: {len(announcements)} announcements found")
        
        # Test active announcements (public)
        active_announcements = db.get_active_announcements()
        print(f"✅ Active announcements: {len(active_announcements)} active announcements")
        
        return True
        
    except Exception as e:
        print(f"❌ App features test failed: {e}")
        return False

def main():
    """Run all database tests"""
    print("🗄️  Robot Console Database Layer Testing")
    print("=" * 50)
    
    # Check environment configuration
    print(f"Database Type: {os.getenv('DATABASE_TYPE', 'mysql')}")
    print(f"MySQL Host: {os.getenv('MYSQL_HOST', 'localhost')}")
    print(f"MySQL Database: {os.getenv('MYSQL_DATABASE', 'robot_console')}")
    print(f"MySQL User: {os.getenv('MYSQL_USER', 'robot_console')}")
    print()
    
    tests = [
        ("MySQL Connection", test_mysql_connection),
        ("Database Schema", test_database_schema),
        ("CRUD Operations", test_crud_operations),
        ("Demo Users", test_demo_users),
        ("App Features", test_app_features)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database layer is properly configured.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())