#!/usr/bin/env python3
"""
Migration script to move data from SQLite to MySQL
"""

import sqlite3
import pymysql
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def migrate_sqlite_to_mysql():
    """Migrate all data from SQLite database to MySQL"""
    
    # SQLite connection
    sqlite_path = "robot_console.db"
    if not os.path.exists(sqlite_path):
        print(f"SQLite database {sqlite_path} not found!")
        return
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # MySQL connection
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'robot_console'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'robot_console'),
        'charset': 'utf8mb4'
    }
    
    try:
        mysql_conn = pymysql.connect(**mysql_config)
        mysql_cursor = mysql_conn.cursor()
        print("Connected to MySQL successfully!")
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        print("Make sure MySQL is running and credentials are correct in .env file")
        return
    
    # Tables to migrate
    tables = ['users', 'bookings', 'sessions', 'messages', 'announcements']
    
    for table in tables:
        print(f"\nMigrating table: {table}")
        
        # Get all data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  No data found in {table}")
            continue
        
        # Get column names
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        print(f"  Found {len(rows)} rows with columns: {columns}")
        
        # Clear existing data in MySQL table (optional - comment out if you want to preserve)
        mysql_cursor.execute(f"DELETE FROM {table}")
        
        # Insert data into MySQL
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        try:
            mysql_cursor.executemany(insert_query, rows)
            mysql_conn.commit()
            print(f"  Successfully migrated {len(rows)} rows")
        except Exception as e:
            print(f"  Error migrating {table}: {e}")
            mysql_conn.rollback()
    
    # Close connections
    sqlite_conn.close()
    mysql_conn.close()
    
    print("\n✅ Migration completed!")
    print("You can now update DATABASE_TYPE=mysql in your .env file")

def create_mysql_database():
    """Create the MySQL database if it doesn't exist"""
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'robot_console'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'charset': 'utf8mb4'
    }
    
    database_name = os.getenv('MYSQL_DATABASE', 'robot_console')
    
    try:
        # Connect without specifying database
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{database_name}' created or already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting SQLite to MySQL migration...")
    print("\n1. Creating MySQL database...")
    
    if not create_mysql_database():
        exit(1)
    
    print("\n2. Migrating data...")
    migrate_sqlite_to_mysql()