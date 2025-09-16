#!/usr/bin/env python3
"""
SQLite Database for Testing
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

class TestDatabaseManager:
    def __init__(self, db_path="test_robot_console.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                robot_type TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Create demo users
        self.create_demo_users()
    
    def create_demo_users(self):
        """Create demo users for testing"""
        demo_users = [
            {
                "name": "Demo User",
                "email": "demo@example.com", 
                "password": "demo123",
                "role": "user"
            },
            {
                "name": "Admin User",
                "email": "admin@example.com",
                "password": "admin123", 
                "role": "admin"
            }
        ]
        
        for user in demo_users:
            try:
                self.create_user(user["name"], user["email"], user["password"], user["role"])
            except:
                pass  # User already exists
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_value = hashed.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
        except:
            return False
    
    def create_user(self, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (name, email, password_hash, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "id": user_id,
            "name": name,
            "email": email,
            "role": role,
            "created_at": datetime.now().isoformat()
        }
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "name": row[1], 
                "email": row[2],
                "password_hash": row[3],
                "role": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            }
        return None
    
    def create_booking(self, user_id: int, robot_type: str, date: str,
                      start_time: str, end_time: str) -> Dict[str, Any]:
        """Create a new booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bookings (user_id, robot_type, date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, robot_type, date, start_time, end_time))
        
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "id": booking_id,
            "user_id": user_id,
            "robot_type": robot_type,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    
    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get bookings for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, u.name as user_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.user_id = ?
            ORDER BY b.date DESC, b.start_time DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        bookings = []
        for row in rows:
            bookings.append({
                "id": row[0],
                "user_id": row[1],
                "robot_type": row[2],
                "date": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "status": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "user_name": row[9]
            })
        
        return bookings
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Get all bookings (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, u.name as user_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            ORDER BY b.date DESC, b.start_time DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        bookings = []
        for row in rows:
            bookings.append({
                "id": row[0],
                "user_id": row[1],
                "robot_type": row[2],
                "date": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "status": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "user_name": row[9]
            })
        
        return bookings
    
    def get_bookings_for_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get bookings for a date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.*, u.name as user_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.date BETWEEN ? AND ?
            ORDER BY b.date, b.start_time
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        bookings = []
        for row in rows:
            bookings.append({
                "id": row[0],
                "user_id": row[1],
                "robot_type": row[2],
                "date": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "status": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "user_name": row[9]
            })
        
        return bookings
    
    def update_booking_status(self, booking_id: int, status: str) -> Optional[Dict[str, Any]]:
        """Update booking status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bookings 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, booking_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return None
        
        cursor.execute("""
            SELECT b.*, u.name as user_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.id = ?
        """, (booking_id,))
        
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "robot_type": row[2],
                "date": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "status": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "user_name": row[9]
            }
        return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, email, role, created_at FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "created_at": row[4]
            })
        
        return users

if __name__ == "__main__":
    # Test the database
    db = TestDatabaseManager()
    print("✅ Test database created with demo users")
    
    # Test user login
    user = db.get_user_by_email("demo@example.com")
    if user:
        print(f"✅ Demo user found: {user['name']}")
        
        # Test password verification
        if db.verify_password("demo123", user["password_hash"]):
            print("✅ Password verification works")
        else:
            print("❌ Password verification failed")
    
    # Test booking creation
    today = datetime.now().strftime("%Y-%m-%d")
    start_time = "10:00"
    end_time = "11:00"
    
    booking = db.create_booking(user["id"], "turtlebot", today, start_time, end_time)
    print(f"✅ Test booking created: {booking['robot_type']} at {booking['start_time']}")
    
    # Get user bookings
    bookings = db.get_user_bookings(user["id"])
    print(f"✅ User has {len(bookings)} booking(s)")
    
    # Get all bookings (admin view)
    all_bookings = db.get_all_bookings()
    print(f"✅ Total bookings in system: {len(all_bookings)}")