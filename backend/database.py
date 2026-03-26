import pymysql
import os
import hashlib
import secrets
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_type = os.getenv('DATABASE_TYPE', 'mysql').lower()
        
        if self.db_type != 'mysql':
            raise ValueError(f"Only MySQL is supported. Found DATABASE_TYPE={self.db_type}")
        
        # MySQL configuration
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
        """Get MySQL database connection"""
        return pymysql.connect(**self.mysql_config)
    
    def _get_placeholder(self):
        """Get the MySQL parameter placeholder"""
        return "%s"
    
    def init_database(self):
        """Initialize the MySQL database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # MySQL syntax
        auto_increment = "AUTO_INCREMENT"
        text_type = "TEXT"
        timestamp_default = "DEFAULT CURRENT_TIMESTAMP"
        primary_key = "PRIMARY KEY AUTO_INCREMENT"
        
        # Users table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER {primary_key},
                name {text_type} NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash {text_type} NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                theia_port INTEGER DEFAULT NULL,
                theia_booking_port INTEGER DEFAULT NULL,
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
        
        # Robots table for robot registry
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS robots (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                webrtc_url VARCHAR(500),
                rtsp_url VARCHAR(500),
                upload_endpoint VARCHAR(500),
                container_image VARCHAR(255),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Add webrtc_url column to existing robots table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE robots ADD COLUMN webrtc_url VARCHAR(500)")
        except pymysql.Error:
            pass
        
        # Add rtsp_url column to existing robots table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE robots ADD COLUMN rtsp_url VARCHAR(500)")
        except pymysql.Error:
            pass
        
        # Add upload_endpoint column for robot code upload URLs
        try:
            cursor.execute("ALTER TABLE robots ADD COLUMN upload_endpoint VARCHAR(500)")
        except pymysql.Error:
            pass

        # Add container_image column for per-robot container image metadata
        try:
            cursor.execute("ALTER TABLE robots ADD COLUMN container_image VARCHAR(255)")
        except pymysql.Error:
            pass
        
        # Add theia_port column to users table for persistent port storage
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN theia_port INTEGER DEFAULT NULL")
        except pymysql.Error:
            pass
        
        # Add theia_booking_port column to users table for booking container port storage
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN theia_booking_port INTEGER DEFAULT NULL")
        except pymysql.Error:
            pass
        
        # Add is_active column for email confirmation
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active TINYINT(1) DEFAULT 0")
        except pymysql.Error:
            pass
        
        # Add email_confirmed_at column for tracking confirmation timestamp
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email_confirmed_at DATETIME NULL")
        except pymysql.Error:
            pass
        
        # Add google_id column for Google OAuth
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(255) NULL")
        except pymysql.Error:
            pass
        
        # Add google_name column for Google OAuth
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN google_name VARCHAR(255) NULL")
        except pymysql.Error:
            pass
        
        # Migration: Copy code_api_url to upload_endpoint if upload_endpoint is empty
        try:
            cursor.execute("""
                UPDATE robots 
                SET upload_endpoint = code_api_url 
                WHERE upload_endpoint IS NULL AND code_api_url IS NOT NULL
            """)
        except pymysql.Error:
            pass
        
        # Migration: Remove deprecated code_api_url column
        try:
            cursor.execute("ALTER TABLE robots DROP COLUMN code_api_url")
        except pymysql.Error:
            pass  # Column doesn't exist or already dropped
        
        # Add robot_id column to bookings table for specific robot assignment
        try:
            cursor.execute("ALTER TABLE bookings ADD COLUMN robot_id INTEGER")
        except pymysql.Error:
            pass  # Column already exists

        # Add last_login column for tracking user login timestamps
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME NULL")
        except pymysql.Error:
            pass  # Column already exists

        # Add login_count column for tracking number of logins
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN login_count INT DEFAULT 0")
        except pymysql.Error:
            pass  # Column already exists

        # Add theia_admin_watch_port column for admin surveillance watch container
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN theia_admin_watch_port INTEGER DEFAULT NULL")
        except pymysql.Error:
            pass  # Column already exists

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
        """Create a new user (inactive by default, requires email confirmation)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute(f"""
                INSERT INTO users (name, email, password_hash, role, is_active)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 0)
            """, (name, email, password_hash, role))
            
            user_id = cursor.lastrowid
            
            # Return user without password
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role,
                "is_active": False,
                "created_at": datetime.now().isoformat()
            }
        except pymysql.IntegrityError:
            raise ValueError("Email already exists")
        finally:
            conn.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return user data if valid and active"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT id, name, email, password_hash, role, created_at, is_active
            FROM users WHERE email = {placeholder}
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            # User not found in database
            return None
        
        # Check if user is active
        is_active = user[6] if len(user) > 6 else False
        
        if self._verify_password(password, user[3]):
            return {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[4],
                "created_at": user[5],
                "is_active": is_active
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
            SELECT id, name, email, role, theia_port, created_at
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
                "theia_port": user[4],
                "created_at": user[5]
            }
        return None
    
    def get_user_theia_port(self, user_id: int) -> Optional[int]:
        """Get user's assigned Theia port from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT theia_port FROM users WHERE id = {placeholder}
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else None
    
    def set_user_theia_port(self, user_id: int, port: int) -> bool:
        """Set user's assigned Theia port in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users SET theia_port = {placeholder} WHERE id = {placeholder}
        """, (port, user_id))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def clear_user_theia_port(self, user_id: int) -> bool:
        """Clear user's assigned Theia port in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users SET theia_port = NULL WHERE id = {placeholder}
        """, (user_id,))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def get_user_theia_booking_port(self, user_id: int) -> Optional[int]:
        """Get user's assigned booking Theia port from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT theia_booking_port FROM users WHERE id = {placeholder}
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else None
    
    def set_user_theia_booking_port(self, user_id: int, port: int) -> bool:
        """Set user's assigned booking Theia port in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users SET theia_booking_port = {placeholder} WHERE id = {placeholder}
        """, (port, user_id))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def clear_user_theia_booking_port(self, user_id: int) -> bool:
        """Clear user's assigned booking Theia port in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users SET theia_booking_port = NULL WHERE id = {placeholder}
        """, (user_id,))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT id, name, email, role, is_active, email_confirmed_at, google_id, google_name, created_at
            FROM users WHERE email = {placeholder}
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[3],
                "is_active": user[4] if user[4] is not None else False,
                "email_confirmed_at": user[5],
                "google_id": user[6],
                "google_name": user[7],
                "created_at": user[8]
            }
        return None
    
    def activate_user_by_email(self, email: str) -> bool:
        """Activate user account by email and set confirmation timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users 
            SET is_active = 1, email_confirmed_at = {placeholder}
            WHERE email = {placeholder}
        """, (datetime.now(), email))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def store_password_reset_token(self, email: str, token: str, expires: datetime) -> bool:
        """Store password reset token for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users 
            SET password_reset_token = {placeholder}, 
                password_reset_expires = {placeholder}
            WHERE email = {placeholder}
        """, (token, expires, email))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def validate_password_reset_token(self, token: str) -> Optional[str]:
        """Validate password reset token and return email if valid"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT email, password_reset_expires 
            FROM users 
            WHERE password_reset_token = {placeholder}
        """, (token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        email, expires = result
        
        # Check if token has expired
        if expires:
            # Ensure expires is a datetime object
            if isinstance(expires, str):
                from datetime import datetime
                expires = datetime.fromisoformat(expires)
            
            if datetime.now() > expires:
                return None
        
        return email
    
    def update_user_password(self, email: str, new_password: str) -> bool:
        """Update user password and clear reset token"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        # Hash the new password
        password_hash = self._hash_password(new_password)
        
        cursor.execute(f"""
            UPDATE users 
            SET password_hash = {placeholder}, 
                password_reset_token = NULL, 
                password_reset_expires = NULL
            WHERE email = {placeholder}
        """, (password_hash, email))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def update_user_role(self, user_id: int, new_role: str) -> Dict[str, Any]:
        """Update user role (admin or user)"""
        if new_role not in ["admin", "user"]:
            raise ValueError(f"Invalid role: {new_role}. Must be 'admin' or 'user'.")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"""
            UPDATE users SET role = {placeholder} WHERE id = {placeholder}
        """, (new_role, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            raise ValueError(f"User with ID {user_id} not found")
        
        # Get updated user info
        cursor.execute(f"""
            SELECT id, name, email, role, is_active, created_at
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
                "is_active": user[4],
                "created_at": user[5]
            }
        return None
    
    def update_user_activity(self, user_id: int, activity_type: str = 'login'):
        """Update user activity tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        now = datetime.now()
        
        if activity_type == 'login':
            cursor.execute(f"""
                UPDATE users 
                SET last_login = {placeholder}, 
                    last_activity = {placeholder}, 
                    login_count = COALESCE(login_count, 0) + 1
                WHERE id = {placeholder}
            """, (now, now, user_id))
        else:
            cursor.execute(f"""
                UPDATE users 
                SET last_activity = {placeholder}
                WHERE id = {placeholder}
            """, (now, user_id))
        
        conn.close()
    
    def delete_user_cascade(self, user_id: int) -> Dict[str, Any]:
        """Delete user and all related data (bookings, sessions, messages)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        # Track deleted records
        deleted = {
            "user_id": user_id,
            "bookings": 0,
            "sessions": 0,
            "messages": 0
        }
        
        # Delete bookings
        cursor.execute(f"""
            DELETE FROM bookings WHERE user_id = {placeholder}
        """, (user_id,))
        deleted["bookings"] = cursor.rowcount
        
        # Delete sessions
        cursor.execute(f"""
            DELETE FROM sessions WHERE user_id = {placeholder}
        """, (user_id,))
        deleted["sessions"] = cursor.rowcount
        
        # Note: Messages don't have user_id foreign key in current schema
        # but we'll handle it if they're associated
        
        # Delete user
        cursor.execute(f"""
            DELETE FROM users WHERE id = {placeholder}
        """, (user_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise ValueError(f"User with ID {user_id} not found")
        
        conn.close()
        return deleted
    
    def upsert_google_user(self, email: str, name: str, google_id: str) -> Dict[str, Any]:
        """Create or update user from Google OAuth"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        try:
            # First, check if user exists by google_id (most specific)
            cursor.execute(f"""
                SELECT id, name, email, role, google_id, created_at
                FROM users WHERE google_id = {placeholder}
            """, (google_id,))
            
            existing_user = cursor.fetchone()
            
            # If not found by google_id, check by email
            if not existing_user:
                cursor.execute(f"""
                    SELECT id, name, email, role, google_id, created_at
                    FROM users WHERE email = {placeholder}
                """, (email,))
                existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user with Google info
                cursor.execute(f"""
                    UPDATE users 
                    SET google_id = {placeholder}, google_name = {placeholder}, 
                        is_active = 1, email_confirmed_at = {placeholder}
                    WHERE id = {placeholder}
                """, (google_id, name, datetime.now(), existing_user[0]))
                
                return {
                    "id": existing_user[0],
                    "name": name,
                    "email": email,
                    "role": existing_user[3],
                    "google_id": google_id,
                    "google_name": name,
                    "is_active": True,
                    "created_at": existing_user[5]
                }
            else:
                # Create new user
                # Generate a random password hash (not used for Google auth)
                password_hash = self._hash_password(secrets.token_urlsafe(32))
                
                cursor.execute(f"""
                    INSERT INTO users (name, email, password_hash, role, is_active, 
                                     email_confirmed_at, google_id, google_name)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                            1, {placeholder}, {placeholder}, {placeholder})
                """, (name, email, password_hash, "user", datetime.now(), google_id, name))
                
                user_id = cursor.lastrowid
                
                return {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "role": "user",
                    "google_id": google_id,
                    "google_name": name,
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
        finally:
            conn.close()
    
    def get_all_assigned_ports(self) -> List[int]:
        """Get all currently assigned Theia ports (preview, booking, and admin watch)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT theia_port FROM users WHERE theia_port IS NOT NULL
        """)
        preview_ports = [result[0] for result in cursor.fetchall() if result[0]]
        
        try:
            cursor.execute("""
                SELECT theia_booking_port FROM users WHERE theia_booking_port IS NOT NULL
            """)
            booking_ports = [result[0] for result in cursor.fetchall() if result[0]]
        except Exception:
            booking_ports = []
        
        try:
            cursor.execute("""
                SELECT theia_admin_watch_port FROM users WHERE theia_admin_watch_port IS NOT NULL
            """)
            admin_watch_ports = [result[0] for result in cursor.fetchall() if result[0]]
        except Exception:
            admin_watch_ports = []
        
        conn.close()
        
        return preview_ports + booking_ports + admin_watch_ports

    def get_user_theia_admin_watch_port(self, user_id: int) -> Optional[int]:
        """Get admin's assigned watch container port from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        cursor.execute(f"SELECT theia_admin_watch_port FROM users WHERE id = {placeholder}", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

    def set_user_theia_admin_watch_port(self, user_id: int, port: int) -> bool:
        """Set admin's assigned watch container port in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        cursor.execute(f"UPDATE users SET theia_admin_watch_port = {placeholder} WHERE id = {placeholder}", (port, user_id))
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def clear_user_theia_admin_watch_port(self, user_id: int) -> bool:
        """Clear admin's assigned watch container port in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        cursor.execute(f"UPDATE users SET theia_admin_watch_port = NULL WHERE id = {placeholder}", (user_id,))
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def get_active_bookings_now(self) -> List[Dict[str, Any]]:
        """Get all bookings that are currently active (within their time window today)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        placeholder = self._get_placeholder()
        cursor.execute(f"""
            SELECT b.id, b.user_id, u.name, u.email, b.robot_type, b.robot_id,
                   b.date, b.start_time, b.end_time, b.status, r.name as robot_name, r.container_image
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            LEFT JOIN robots r ON b.robot_id = r.id
            WHERE b.date = {placeholder}
              AND b.status = 'active'
            ORDER BY b.start_time
        """, (current_date,))
        bookings = cursor.fetchall()
        conn.close()

        current_time_obj = now.time()
        active_now = []
        for b in bookings:
            start_time_obj = self._parse_time_value(b[7])
            end_time_obj = self._parse_time_value(b[8])
            if not start_time_obj or not end_time_obj:
                continue
            if not (start_time_obj <= current_time_obj <= end_time_obj):
                continue
            active_now.append(
                {
                    "id": b[0],
                    "user_id": b[1],
                    "user_name": b[2],
                    "user_email": b[3],
                    "robot_type": b[4],
                    "robot_id": b[5],
                    "date": b[6],
                    "start_time": b[7],
                    "end_time": b[8],
                    "status": b[9],
                    "robot_name": b[10] or "Unknown",
                    "robot_image": b[11],
                }
            )
        return active_now

    @staticmethod
    def _parse_time_value(value: Optional[str]) -> Optional[time]:
        """Parse HH:MM or HH:MM:SS time string; return None when parsing fails."""
        normalized = (value or "").strip()
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(normalized, fmt).time()
            except ValueError:
                continue
        return None

    
    def _find_available_robot(self, robot_type: str, date: str, start_time: str, end_time: str, cursor) -> Optional[Dict[str, Any]]:
        """Find an available robot of the specified type for the given time slot"""
        placeholder = self._get_placeholder()
        
        # Get all active robots of the requested type
        cursor.execute(f"""
            SELECT id, name, type, webrtc_url, upload_endpoint, status, created_at, updated_at
            FROM robots WHERE type = {placeholder} AND status = 'active'
            ORDER BY created_at ASC
        """, (robot_type,))
        
        robots = cursor.fetchall()
        
        for robot_row in robots:
            robot = {
                "id": robot_row[0],
                "name": robot_row[1],
                "type": robot_row[2],
                "webrtc_url": robot_row[3],
                "upload_endpoint": robot_row[4],
                "status": robot_row[5],
                "created_at": robot_row[6].isoformat() if robot_row[6] else None,
                "updated_at": robot_row[7].isoformat() if robot_row[7] else None
            }
            
            # Check if this robot is available for the requested time slot
            if self._is_robot_available(robot["id"], date, start_time, end_time, cursor):
                return robot
        
        return None
    
    def _is_robot_available(self, robot_id: int, date: str, start_time: str, end_time: str, cursor) -> bool:
        """Check if a specific robot is available for the given time slot"""
        placeholder = self._get_placeholder()

        # Get existing bookings for this robot on the same date
        cursor.execute(f"""
            SELECT start_time, end_time FROM bookings 
            WHERE robot_id = {placeholder} AND date = {placeholder} AND status IN ('active', 'scheduled')
        """, (robot_id, date))
        
        existing_bookings = cursor.fetchall()
        
        # Check for time conflicts using the same logic as booking service
        from datetime import time
        
        def parse_time_string(time_str: str) -> time:
            parsed = self._parse_time_value(time_str)
            if parsed is None:
                raise ValueError(f"Invalid time format: {time_str}")
            return parsed
        
        def times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
            t1_start = parse_time_string(start1)
            t1_end = parse_time_string(end1)
            t2_start = parse_time_string(start2)
            t2_end = parse_time_string(end2)
            return t1_start < t2_end and t2_start < t1_end
        
        for existing_start, existing_end in existing_bookings:
            if times_overlap(start_time, end_time, existing_start, existing_end):
                return False
        
        return True
    
    def create_booking(self, user_id: int, robot_id: int, date: str, start_time: str, end_time: str, robot_type: Optional[str] = None) -> Dict[str, Any]:
        """Create a new booking for a specific robot instance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        try:
            # Resolve robot details
            robot = self.get_robot_by_id(robot_id)
            if not robot or robot.get("status") != "active":
                raise HTTPException(status_code=404, detail=f"Robot {robot_id} not found or inactive")
            robot_type = robot_type or robot.get("type")

            # Enforce no overlap for this robot/time window
            if not self._is_robot_available(robot_id, date, start_time, end_time, cursor):
                raise HTTPException(
                    status_code=409,
                    detail=f"Robot {robot_id} is already booked for the requested time slot"
                )
            
            cursor.execute(f"""
                INSERT INTO bookings (user_id, robot_type, robot_id, date, start_time, end_time)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (user_id, robot_type, robot_id, date, start_time, end_time))
            
            booking_id = cursor.lastrowid
            
            return {
                "id": booking_id,
                "user_id": user_id,
                "robot_type": robot_type,
                "robot_id": robot_id,
                "robot_name": robot.get('name', 'Unknown'),
                "robot_image": robot.get("container_image"),
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user with robot information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT b.id, b.user_id, b.robot_type, b.robot_id, b.date, b.start_time, b.end_time, b.status, b.created_at,
                   r.name as robot_name, r.container_image
            FROM bookings b
            LEFT JOIN robots r ON b.robot_id = r.id
            WHERE b.user_id = {self._get_placeholder()} 
            ORDER BY b.date DESC, b.start_time DESC
        """, (user_id,))
        
        bookings = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": booking[0],
                "user_id": booking[1],
                "robot_type": booking[2],
                "robot_id": booking[3],
                "date": booking[4],
                "start_time": booking[5],
                "end_time": booking[6],
                "status": booking[7],
                "created_at": booking[8].isoformat() if booking[8] else None,
                "robot_name": booking[9] or "Unknown",
                "robot_image": booking[10]
            }
            for booking in bookings
        ]
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Get all bookings (admin only) with robot information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.id, b.user_id, u.name, u.email, b.robot_type, b.robot_id, b.date, 
                   b.start_time, b.end_time, b.status, b.created_at, r.name as robot_name, r.container_image
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            LEFT JOIN robots r ON b.robot_id = r.id
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
                "robot_id": booking[5],
                "date": booking[6],
                "start_time": booking[7],
                "end_time": booking[8],
                "status": booking[9],
                "created_at": booking[10].isoformat() if booking[10] else None,
                "robot_name": booking[11] or "Unknown",
                "robot_image": booking[12]
            }
            for booking in bookings
        ]
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, role, created_at, is_active, last_login, login_count
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
                "created_at": user[4].isoformat() if user[4] else None,
                "is_active": bool(user[5]) if user[5] is not None else False,
                "last_login": user[6].isoformat() if user[6] else None,
                "login_count": user[7] or 0
            }
            for user in users
        ]
    
    def update_booking_status(self, booking_id: int, status: str) -> Optional[Dict[str, Any]]:
        """Update booking status and return the updated booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()

        cursor.execute(f"""
            UPDATE bookings SET status = {placeholder} WHERE id = {placeholder}
        """, (status, booking_id))

        if cursor.rowcount == 0:
            conn.close()
            return None

        cursor.execute(f"""
            SELECT b.id, b.user_id, u.name, u.email, b.robot_type, b.robot_id, b.date,
                   b.start_time, b.end_time, b.status, b.created_at, r.name as robot_name, r.container_image
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            LEFT JOIN robots r ON b.robot_id = r.id
            WHERE b.id = {placeholder}
        """, (booking_id,))

        booking = cursor.fetchone()
        conn.close()

        if not booking:
            return None

        return {
            "id": booking[0],
            "user_id": booking[1],
            "user_name": booking[2],
            "user_email": booking[3],
            "robot_type": booking[4],
            "robot_id": booking[5],
            "date": booking[6],
            "start_time": booking[7],
            "end_time": booking[8],
            "status": booking[9],
            "created_at": booking[10].isoformat() if booking[10] else None,
            "robot_name": booking[11] if len(booking) > 11 else None,
            "robot_image": booking[12] if len(booking) > 12 else None
        }
    
    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DELETE FROM bookings WHERE id = {self._get_placeholder()}", (booking_id,))
        
        deleted = cursor.rowcount > 0
        conn.close()
        
        return deleted
    
    def get_bookings_for_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get bookings within a date range with robot information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT b.id, b.user_id, u.name, b.robot_type, b.robot_id, b.date, 
                   b.start_time, b.end_time, b.status, r.name as robot_name, r.container_image
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            LEFT JOIN robots r ON b.robot_id = r.id  
            WHERE b.date >= {self._get_placeholder()} AND b.date <= {self._get_placeholder()} AND b.status IN ('active', 'scheduled')
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
                "robot_id": booking[4],
                "date": booking[5],
                "start_time": booking[6],
                "end_time": booking[7],
                "status": booking[8],
                "robot_name": booking[9] or "Unknown",
                "robot_image": booking[10]
            }
            for booking in bookings
        ]
    
    # Message management methods
    def create_message(self, name: str, email: str, message: str) -> Dict[str, Any]:
        """Create a new contact message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                INSERT INTO messages (name, email, message)
                VALUES ({self._get_placeholder()}, {self._get_placeholder()}, {self._get_placeholder()})
            """, (name, email, message))
            
            message_id = cursor.lastrowid
            
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
                "created_at": message[5].isoformat() if hasattr(message[5], 'isoformat') else str(message[5]) if message[5] else None
            }
            for message in messages
        ]
    
    def update_message_status(self, message_id: int, status: str) -> bool:
        """Update message status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE messages SET status = {self._get_placeholder()} WHERE id = {self._get_placeholder()}
        """, (status, message_id))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def delete_message(self, message_id: int) -> bool:
        """Delete a message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DELETE FROM messages WHERE id = {self._get_placeholder()}", (message_id,))
        
        deleted = cursor.rowcount > 0
        conn.close()
        
        return deleted
    
    # Announcement management methods
    def create_announcement(self, title: str, content: str, priority: str, created_by: int) -> Dict[str, Any]:
        """Create a new announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                INSERT INTO announcements (title, content, priority, created_by)
                VALUES ({self._get_placeholder()}, {self._get_placeholder()}, {self._get_placeholder()}, {self._get_placeholder()})
            """, (title, content, priority, created_by))
            
            announcement_id = cursor.lastrowid
            
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
                "created_at": announcement[7].isoformat() if hasattr(announcement[7], 'isoformat') else str(announcement[7]) if announcement[7] else None,
                "updated_at": announcement[8].isoformat() if hasattr(announcement[8], 'isoformat') else str(announcement[8]) if announcement[8] else None
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
        
        cursor.execute(f"""
            UPDATE announcements 
            SET title = {self._get_placeholder()}, content = {self._get_placeholder()}, priority = {self._get_placeholder()}, is_active = {self._get_placeholder()}, updated_at = CURRENT_TIMESTAMP
            WHERE id = {self._get_placeholder()}
        """, (title, content, priority, is_active, announcement_id))
        
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def delete_announcement(self, announcement_id: int) -> bool:
        """Delete an announcement"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DELETE FROM announcements WHERE id = {self._get_placeholder()}", (announcement_id,))
        
        deleted = cursor.rowcount > 0
        conn.close()
        
        return deleted
    
    # Robot Registry Methods
    
    def create_robot(self, name: str, robot_type: str, webrtc_url: str = None, rtsp_url: str = None, upload_endpoint: str = None, container_image: str = None, status: str = 'active') -> Dict[str, Any]:
        """Create a new robot in the registry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        try:
            cursor.execute(f"""
                INSERT INTO robots (name, type, webrtc_url, rtsp_url, upload_endpoint, container_image, status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (name, robot_type, webrtc_url, rtsp_url, upload_endpoint, container_image, status))
            robot_id = cursor.lastrowid
            return {
                "id": robot_id,
                "name": name,
                "type": robot_type,
                "webrtc_url": webrtc_url,
                "rtsp_url": rtsp_url,
                "upload_endpoint": upload_endpoint,
                "container_image": container_image,
                "status": status,
                "created_at": datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def get_all_robots(self) -> List[Dict[str, Any]]:
        """Get all robots from the registry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, type, webrtc_url, rtsp_url, upload_endpoint, container_image, status, created_at, updated_at
            FROM robots ORDER BY created_at DESC
        """)
        robots = cursor.fetchall()
        conn.close()
        return [
            {
                "id": robot[0],
                "name": robot[1],
                "type": robot[2],
                "webrtc_url": robot[3],
                "rtsp_url": robot[4],
                "upload_endpoint": robot[5],
                "container_image": robot[6],
                "status": robot[7],
                "created_at": robot[8].isoformat() if robot[8] else None,
                "updated_at": robot[9].isoformat() if robot[9] else None
            }
            for robot in robots
        ]
    
    def get_robot_by_id(self, robot_id: int) -> Optional[Dict[str, Any]]:
        """Get a robot by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        cursor.execute(f"""
            SELECT id, name, type, webrtc_url, rtsp_url, upload_endpoint, container_image, status, created_at, updated_at
            FROM robots WHERE id = {placeholder}
        """, (robot_id,))
        robot = cursor.fetchone()
        conn.close()
        if not robot:
            return None
        return {
            "id": robot[0],
            "name": robot[1],
            "type": robot[2],
            "webrtc_url": robot[3],
            "rtsp_url": robot[4],
            "upload_endpoint": robot[5],
            "container_image": robot[6],
            "status": robot[7],
            "created_at": robot[8].isoformat() if robot[8] else None,
            "updated_at": robot[9].isoformat() if robot[9] else None
        }

    def get_robot_by_type(self, robot_type: str) -> Optional[Dict[str, Any]]:
        """Get a robot by type (returns first match)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        cursor.execute(f"""
            SELECT id, name, type, webrtc_url, rtsp_url, upload_endpoint, container_image, status, created_at, updated_at
            FROM robots WHERE type = {placeholder} LIMIT 1
        """, (robot_type,))
        robot = cursor.fetchone()
        conn.close()
        if not robot:
            return None
        return {
            "id": robot[0],
            "name": robot[1],
            "type": robot[2],
            "webrtc_url": robot[3],
            "rtsp_url": robot[4],
            "upload_endpoint": robot[5],
            "container_image": robot[6],
            "status": robot[7],
            "created_at": robot[8].isoformat() if robot[8] else None,
            "updated_at": robot[9].isoformat() if robot[9] else None
        }

    def update_robot(self, robot_id: int, name: str = None, robot_type: str = None, webrtc_url: str = None, rtsp_url: str = None, upload_endpoint: str = None, container_image: str = None, status: str = None) -> bool:
        """Update a robot in the registry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        update_fields = []
        update_values = []

        if name is not None:
            update_fields.append(f"name = {placeholder}")
            update_values.append(name)
        if robot_type is not None:
            update_fields.append(f"type = {placeholder}")
            update_values.append(robot_type)
        if webrtc_url is not None:
            update_fields.append(f"webrtc_url = {placeholder}")
            update_values.append(webrtc_url)
        if rtsp_url is not None:
            update_fields.append(f"rtsp_url = {placeholder}")
            update_values.append(rtsp_url)
        if upload_endpoint is not None:
            update_fields.append(f"upload_endpoint = {placeholder}")
            update_values.append(upload_endpoint)
        if container_image is not None:
            update_fields.append(f"container_image = {placeholder}")
            update_values.append(container_image)
        if status is not None:
            update_fields.append(f"status = {placeholder}")
            update_values.append(status)
        if not update_fields:
            conn.close()
            return False
        update_fields.append(f"updated_at = NOW()")
        update_values.append(robot_id)
        query = f"UPDATE robots SET {', '.join(update_fields)} WHERE id = {placeholder}"
        cursor.execute(query, update_values)
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def get_active_robots(self) -> List[Dict[str, Any]]:
        """Get all active robots from the registry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, type, webrtc_url, rtsp_url, upload_endpoint, container_image, status, created_at, updated_at
            FROM robots WHERE status = 'active' ORDER BY created_at DESC
        """)
        robots = cursor.fetchall()
        conn.close()
        return [
            {
                "id": robot[0],
                "name": robot[1],
                "type": robot[2],
                "webrtc_url": robot[3],
                "rtsp_url": robot[4],
                "upload_endpoint": robot[5],
                "container_image": robot[6],
                "status": robot[7],
                "created_at": robot[8].isoformat() if robot[8] else None,
                "updated_at": robot[9].isoformat() if robot[9] else None
            }
            for robot in robots
        ]

    def get_active_robot_by_type(self, robot_type: str) -> Optional[Dict[str, Any]]:
        """Get an active robot by type (returns first active match)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        cursor.execute(f"""
            SELECT id, name, type, webrtc_url, rtsp_url, upload_endpoint, container_image, status, created_at, updated_at
            FROM robots WHERE type = {placeholder} AND status = 'active' LIMIT 1
        """, (robot_type,))
        robot = cursor.fetchone()
        conn.close()
        if not robot:
            return None
        return {
            "id": robot[0],
            "name": robot[1],
            "type": robot[2],
            "webrtc_url": robot[3],
            "rtsp_url": robot[4],
            "upload_endpoint": robot[5],
            "container_image": robot[6],
            "status": robot[7],
            "created_at": robot[8].isoformat() if robot[8] else None,
            "updated_at": robot[9].isoformat() if robot[9] else None
        }

    
    def delete_robot(self, robot_id: int) -> bool:
        """Delete a robot from the registry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholder = self._get_placeholder()
        
        cursor.execute(f"DELETE FROM robots WHERE id = {placeholder}", (robot_id,))
        
        deleted = cursor.rowcount > 0
        conn.close()
        
        return deleted
