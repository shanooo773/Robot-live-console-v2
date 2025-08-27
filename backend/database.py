import sqlite3
import pymysql
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self, db_path: str = "robot_console.db"):
        self.db_path = db_path
        self.db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
        
        # MySQL configuration
        if self.db_type == 'mysql':
            self.mysql_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'robot_console'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'robot_console'),
                'charset': 'utf8mb4',
                'autocommit': True
            }
        
        self.init_database()
    
    def get_connection(self):
        """Get database connection based on database type"""
        if self.db_type == 'mysql':
            return pymysql.connect(**self.mysql_config)
        else:
            return sqlite3.connect(self.db_path)
    
    def _get_placeholder(self):
        """Get the correct parameter placeholder for the database type"""
        return "%s" if self.db_type == 'mysql' else "?"
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # SQL syntax differences between SQLite and MySQL
        if self.db_type == 'mysql':
            auto_increment = "AUTO_INCREMENT"
            text_type = "TEXT"
            timestamp_default = "DEFAULT CURRENT_TIMESTAMP"
            primary_key = "PRIMARY KEY"
        else:
            auto_increment = "AUTOINCREMENT"
            text_type = "TEXT"
            timestamp_default = "DEFAULT CURRENT_TIMESTAMP"
            primary_key = "PRIMARY KEY AUTOINCREMENT"
        
        # Users table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER {primary_key},
                name {text_type} NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash {text_type} NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP {timestamp_default}
            )
        """)
        
        # Bookings table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER {primary_key},
                user_id INTEGER NOT NULL,
                robot_type VARCHAR(100) NOT NULL,
                date VARCHAR(20) NOT NULL,
                start_time VARCHAR(10) NOT NULL,
                end_time VARCHAR(10) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP {timestamp_default},
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Sessions table for JWT token management
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER {primary_key},
                user_id INTEGER NOT NULL,
                token_hash {text_type} NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP {timestamp_default},
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Messages table for contact form submissions
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER {primary_key},
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                message {text_type} NOT NULL,
                status VARCHAR(50) DEFAULT 'unread',
                created_at TIMESTAMP {timestamp_default}
            )
        """)
        
        # Announcements table for admin announcements
        if self.db_type == 'mysql':
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER {primary_key},
                    title VARCHAR(255) NOT NULL,
                    content {text_type} NOT NULL,
                    priority VARCHAR(50) DEFAULT 'normal',
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP {timestamp_default},
                    updated_at TIMESTAMP {timestamp_default} ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
        else:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER {primary_key},
                    title VARCHAR(255) NOT NULL,
                    content {text_type} NOT NULL,
                    priority VARCHAR(50) DEFAULT 'normal',
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP {timestamp_default},
                    updated_at TIMESTAMP {timestamp_default},
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)
        
        if self.db_type == 'sqlite':
            conn.commit()
        
        # Create default admin user if none exists
        self._create_default_admin(cursor, conn)
        
        conn.close()
    
    def _create_default_admin(self, cursor, conn):
        """Create a default admin user if no admin exists"""
        placeholder = self._get_placeholder()
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE role = {placeholder}", ("admin",))
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            admin_password = "admin123"
            password_hash = self._hash_password(admin_password)
            cursor.execute(f"""
                INSERT INTO users (name, email, password_hash, role)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, ("Admin User", "admin@robot-console.com", password_hash, "admin"))
            if self.db_type == 'sqlite':
                if self.db_type == "sqlite":

                    conn.commit()
            print(f"Created default admin user: admin@robot-console.com / {admin_password}")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{pwd_hash}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, pwd_hash = password_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
        except ValueError:
            return False
    
    def create_user(self, name: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute(f"""
                INSERT INTO users (name, email, password_hash, role)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (name, email, password_hash, role))
            
            user_id = cursor.lastrowid
            if self.db_type == 'sqlite':
                conn.commit()
            
            # Return user without password
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role,
                "created_at": datetime.now().isoformat()
            }
        except (sqlite3.IntegrityError, pymysql.IntegrityError):
            raise ValueError("Email already exists")
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return user data if valid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT id, name, email, password_hash, role, created_at
            FROM users WHERE email = {placeholder}
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            # User not found in database
            return None
            
        if self._verify_password(password, user[3]):
            return {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[4],
                "created_at": user[5]
            }
        else:
            # Password verification failed
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT id, name, email, role, created_at
            FROM users WHERE id = {placeholder}
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[3],
                "created_at": user[4]
            }
        return None
    
    def create_booking(self, user_id: int, robot_type: str, date: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Create a new booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        try:
            cursor.execute(f"""
                INSERT INTO bookings (user_id, robot_type, date, start_time, end_time)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (user_id, robot_type, date, start_time, end_time))
            
            booking_id = cursor.lastrowid
            if self.db_type == "sqlite":
                conn.commit()
            
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
        finally:
            conn.close()
    
    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, robot_type, date, start_time, end_time, status, created_at
            FROM bookings WHERE user_id = ? ORDER BY date DESC, start_time DESC
        """, (user_id,))
        
        bookings = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": booking[0],
                "user_id": booking[1],
                "robot_type": booking[2],
                "date": booking[3],
                "start_time": booking[4],
                "end_time": booking[5],
                "status": booking[6],
                "created_at": booking[7]
            }
            for booking in bookings
        ]
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Get all bookings (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.id, b.user_id, u.name, u.email, b.robot_type, b.date, 
                   b.start_time, b.end_time, b.status, b.created_at
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            ORDER BY b.date DESC, b.start_time DESC
        """)
        
        bookings = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": booking[0],
                "user_id": booking[1],
                "user_name": booking[2],
                "user_email": booking[3],
                "robot_type": booking[4],
                "date": booking[5],
                "start_time": booking[6],
                "end_time": booking[7],
                "status": booking[8],
                "created_at": booking[9]
            }
            for booking in bookings
        ]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, role, created_at
            FROM users ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[3],
                "created_at": user[4]
            }
            for user in users
        ]
    
    def update_booking_status(self, booking_id: int, status: str) -> bool:
        """Update booking status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bookings SET status = ? WHERE id = ?
        """, (status, booking_id))
        
        updated = cursor.rowcount > 0
        if self.db_type == "sqlite":

            conn.commit()
        conn.close()
        
        return updated
    
    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        
        deleted = cursor.rowcount > 0
        if self.db_type == "sqlite":

            conn.commit()
        conn.close()
        
        return deleted
    
    def get_bookings_for_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get bookings within a date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.id, b.user_id, u.name, b.robot_type, b.date, 
                   b.start_time, b.end_time, b.status
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.date >= ? AND b.date <= ? AND b.status = 'active'
            ORDER BY b.date, b.start_time
        """, (start_date, end_date))
        
        bookings = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": booking[0],
                "user_id": booking[1],
                "user_name": booking[2],
                "robot_type": booking[3],
                "date": booking[4],
                "start_time": booking[5],
                "end_time": booking[6],
                "status": booking[7]
            }
            for booking in bookings
        ]
    
    # Message management methods
    def create_message(self, name: str, email: str, message: str) -> Dict[str, Any]:
        """Create a new contact message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO messages (name, email, message)
                VALUES (?, ?, ?)
            """, (name, email, message))
            
            message_id = cursor.lastrowid
            if self.db_type == "sqlite":

                conn.commit()
            
            return {
                "id": message_id,
                "name": name,
                "email": email,
                "message": message,
                "status": "unread",
                "created_at": datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """Get all contact messages (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, message, status, created_at
            FROM messages ORDER BY created_at DESC
        """)
        
        messages = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": message[0],
                "name": message[1],
                "email": message[2],
                "message": message[3],
                "status": message[4],
                "created_at": message[5]
            }
            for message in messages
        ]
    
    def update_message_status(self, message_id: int, status: str) -> bool:
        """Update message status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE messages SET status = ? WHERE id = ?
        """, (status, message_id))
        
        updated = cursor.rowcount > 0
        if self.db_type == "sqlite":

            conn.commit()
        conn.close()
        
        return updated
    
    def delete_message(self, message_id: int) -> bool:
        """Delete a message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        
        deleted = cursor.rowcount > 0
        if self.db_type == "sqlite":

            conn.commit()
        conn.close()
        
        return deleted
    
    # Announcement management methods
    def create_announcement(self, title: str, content: str, priority: str, created_by: int) -> Dict[str, Any]:
        """Create a new announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO announcements (title, content, priority, created_by)
                VALUES (?, ?, ?, ?)
            """, (title, content, priority, created_by))
            
            announcement_id = cursor.lastrowid
            if self.db_type == "sqlite":

                conn.commit()
            
            return {
                "id": announcement_id,
                "title": title,
                "content": content,
                "priority": priority,
                "is_active": True,
                "created_by": created_by,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def get_all_announcements(self) -> List[Dict[str, Any]]:
        """Get all announcements"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.title, a.content, a.priority, a.is_active, 
                   a.created_by, u.name, a.created_at, a.updated_at
            FROM announcements a
            JOIN users u ON a.created_by = u.id
            ORDER BY a.created_at DESC
        """)
        
        announcements = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": announcement[0],
                "title": announcement[1],
                "content": announcement[2],
                "priority": announcement[3],
                "is_active": bool(announcement[4]),
                "created_by": announcement[5],
                "created_by_name": announcement[6],
                "created_at": announcement[7],
                "updated_at": announcement[8]
            }
            for announcement in announcements
        ]
    
    def get_active_announcements(self) -> List[Dict[str, Any]]:
        """Get active announcements for users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, priority, created_at
            FROM announcements 
            WHERE is_active = 1
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'normal' THEN 2 
                    WHEN 'low' THEN 3 
                END,
                created_at DESC
        """)
        
        announcements = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": announcement[0],
                "title": announcement[1],
                "content": announcement[2],
                "priority": announcement[3],
                "created_at": announcement[4]
            }
            for announcement in announcements
        ]
    
    def update_announcement(self, announcement_id: int, title: str, content: str, priority: str, is_active: bool) -> bool:
        """Update an announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE announcements 
            SET title = ?, content = ?, priority = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, priority, is_active, announcement_id))
        
        updated = cursor.rowcount > 0
        if self.db_type == "sqlite":

            conn.commit()
        conn.close()
        
        return updated
    
    def delete_announcement(self, announcement_id: int) -> bool:
        """Delete an announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        
        deleted = cursor.rowcount > 0
        if self.db_type == "sqlite":

            conn.commit()
        conn.close()
        
        return deleted