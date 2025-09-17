#!/usr/bin/env python3
"""
Migration script to add status column to robots table
Adds 'status' column with default value 'active' to existing robots
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database import DatabaseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)

def migrate_robot_status():
    """Add status column to robots table if it doesn't exist"""
    print("🔄 Starting robot status migration...")
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if status column exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'robots' 
            AND COLUMN_NAME = 'status'
        """)
        
        if cursor.fetchone():
            print("✅ Status column already exists in robots table")
            conn.close()
            return True
        
        # Add status column
        print("➕ Adding status column to robots table...")
        cursor.execute("""
            ALTER TABLE robots 
            ADD COLUMN status VARCHAR(20) DEFAULT 'active' AFTER code_api_url
        """)
        
        # Update all existing robots to be active
        cursor.execute("UPDATE robots SET status = 'active' WHERE status IS NULL")
        
        print("✅ Status column added successfully")
        print(f"✅ All existing robots set to 'active' status")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("""
            DESCRIBE robots
        """)
        
        columns = cursor.fetchall()
        status_column = None
        
        for column in columns:
            if column[0] == 'status':
                status_column = column
                break
        
        if status_column:
            print(f"✅ Status column found: {status_column[0]} {status_column[1]} DEFAULT {status_column[4]}")
        else:
            print("❌ Status column not found!")
            return False
        
        # Check robot count
        cursor.execute("SELECT COUNT(*) FROM robots")
        robot_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM robots WHERE status = 'active'")
        active_count = cursor.fetchone()[0]
        
        print(f"📊 Total robots: {robot_count}")
        print(f"📊 Active robots: {active_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Run the migration"""
    print("🚀 Robot Status Migration Script")
    print("=" * 40)
    
    # Run migration
    if not migrate_robot_status():
        print("\n❌ Migration failed!")
        return False
    
    # Verify migration
    if not verify_migration():
        print("\n❌ Migration verification failed!")
        return False
    
    print("\n✅ Migration completed successfully!")
    print("All robots now have status field with default 'active' value")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)