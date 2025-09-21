#!/usr/bin/env python3
"""
Quick MySQL setup script that uses debian-sys-maint credentials
to properly initialize the database for the Robot Console.
"""

import pymysql
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Set up MySQL database and user using debian-sys-maint credentials"""
    
    print("🔧 Setting up MySQL database using debian-sys-maint credentials...")
    
    # debian-sys-maint credentials from /etc/mysql/debian.cnf
    debian_password = "ZjxyniNqgIRZ060f"
    
    # Database configuration from .env
    db_host = os.getenv('MYSQL_HOST', 'localhost')
    db_port = int(os.getenv('MYSQL_PORT', 3306))
    db_user = os.getenv('MYSQL_USER', 'robot_console')
    db_password = os.getenv('MYSQL_PASSWORD', '1122root')
    db_name = os.getenv('MYSQL_DATABASE', 'robot_console')
    
    try:
        # Connect using debian-sys-maint
        print(f"📡 Connecting to MySQL as debian-sys-maint...")
        conn = pymysql.connect(
            host=db_host,
            port=db_port,
            user='debian-sys-maint',
            password=debian_password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # Create database
        print(f"🗄️  Creating database '{db_name}'...")
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS `{db_name}` 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """)
        
        # Create user
        print(f"👤 Creating user '{db_user}'...")
        cursor.execute(f"""
            CREATE USER IF NOT EXISTS '{db_user}'@'localhost' 
            IDENTIFIED WITH mysql_native_password BY '{db_password}'
        """)
        
        # Grant permissions
        print(f"🔑 Granting permissions to '{db_user}'...")
        cursor.execute(f"""
            GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, REFERENCES 
            ON `{db_name}`.* TO '{db_user}'@'localhost'
        """)
        
        # Apply changes
        cursor.execute("FLUSH PRIVILEGES")
        
        print("✅ Database setup completed successfully!")
        
        # Test the new user connection
        print(f"🧪 Testing connection with user '{db_user}'...")
        test_conn = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT 1")
        result = test_cursor.fetchone()
        test_conn.close()
        
        if result[0] == 1:
            print("✅ User connection test successful!")
            return True
        else:
            print("❌ User connection test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function"""
    print("🗄️  Quick MySQL Setup for Robot Console")
    print("=" * 40)
    
    if setup_database():
        print("\n🎉 Database setup completed successfully!")
        print("✅ You can now run the database tests.")
        return 0
    else:
        print("\n❌ Database setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())