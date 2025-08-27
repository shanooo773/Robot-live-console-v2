#!/usr/bin/env python3
"""
Migration script to move data from SQLite to MySQL
This version creates tables automatically in MySQL if they do not exist.
"""

import sqlite3
import pymysql
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Define MySQL table schemas (adjust columns as needed)
TABLE_SCHEMAS = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            password_hash VARCHAR(255),
            role VARCHAR(50),
            created_at DATETIME
        )
    """,
    "bookings": """
    CREATE TABLE IF NOT EXISTS bookings (
        id INT PRIMARY KEY,
        user_id INT,
        robot_type VARCHAR(50),
        date DATE,
        start_time DATETIME,
        end_time DATETIME,
        status VARCHAR(50),
        created_at DATETIME
    )
"""

    "sessions": """
        CREATE TABLE IF NOT EXISTS sessions (
            id INT PRIMARY KEY,
            booking_id INT,
            session_data TEXT,
            created_at DATETIME
        )
    """,
    "messages": """
        CREATE TABLE IF NOT EXISTS messages (
            id INT PRIMARY KEY,
            user_id INT,
            content TEXT,
            created_at DATETIME
        )
    """,
    "announcements": """
        CREATE TABLE IF NOT EXISTS announcements (
            id INT PRIMARY KEY,
            title VARCHAR(255),
            content TEXT,
            created_at DATETIME
        )
    """
}

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
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{database_name}' created or already exists")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def migrate_sqlite_to_mysql():
    """Migrate all data from SQLite database to MySQL"""
    sqlite_path = "robot_console.db"
    if not os.path.exists(sqlite_path):
        print(f"SQLite database {sqlite_path} not found!")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

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
        return

    for table, create_sql in TABLE_SCHEMAS.items():
        print(f"\nProcessing table: {table}")

        # Create table if not exists
        mysql_cursor.execute(create_sql)

        # Fetch all data from SQLite
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            if not rows:
                print(f"  No data found in {table}")
                continue
        except sqlite3.OperationalError:
            print(f"  Table '{table}' does not exist in SQLite, skipping.")
            continue

        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        print(f"  Found {len(rows)} rows with columns: {columns}")

        # Clear MySQL table
        mysql_cursor.execute(f"DELETE FROM {table}")

        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        try:
            mysql_cursor.executemany(insert_query, rows)
            mysql_conn.commit()
            print(f"  Successfully migrated {len(rows)} rows")
        except Exception as e:
            print(f"  Error migrating {table}: {e}")
            mysql_conn.rollback()

    sqlite_conn.close()
    mysql_conn.close()
    print("\n✅ Migration completed! You can now use MySQL as your database.")

if __name__ == "__main__":
    print("🔄 Starting SQLite to MySQL migration...")

    if not create_mysql_database():
        exit(1)

    migrate_sqlite_to_mysql()
