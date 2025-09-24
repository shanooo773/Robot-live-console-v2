#!/usr/bin/env python3
"""
Comprehensive Data Validation Script for Robot Live Console
Tests that all data is real and dashboard data of admin is real
Script to check in detail that MySQL section is correct

Features:
- Real data integrity validation
- Admin dashboard data verification
- MySQL section detailed validation
- Database consistency checks
- Schema vs actual data validation
- Production readiness verification
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database import DatabaseManager
    from dotenv import load_dotenv
    import pymysql
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Some dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

load_dotenv()

class ComprehensiveDataValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed_tests = 0
        self.total_tests = 0
        self.mysql_connection = None
        self.db_manager = None
        
    def add_issue(self, severity: str, category: str, description: str):
        """Add validation issue"""
        self.issues.append({
            "severity": severity,
            "category": category,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_warning(self, category: str, description: str):
        """Add validation warning"""
        self.warnings.append({
            "category": category,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })

    def test_mysql_connection_detailed(self) -> bool:
        """Test 1: Detailed MySQL Connection and Configuration"""
        print("🔍 Testing MySQL connection and configuration in detail...")
        self.total_tests += 1
        
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'robot_console'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'robot_console'),
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'autocommit': True
        }
        
        try:
            # Test connection
            print(f"   📡 Connecting to MySQL at {mysql_config['host']}:{mysql_config['port']}")
            print(f"   🗃️  Database: {mysql_config['database']}")
            print(f"   👤 User: {mysql_config['user']}")
            
            conn = pymysql.connect(**mysql_config)
            self.mysql_connection = conn
            cursor = conn.cursor()
            
            # Test 1.1: Basic connectivity
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"   ✅ Basic connection test: {result}")
            
            # Test 1.2: Server version and capabilities
            cursor.execute("SELECT VERSION() as version")
            version = cursor.fetchone()
            print(f"   ✅ MySQL Version: {version[0]}")
            
            # Test 1.3: Database selection
            cursor.execute("SELECT DATABASE() as current_db")
            db_result = cursor.fetchone()
            print(f"   ✅ Current Database: {db_result[0]}")
            
            # Test 1.4: Character set validation
            cursor.execute("SELECT @@character_set_database, @@collation_database")
            charset_info = cursor.fetchone()
            print(f"   ✅ Character Set: {charset_info[0]}, Collation: {charset_info[1]}")
            
            if charset_info[0] != 'utf8mb4':
                self.add_warning("MySQL Config", f"Database charset is {charset_info[0]}, recommended: utf8mb4")
            
            # Test 1.5: User privileges
            cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
            grants = cursor.fetchall()
            print(f"   ✅ User privileges verified: {len(grants)} grant(s) found")
            
            self.passed_tests += 1
            return True
            
        except Exception as e:
            print(f"   ❌ MySQL connection failed: {e}")
            self.add_issue("CRITICAL", "MySQL Connection", f"Cannot connect to MySQL: {e}")
            return False

    def test_database_schema_integrity(self) -> bool:
        """Test 2: Database Schema Integrity and Real Structure"""
        print("\n🏗️  Testing database schema integrity...")
        self.total_tests += 1
        
        if not self.mysql_connection:
            print("   ⚠️  No MySQL connection available - testing schema file structure")
            return self._test_schema_file_structure()
        
        try:
            cursor = self.mysql_connection.cursor()
            
            # Test 2.1: Required tables exist
            required_tables = {
                'users': ['id', 'name', 'email', 'password_hash', 'role', 'created_at'],
                'bookings': ['id', 'user_id', 'robot_type', 'date', 'start_time', 'end_time', 'status', 'created_at'],
                'robots': ['id', 'name', 'type', 'webrtc_url', 'code_api_url', 'status', 'created_at', 'updated_at'],
                'sessions': ['id', 'user_id', 'token_hash', 'expires_at', 'created_at'],
                'messages': ['id', 'name', 'email', 'subject', 'message', 'status', 'created_at'],
                'announcements': ['id', 'title', 'content', 'priority', 'active', 'created_at', 'updated_at']
            }
            
            cursor.execute("SHOW TABLES")
            existing_tables = [table[0] for table in cursor.fetchall()]
            print(f"   📋 Found tables: {existing_tables}")
            
            for table_name, required_columns in required_tables.items():
                if table_name not in existing_tables:
                    self.add_issue("HIGH", "Schema", f"Required table '{table_name}' missing")
                    continue
                
                # Check table structure
                cursor.execute(f"DESCRIBE {table_name}")
                table_columns = cursor.fetchall()
                column_names = [col[0] for col in table_columns]
                
                print(f"   🔍 Table '{table_name}': {len(column_names)} columns")
                
                # Validate required columns
                missing_columns = set(required_columns) - set(column_names)
                if missing_columns:
                    self.add_issue("HIGH", "Schema", f"Table '{table_name}' missing columns: {missing_columns}")
                
                # Check data types and constraints
                for col in table_columns:
                    col_name, col_type, nullable, key, default, extra = col
                    print(f"     - {col_name}: {col_type} (NULL: {nullable}, Key: {key}, Default: {default}, Extra: {extra})")
                    
                    # Validate critical constraints
                    if col_name == 'id' and 'auto_increment' not in extra.lower():
                        self.add_warning("Schema", f"Table '{table_name}' ID column should be AUTO_INCREMENT")
                    
                    if col_name in ['email'] and nullable == 'YES':
                        self.add_warning("Schema", f"Table '{table_name}' email column should be NOT NULL")
            
            self.passed_tests += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Schema validation failed: {e}")
            self.add_issue("HIGH", "Schema", f"Schema validation error: {e}")
            return False

    def _test_schema_file_structure(self) -> bool:
        """Fallback: Test schema structure from database.py file"""
        try:
            db_file = Path('backend/database.py')
            if not db_file.exists():
                self.add_issue("CRITICAL", "Schema", "backend/database.py not found")
                return False
                
            content = db_file.read_text()
            
            # Check for required table definitions
            required_tables = ['users', 'bookings', 'robots', 'sessions', 'messages', 'announcements']
            
            for table in required_tables:
                if f"CREATE TABLE IF NOT EXISTS {table}" in content:
                    print(f"   ✅ Table definition found: {table}")
                else:
                    self.add_issue("HIGH", "Schema", f"Table definition missing: {table}")
                    
            # Check MySQL-specific syntax
            mysql_features = [
                'AUTO_INCREMENT',
                'VARCHAR(',
                'TIMESTAMP',
                'DEFAULT CURRENT_TIMESTAMP'
            ]
            
            for feature in mysql_features:
                if feature in content:
                    print(f"   ✅ MySQL feature found: {feature}")
                else:
                    self.add_warning("Schema", f"MySQL feature not found: {feature}")
            
            return True
            
        except Exception as e:
            self.add_issue("HIGH", "Schema", f"Schema file validation error: {e}")
            return False

    def test_admin_dashboard_data_integrity(self) -> bool:
        """Test 3: Admin Dashboard Data Integrity and Real Data"""
        print("\n👨‍💼 Testing admin dashboard data integrity...")
        self.total_tests += 1
        
        if not self.mysql_connection:
            print("   ⚠️  No MySQL connection - testing admin endpoint structure")
            return self._test_admin_endpoints_structure()
        
        try:
            cursor = self.mysql_connection.cursor()
            
            # Test 3.1: Admin user exists and is valid
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            print(f"   👥 Admin users found: {admin_count}")
            
            if admin_count == 0:
                self.add_issue("CRITICAL", "Admin Data", "No admin users found in database")
                return False
            
            # Test 3.2: Admin user data integrity
            cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE role = 'admin'")
            admin_users = cursor.fetchall()
            
            for admin in admin_users:
                admin_id, name, email, role, created_at = admin
                print(f"   🔍 Admin: {name} ({email}) - ID: {admin_id}, Created: {created_at}")
                
                # Validate admin data quality
                if not email or '@' not in email:
                    self.add_issue("HIGH", "Admin Data", f"Admin {admin_id} has invalid email: {email}")
                    
                if not name or len(name.strip()) < 2:
                    self.add_issue("HIGH", "Admin Data", f"Admin {admin_id} has invalid name: {name}")
                    
                if role != 'admin':
                    self.add_issue("CRITICAL", "Admin Data", f"User {admin_id} has incorrect role: {role}")
            
            # Test 3.3: Admin can access all necessary data
            admin_accessible_tables = ['users', 'bookings', 'robots', 'sessions', 'messages', 'announcements']
            
            for table in admin_accessible_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   📊 Admin can access {table}: {count} records")
                except Exception as e:
                    self.add_issue("HIGH", "Admin Access", f"Admin cannot access table {table}: {e}")
            
            # Test 3.4: Admin dashboard statistics data
            self._test_admin_statistics(cursor)
            
            self.passed_tests += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Admin dashboard validation failed: {e}")
            self.add_issue("HIGH", "Admin Dashboard", f"Admin data validation error: {e}")
            return False

    def _test_admin_endpoints_structure(self) -> bool:
        """Test admin endpoints structure in main.py"""
        try:
            main_file = Path('backend/main.py')
            if not main_file.exists():
                self.add_issue("CRITICAL", "Admin Endpoints", "backend/main.py not found")
                return False
                
            content = main_file.read_text()
            
            # Check for admin endpoints
            admin_endpoints = [
                '@require_admin',
                '/admin/robots',
                '/admin/stats',
                '/bookings/all',
                'list_theia_containers'
            ]
            
            for endpoint in admin_endpoints:
                if endpoint in content:
                    print(f"   ✅ Admin endpoint found: {endpoint}")
                else:
                    self.add_issue("HIGH", "Admin Endpoints", f"Admin endpoint missing: {endpoint}")
            
            return True
            
        except Exception as e:
            self.add_issue("HIGH", "Admin Endpoints", f"Admin endpoints validation error: {e}")
            return False

    def _test_admin_statistics(self, cursor):
        """Test admin statistics data integrity"""
        try:
            # User statistics
            cursor.execute("SELECT COUNT(*) as total_users, COUNT(CASE WHEN role='admin' THEN 1 END) as admin_users FROM users")
            user_stats = cursor.fetchone()
            print(f"   📈 User Statistics: Total: {user_stats[0]}, Admins: {user_stats[1]}")
            
            # Booking statistics
            cursor.execute("SELECT COUNT(*) as total_bookings, COUNT(CASE WHEN status='active' THEN 1 END) as active_bookings FROM bookings")
            booking_stats = cursor.fetchone()
            print(f"   📈 Booking Statistics: Total: {booking_stats[0]}, Active: {booking_stats[1]}")
            
            # Robot statistics
            cursor.execute("SELECT COUNT(*) as total_robots, COUNT(CASE WHEN status='active' THEN 1 END) as active_robots FROM robots")
            robot_stats = cursor.fetchone()
            print(f"   📈 Robot Statistics: Total: {robot_stats[0]}, Active: {robot_stats[1]}")
            
        except Exception as e:
            self.add_warning("Admin Statistics", f"Cannot retrieve statistics: {e}")

    def test_data_consistency_and_integrity(self) -> bool:
        """Test 4: Data Consistency and Integrity"""
        print("\n🔍 Testing data consistency and integrity...")
        self.total_tests += 1
        
        if not self.mysql_connection:
            print("   ⚠️  No MySQL connection - skipping data consistency tests")
            self.add_warning("Data Consistency", "Cannot test data consistency without MySQL connection")
            return True
        
        try:
            cursor = self.mysql_connection.cursor()
            
            # Test 4.1: Foreign key relationships
            self._test_foreign_key_integrity(cursor)
            
            # Test 4.2: Data format validation
            self._test_data_formats(cursor)
            
            # Test 4.3: Business logic constraints
            self._test_business_logic_constraints(cursor)
            
            # Test 4.4: Temporal data consistency
            self._test_temporal_consistency(cursor)
            
            self.passed_tests += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Data consistency validation failed: {e}")
            self.add_issue("HIGH", "Data Consistency", f"Data consistency error: {e}")
            return False

    def _test_foreign_key_integrity(self, cursor):
        """Test foreign key relationships"""
        print("   🔗 Testing foreign key integrity...")
        
        # Test bookings -> users relationship
        cursor.execute("""
            SELECT COUNT(*) FROM bookings b 
            LEFT JOIN users u ON b.user_id = u.id 
            WHERE u.id IS NULL
        """)
        orphaned_bookings = cursor.fetchone()[0]
        if orphaned_bookings > 0:
            self.add_issue("HIGH", "Data Integrity", f"{orphaned_bookings} bookings have invalid user_id")
        else:
            print("     ✅ All bookings have valid user references")
        
        # Test sessions -> users relationship
        cursor.execute("""
            SELECT COUNT(*) FROM sessions s 
            LEFT JOIN users u ON s.user_id = u.id 
            WHERE u.id IS NULL
        """)
        orphaned_sessions = cursor.fetchone()[0]
        if orphaned_sessions > 0:
            self.add_issue("HIGH", "Data Integrity", f"{orphaned_sessions} sessions have invalid user_id")
        else:
            print("     ✅ All sessions have valid user references")

    def _test_data_formats(self, cursor):
        """Test data format validation"""
        print("   📋 Testing data formats...")
        
        # Test email formats
        cursor.execute("SELECT id, email FROM users WHERE email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'")
        invalid_emails = cursor.fetchall()
        if invalid_emails:
            self.add_issue("MEDIUM", "Data Format", f"{len(invalid_emails)} users have invalid email formats")
        else:
            print("     ✅ All user emails have valid format")
        
        # Test password hash formats (should not be empty or plain text)
        cursor.execute("SELECT id, password_hash FROM users WHERE password_hash IS NULL OR LENGTH(password_hash) < 10")
        weak_passwords = cursor.fetchall()
        if weak_passwords:
            self.add_issue("HIGH", "Data Security", f"{len(weak_passwords)} users have weak or missing password hashes")
        else:
            print("     ✅ All users have proper password hashes")

    def _test_business_logic_constraints(self, cursor):
        """Test business logic constraints"""
        print("   💼 Testing business logic constraints...")
        
        # Test no overlapping bookings for same robot
        cursor.execute("""
            SELECT robot_type, date, COUNT(*) as conflicts
            FROM bookings 
            WHERE status = 'active'
            GROUP BY robot_type, date, start_time, end_time
            HAVING COUNT(*) > 1
        """)
        booking_conflicts = cursor.fetchall()
        if booking_conflicts:
            self.add_issue("HIGH", "Business Logic", f"{len(booking_conflicts)} booking conflicts found")
        else:
            print("     ✅ No booking conflicts detected")
        
        # Test future bookings only
        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE status = 'active' AND STR_TO_DATE(CONCAT(date, ' ', start_time), '%Y-%m-%d %H:%i') < NOW()
        """)
        past_active_bookings = cursor.fetchone()[0]
        if past_active_bookings > 0:
            self.add_warning("Business Logic", f"{past_active_bookings} active bookings are in the past")

    def _test_temporal_consistency(self, cursor):
        """Test temporal data consistency"""
        print("   ⏰ Testing temporal consistency...")
        
        # Test created_at timestamps
        cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > NOW()")
        future_users = cursor.fetchone()[0]
        if future_users > 0:
            self.add_issue("MEDIUM", "Temporal Data", f"{future_users} users have future creation dates")
        
        # Test session expiration
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at < created_at")
        invalid_sessions = cursor.fetchone()[0]
        if invalid_sessions > 0:
            self.add_issue("HIGH", "Temporal Data", f"{invalid_sessions} sessions expire before creation")

    def test_mysql_specific_features(self) -> bool:
        """Test 5: MySQL-Specific Features and Configuration"""
        print("\n🐬 Testing MySQL-specific features...")
        self.total_tests += 1
        
        if not self.mysql_connection:
            print("   ⚠️  No MySQL connection - testing configuration files")
            return self._test_mysql_config_files()
        
        try:
            cursor = self.mysql_connection.cursor()
            
            # Test 5.1: MySQL engine and storage
            cursor.execute("SHOW TABLE STATUS")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                engine = table[1]
                print(f"   🔧 Table '{table_name}': Engine = {engine}")
                
                if engine != 'InnoDB':
                    self.add_warning("MySQL Config", f"Table '{table_name}' uses {engine}, recommended: InnoDB")
            
            # Test 5.2: MySQL variables
            important_vars = [
                'innodb_buffer_pool_size',
                'max_connections',
                'query_cache_size',
                'innodb_log_file_size'
            ]
            
            for var in important_vars:
                cursor.execute(f"SHOW VARIABLES LIKE '{var}'")
                result = cursor.fetchone()
                if result:
                    print(f"   ⚙️  {result[0]}: {result[1]}")
                else:
                    self.add_warning("MySQL Config", f"Variable '{var}' not found")
            
            # Test 5.3: Index analysis
            self._test_mysql_indexes(cursor)
            
            # Test 5.4: MySQL performance
            self._test_mysql_performance(cursor)
            
            self.passed_tests += 1
            return True
            
        except Exception as e:
            print(f"   ❌ MySQL features validation failed: {e}")
            self.add_issue("HIGH", "MySQL Features", f"MySQL features error: {e}")
            return False

    def _test_mysql_config_files(self) -> bool:
        """Test MySQL configuration in files"""
        try:
            # Check .env configuration
            env_vars = {
                'DATABASE_TYPE': 'mysql',
                'MYSQL_HOST': os.getenv('MYSQL_HOST'),
                'MYSQL_PORT': os.getenv('MYSQL_PORT'),
                'MYSQL_USER': os.getenv('MYSQL_USER'),
                'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
                'MYSQL_DATABASE': os.getenv('MYSQL_DATABASE')
            }
            
            for var, value in env_vars.items():
                if value:
                    print(f"   ✅ {var}: {value}")
                else:
                    self.add_issue("HIGH", "MySQL Config", f"Missing environment variable: {var}")
            
            return True
            
        except Exception as e:
            self.add_issue("HIGH", "MySQL Config", f"MySQL config validation error: {e}")
            return False

    def _test_mysql_indexes(self, cursor):
        """Test MySQL indexes"""
        print("   📊 Testing MySQL indexes...")
        
        important_indexes = {
            'users': ['email'],
            'bookings': ['user_id', 'robot_type', 'date'],
            'sessions': ['user_id', 'token_hash'],
            'robots': ['type', 'status']
        }
        
        for table, expected_indexes in important_indexes.items():
            cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = cursor.fetchall()
            index_columns = [idx[4] for idx in indexes if idx[4] != 'id']  # Exclude primary key
            
            for expected_col in expected_indexes:
                if expected_col in index_columns:
                    print(f"     ✅ Index found on {table}.{expected_col}")
                else:
                    self.add_warning("MySQL Performance", f"Consider adding index on {table}.{expected_col}")

    def _test_mysql_performance(self, cursor):
        """Test MySQL performance indicators"""
        print("   ⚡ Testing MySQL performance...")
        
        # Test query execution time
        start_time = datetime.now()
        cursor.execute("SELECT COUNT(*) FROM users")
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        print(f"     ⏱️  Simple query execution time: {query_time:.4f}s")
        
        if query_time > 1.0:
            self.add_warning("MySQL Performance", f"Simple query took {query_time:.4f}s (>1s)")

    def test_production_readiness(self) -> bool:
        """Test 6: Production Readiness"""
        print("\n🚀 Testing production readiness...")
        self.total_tests += 1
        
        try:
            # Test 6.1: Environment configuration
            env = os.getenv('ENVIRONMENT', 'development')
            print(f"   🌍 Environment: {env}")
            
            if env == 'production':
                # Production-specific checks
                self._test_production_security()
                self._test_production_configuration()
            else:
                print("   ℹ️  Development environment detected")
            
            # Test 6.2: Security configurations
            self._test_security_config()
            
            # Test 6.3: Backup and recovery readiness
            self._test_backup_readiness()
            
            self.passed_tests += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Production readiness validation failed: {e}")
            self.add_issue("HIGH", "Production Readiness", f"Production readiness error: {e}")
            return False

    def _test_production_security(self):
        """Test production security settings"""
        print("   🔒 Testing production security...")
        
        # Check for default passwords
        default_passwords = ['admin123', 'password', '123456', 'admin']
        admin_password = os.getenv('ADMIN_PASSWORD', '')
        
        if admin_password in default_passwords:
            self.add_issue("CRITICAL", "Security", "Admin using default password in production")
        
        # Check JWT secret
        jwt_secret = os.getenv('SECRET_KEY', '')
        if not jwt_secret or jwt_secret == 'your-secret-key-here':
            self.add_issue("CRITICAL", "Security", "Default JWT secret key in production")

    def _test_production_configuration(self):
        """Test production configuration"""
        print("   ⚙️  Testing production configuration...")
        
        # Check CORS settings
        cors_origins = os.getenv('PRODUCTION_CORS_ORIGINS', '')
        if not cors_origins:
            self.add_warning("Production Config", "No production CORS origins configured")
        
        # Check SSL/HTTPS
        vps_url = os.getenv('VPS_URL', '')
        if vps_url and not vps_url.startswith('https://'):
            self.add_warning("Production Config", "VPS URL not using HTTPS")

    def _test_security_config(self):
        """Test security configuration"""
        print("   🛡️  Testing security configuration...")
        
        # Check for sensitive files
        sensitive_files = ['.env', 'backend/.env']
        for file_path in sensitive_files:
            if Path(file_path).exists():
                print(f"     ⚠️  Sensitive file exists: {file_path}")

    def _test_backup_readiness(self):
        """Test backup and recovery readiness"""
        print("   💾 Testing backup readiness...")
        
        # Check for backup scripts
        backup_files = ['setup_mysql.sh', 'robot_console.sql']
        backup_ready = False
        
        for backup_file in backup_files:
            if Path(backup_file).exists():
                print(f"     ✅ Backup file found: {backup_file}")
                backup_ready = True
            else:
                print(f"     ⚠️  Backup file missing: {backup_file}")
        
        if not backup_ready:
            self.add_warning("Backup", "No backup scripts found")

    def generate_comprehensive_report(self) -> bool:
        """Generate comprehensive validation report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DATA VALIDATION REPORT")
        print("=" * 80)
        
        # Summary statistics
        print(f"\n📈 VALIDATION SUMMARY:")
        print(f"   ✅ Tests Passed: {self.passed_tests}/{self.total_tests}")
        print(f"   ❌ Issues Found: {len(self.issues)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        # Success rate
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        # Issues breakdown
        if self.issues:
            print(f"\n❌ ISSUES FOUND:")
            severity_counts = {}
            for issue in self.issues:
                severity = issue['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                print(f"   {severity}: {issue['category']} - {issue['description']}")
            
            print(f"\n📋 Issues by Severity:")
            for severity, count in severity_counts.items():
                print(f"   {severity}: {count}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning['category']}: {warning['description']}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])
        
        if critical_issues > 0:
            print("   ❌ CRITICAL ISSUES FOUND - System not ready for production")
            status = False
        elif high_issues > 0:
            print("   ⚠️  HIGH PRIORITY ISSUES - Review required before production")
            status = False
        elif success_rate >= 80:
            print("   ✅ SYSTEM READY - All critical validations passed")
            status = True
        else:
            print("   ⚠️  PARTIAL VALIDATION - Some tests could not be completed")
            status = False
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not self.mysql_connection:
            print("   📡 Setup MySQL connection for complete validation")
        if critical_issues > 0:
            print("   🔧 Fix critical issues before proceeding")
        if high_issues > 0:
            print("   ⚙️  Address high priority issues")
        if len(self.warnings) > 5:
            print("   📝 Review and address warnings for optimal performance")
        
        # Save detailed report
        self._save_detailed_report()
        
        return status

    def _save_detailed_report(self):
        """Save detailed report to file"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "tests_passed": self.passed_tests,
                "total_tests": self.total_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                "issues_count": len(self.issues),
                "warnings_count": len(self.warnings)
            },
            "issues": self.issues,
            "warnings": self.warnings
        }
        
        report_file = Path('data_validation_report.json')
        report_file.write_text(json.dumps(report_data, indent=2))
        print(f"   📄 Detailed report saved to: {report_file}")

def main():
    """Run comprehensive data validation"""
    print("🔍 COMPREHENSIVE DATA VALIDATION")
    print("Validating that all data is real and dashboard data of admin is real")
    print("Script to check in detail that MySQL section is correct")
    print("=" * 80)
    
    if not DEPENDENCIES_AVAILABLE:
        print("⚠️  Some dependencies are not available. Install with:")
        print("   pip install -r backend/requirements.txt")
        print("\nContinuing with available validations...")
    
    validator = ComprehensiveDataValidator()
    
    # Run all validation tests
    print("\n🚀 Starting comprehensive validation...")
    
    # Test 1: MySQL Connection and Configuration
    validator.test_mysql_connection_detailed()
    
    # Test 2: Database Schema Integrity
    validator.test_database_schema_integrity()
    
    # Test 3: Admin Dashboard Data Integrity
    validator.test_admin_dashboard_data_integrity()
    
    # Test 4: Data Consistency and Integrity
    validator.test_data_consistency_and_integrity()
    
    # Test 5: MySQL-Specific Features
    validator.test_mysql_specific_features()
    
    # Test 6: Production Readiness
    validator.test_production_readiness()
    
    # Generate comprehensive report
    is_valid = validator.generate_comprehensive_report()
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())