import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

class DatabaseManager:
    def __init__(self, db_path: str = "robot_console.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Sessions table for JWT token management
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Messages table for contact form submissions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'unread',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Announcements table for admin announcements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)
        
        conn.commit()
        
        # Create default admin user if none exists
        self._create_default_admin(cursor, conn)
        
        conn.close()
    
    def _create_default_admin(self, cursor, conn):
        """Create a default admin user if no admin exists"""
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            admin_password = "admin123"
            password_hash = self._hash_password(admin_password)
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, ("Admin User", "admin@robot-console.com", password_hash, "admin"))
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, password_hash, role))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Return user without password
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role,
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.IntegrityError:
            raise ValueError("Email already exists")
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return user data if valid"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, password_hash, role, created_at
            FROM users WHERE email = ?
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, role, created_at
            FROM users WHERE id = ?
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO bookings (user_id, robot_type, date, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, robot_type, date, start_time, end_time))
            
            booking_id = cursor.lastrowid
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bookings SET status = ? WHERE id = ?
        """, (status, booking_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_bookings_for_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get bookings within a date range"""
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO messages (name, email, message)
                VALUES (?, ?, ?)
            """, (name, email, message))
            
            message_id = cursor.lastrowid
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE messages SET status = ? WHERE id = ?
        """, (status, message_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def delete_message(self, message_id: int) -> bool:
        """Delete a message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    # Announcement management methods
    def create_announcement(self, title: str, content: str, priority: str, created_by: int) -> Dict[str, Any]:
        """Create a new announcement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO announcements (title, content, priority, created_by)
                VALUES (?, ?, ?, ?)
            """, (title, content, priority, created_by))
            
            announcement_id = cursor.lastrowid
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE announcements 
            SET title = ?, content = ?, priority = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, content, priority, is_active, announcement_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def delete_announcement(self, announcement_id: int) -> bool:
        """Delete an announcement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted