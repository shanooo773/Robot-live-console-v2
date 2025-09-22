#!/usr/bin/env python3
"""
Admin Dashboard Data Integrity Validation Script
Validates that admin dashboard data is real and all admin functionality works correctly

Features:
- Admin user data validation
- Admin dashboard endpoint verification
- Admin-accessible data validation
- Admin statistics accuracy
- Admin functionality testing
- Real data vs mock data validation
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database import DatabaseManager
    from dotenv import load_dotenv
    import pymysql
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Backend dependencies not available: {e}")
    BACKEND_AVAILABLE = False

load_dotenv()

class AdminDashboardValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.admin_data = {}
        self.dashboard_stats = {}
        self.connection = None
        
    def add_issue(self, severity: str, description: str):
        """Add validation issue"""
        self.issues.append({
            "severity": severity,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_warning(self, description: str):
        """Add validation warning"""
        self.warnings.append({
            "description": description,
            "timestamp": datetime.now().isoformat()
        })

    def validate_admin_endpoints(self) -> bool:
        """Validate admin dashboard endpoints exist and are properly secured"""
        print("🔍 Validating Admin Dashboard Endpoints...")
        print("-" * 50)
        
        # Check main.py for admin endpoints
        main_file = Path('backend/main.py')
        if not main_file.exists():
            self.add_issue("CRITICAL", "backend/main.py not found - cannot validate admin endpoints")
            return False
        
        content = main_file.read_text()
        
        # Required admin endpoints and features
        admin_requirements = {
            # Authentication and authorization
            'require_admin': {
                'patterns': ['@require_admin', 'require_admin\\(', 'def require_admin'],
                'description': 'Admin authentication decorator'
            },
            
            # Robot management endpoints
            '/admin/robots': {
                'patterns': ['/admin/robots', 'admin_robots', r'def.*admin.*robots'],
                'description': 'Robot management endpoint'
            },
            
            # User management
            '/admin/users': {
                'patterns': ['/admin/users', 'admin_users', r'def.*admin.*users'],
                'description': 'User management endpoint'
            },
            
            # Booking management
            '/bookings/all': {
                'patterns': ['/bookings/all', r'bookings.*all', r'def.*bookings.*all'],
                'description': 'All bookings view endpoint'
            },
            
            # System statistics
            '/admin/stats': {
                'patterns': ['/admin/stats', 'admin_stats', r'def.*admin.*stats'],
                'description': 'Admin statistics endpoint'
            },
            
            # Container management
            'theia_containers': {
                'patterns': [r'theia.*containers', r'list.*containers', r'container.*management'],
                'description': 'Theia container management'
            }
        }
        
        found_endpoints = []
        missing_endpoints = []
        
        for endpoint, config in admin_requirements.items():
            patterns = config['patterns']
            description = config['description']
            
            found = False
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
            
            if found:
                print(f"   ✅ {description}: Found")
                found_endpoints.append(endpoint)
            else:
                print(f"   ❌ {description}: Missing")
                missing_endpoints.append(endpoint)
                self.add_issue("HIGH", f"Missing admin endpoint: {endpoint} ({description})")
        
        # Check for proper authentication on admin endpoints
        self._validate_admin_authentication(content)
        
        # Check for proper error handling
        self._validate_admin_error_handling(content)
        
        return len(missing_endpoints) == 0

    def _validate_admin_authentication(self, content: str):
        """Validate admin authentication implementation"""
        print("\n🔐 Admin Authentication Validation:")
        
        # Check for JWT authentication
        jwt_patterns = ['jwt', 'JWT', 'token', 'authenticate']
        jwt_found = any(pattern in content for pattern in jwt_patterns)
        
        if jwt_found:
            print("   ✅ JWT authentication references found")
        else:
            self.add_issue("HIGH", "No JWT authentication implementation found")
        
        # Check for role-based access control
        rbac_patterns = ['role', 'admin', 'require_admin', 'permission']
        rbac_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in rbac_patterns)
        
        if rbac_found:
            print("   ✅ Role-based access control references found")
        else:
            self.add_issue("HIGH", "No role-based access control implementation found")
        
        # Check auth.py file
        auth_file = Path('backend/auth.py')
        if auth_file.exists():
            print("   ✅ Auth module found")
            self._validate_auth_module(auth_file)
        else:
            self.add_issue("HIGH", "Auth module (auth.py) not found")

    def _validate_auth_module(self, auth_file: Path):
        """Validate authentication module"""
        content = auth_file.read_text()
        
        auth_features = {
            'get_current_user': 'User authentication function',
            'require_admin': 'Admin authorization function',
            'create_token': 'Token creation function',
            'verify_token': 'Token verification function'
        }
        
        for feature, description in auth_features.items():
            if feature in content:
                print(f"     ✅ {description}")
            else:
                self.add_warning(f"Auth feature missing: {description}")

    def _validate_admin_error_handling(self, content: str):
        """Validate admin error handling"""
        print("\n⚠️  Admin Error Handling:")
        
        error_patterns = {
            'HTTPException': 'HTTP error responses',
            'try.*except': 'Exception handling blocks',
            'status_code': 'HTTP status codes',
            'error.*message': 'Error messages'
        }
        
        for pattern, description in error_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                print(f"   ✅ {description} found")
            else:
                self.add_warning(f"Error handling missing: {description}")

    def validate_admin_data_integrity(self) -> bool:
        """Validate admin user data integrity"""
        print("\n👨‍💼 Validating Admin User Data Integrity...")
        print("-" * 50)
        
        # Try to connect to database
        if BACKEND_AVAILABLE:
            try:
                db_manager = DatabaseManager()
                self.connection = db_manager.get_connection()
                return self._validate_admin_data_live()
            except Exception as e:
                print(f"   ⚠️  Cannot connect to database: {e}")
                return self._validate_admin_data_config()
        else:
            return self._validate_admin_data_config()

    def _validate_admin_data_live(self) -> bool:
        """Validate admin data with live database connection"""
        cursor = self.connection.cursor()
        
        # Check for admin users
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        print(f"   📊 Admin users in database: {admin_count}")
        
        if admin_count == 0:
            self.add_issue("CRITICAL", "No admin users found in database")
            return False
        
        # Get admin user details
        cursor.execute("""
            SELECT id, name, email, role, created_at, 
                   CASE WHEN password_hash IS NULL OR password_hash = '' THEN 'EMPTY' 
                        WHEN LENGTH(password_hash) < 10 THEN 'WEAK' 
                        ELSE 'STRONG' END as password_strength
            FROM users WHERE role = 'admin'
        """)
        
        admin_users = cursor.fetchall()
        
        for admin in admin_users:
            user_id, name, email, role, created_at, password_strength = admin
            
            print(f"\n   🔍 Admin User Analysis:")
            print(f"     👤 ID: {user_id}")
            print(f"     📝 Name: {name}")
            print(f"     📧 Email: {email}")
            print(f"     🛡️  Role: {role}")
            print(f"     📅 Created: {created_at}")
            print(f"     🔐 Password: {password_strength}")
            
            # Validate admin data quality
            issues = []
            
            if not name or len(name.strip()) < 2:
                issues.append("Invalid or missing name")
            
            if not email or '@' not in email or '.' not in email.split('@')[1]:
                issues.append("Invalid email format")
            
            if password_strength in ['EMPTY', 'WEAK']:
                issues.append(f"Password strength: {password_strength}")
            
            if role != 'admin':
                issues.append(f"Incorrect role: {role}")
            
            # Check for default/test data
            if self._is_demo_data(name, email):
                self.add_warning(f"Admin user {user_id} appears to be demo/test data")
            
            if issues:
                print(f"     ❌ Issues: {', '.join(issues)}")
                for issue in issues:
                    self.add_issue("HIGH", f"Admin user {user_id}: {issue}")
            else:
                print(f"     ✅ Admin data valid")
        
        # Validate admin access patterns
        self._validate_admin_access_patterns(cursor)
        
        # Validate admin statistics
        self._validate_admin_statistics(cursor)
        
        return len([i for i in self.issues if i['severity'] == 'CRITICAL']) == 0

    def _validate_admin_data_config(self) -> bool:
        """Validate admin data from configuration files"""
        print("   ⚠️  Using configuration-based validation")
        
        # Check environment variables for admin setup
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        demo_admin_email = os.getenv('DEMO_ADMIN_EMAIL')
        demo_admin_password = os.getenv('DEMO_ADMIN_PASSWORD')
        
        print(f"\n   📧 Admin Email (env): {admin_email}")
        print(f"   🔐 Admin Password (env): {'***' if admin_password else 'Not Set'}")
        print(f"   📧 Demo Admin Email (env): {demo_admin_email}")
        print(f"   🔐 Demo Admin Password (env): {'***' if demo_admin_password else 'Not Set'}")
        
        # Validate admin configuration
        if not admin_email:
            self.add_issue("HIGH", "ADMIN_EMAIL not configured")
        elif not self._is_valid_email(admin_email):
            self.add_issue("HIGH", f"Invalid admin email format: {admin_email}")
        
        if not admin_password:
            self.add_issue("HIGH", "ADMIN_PASSWORD not configured")
        elif self._is_weak_password(admin_password):
            self.add_issue("HIGH", "Admin password is weak or default")
        
        # Check for demo user setup script
        demo_script = Path('setup_demo_users.py')
        if demo_script.exists():
            print(f"   ✅ Demo user setup script found: {demo_script}")
            self._validate_demo_script(demo_script)
        else:
            self.add_warning("Demo user setup script not found")
        
        return True

    def _is_demo_data(self, name: str, email: str) -> bool:
        """Check if user data appears to be demo/test data"""
        demo_indicators = [
            'demo', 'test', 'admin', 'example', 'sample',
            'user', 'default', 'temp', 'fake'
        ]
        
        name_lower = name.lower() if name else ''
        email_lower = email.lower() if email else ''
        
        return any(indicator in name_lower or indicator in email_lower 
                  for indicator in demo_indicators)

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def _is_weak_password(self, password: str) -> bool:
        """Check if password is weak or default"""
        weak_passwords = [
            'admin', 'admin123', 'password', 'password123',
            '123456', 'qwerty', 'letmein', 'welcome'
        ]
        
        return (password.lower() in weak_passwords or 
                len(password) < 8 or 
                password.isdigit() or 
                password.isalpha())

    def _validate_demo_script(self, script_path: Path):
        """Validate demo user setup script"""
        content = script_path.read_text()
        
        if 'admin' in content.lower():
            print("     ✅ Demo script includes admin user setup")
        else:
            self.add_warning("Demo script may not include admin user setup")

    def _validate_admin_access_patterns(self, cursor):
        """Validate admin access patterns"""
        print(f"\n   🔍 Admin Access Pattern Analysis:")
        
        # Check admin sessions
        cursor.execute("""
            SELECT COUNT(*) as session_count
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE u.role = 'admin'
        """)
        
        admin_sessions = cursor.fetchone()[0]
        print(f"     🔄 Admin sessions: {admin_sessions}")
        
        if admin_sessions == 0:
            self.add_warning("No admin sessions found - admins may not be logging in")
        
        # Check admin-created data
        admin_created_data = {}
        
        # Check for admin-created announcements
        cursor.execute("SELECT COUNT(*) FROM announcements")
        announcement_count = cursor.fetchone()[0]
        admin_created_data['announcements'] = announcement_count
        
        # Check for robots (admin-managed)
        cursor.execute("SELECT COUNT(*) FROM robots")
        robot_count = cursor.fetchone()[0]
        admin_created_data['robots'] = robot_count
        
        print(f"     📊 Admin-managed data:")
        for data_type, count in admin_created_data.items():
            print(f"       {data_type}: {count}")
            if count == 0:
                self.add_warning(f"No {data_type} found - admin may not be managing data")

    def _validate_admin_statistics(self, cursor):
        """Validate admin dashboard statistics"""
        print(f"\n   📈 Admin Statistics Validation:")
        
        # Gather key statistics that would appear on admin dashboard
        stats = {}
        
        try:
            # User statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN role = 'admin' THEN 1 END) as admin_users,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as regular_users
                FROM users
            """)
            user_stats = cursor.fetchone()
            stats['users'] = {
                'total': user_stats[0],
                'admin': user_stats[1],
                'regular': user_stats[2]
            }
            
            # Booking statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_bookings,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_bookings,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_bookings
                FROM bookings
            """)
            booking_stats = cursor.fetchone()
            stats['bookings'] = {
                'total': booking_stats[0],
                'active': booking_stats[1],
                'completed': booking_stats[2]
            }
            
            # Robot statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_robots,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_robots,
                    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_robots
                FROM robots
            """)
            robot_stats = cursor.fetchone()
            stats['robots'] = {
                'total': robot_stats[0],
                'active': robot_stats[1],
                'inactive': robot_stats[2]
            }
            
            # Display statistics
            for category, data in stats.items():
                print(f"     📊 {category.title()}:")
                for key, value in data.items():
                    print(f"       {key}: {value}")
            
            # Validate statistics consistency
            self._validate_statistics_consistency(stats)
            
            # Store for report
            self.dashboard_stats = stats
            
        except Exception as e:
            print(f"     ❌ Error gathering statistics: {e}")
            self.add_issue("MEDIUM", f"Cannot gather admin statistics: {e}")

    def _validate_statistics_consistency(self, stats: Dict):
        """Validate statistics for consistency"""
        # Check user statistics
        user_total = stats['users']['total']
        user_sum = stats['users']['admin'] + stats['users']['regular']
        
        if user_total != user_sum:
            self.add_issue("MEDIUM", f"User statistics inconsistent: total={user_total}, sum={user_sum}")
        
        # Check for empty system
        if all(category['total'] == 0 for category in stats.values()):
            self.add_issue("HIGH", "All statistics are zero - system appears empty")
        
        # Check for reasonable data distribution
        if stats['users']['admin'] > stats['users']['regular'] and stats['users']['total'] > 2:
            self.add_warning("More admin users than regular users - unusual for production")

    def validate_admin_ui_components(self) -> bool:
        """Validate admin UI components and frontend integration"""
        print("\n🖥️  Validating Admin UI Components...")
        print("-" * 50)
        
        # Check frontend admin components
        frontend_dir = Path('frontend')
        if not frontend_dir.exists():
            self.add_issue("HIGH", "Frontend directory not found")
            return False
        
        # Look for admin-specific components
        admin_components = []
        ui_issues = []
        
        # Search for admin components in frontend
        for file_path in frontend_dir.rglob('*.js'):
            content = file_path.read_text()
            
            # Check for admin-related code
            admin_patterns = [
                'admin', 'Admin', 'dashboard', 'Dashboard',
                'require.*admin', 'isAdmin', 'adminOnly'
            ]
            
            for pattern in admin_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    admin_components.append(str(file_path))
                    break
        
        print(f"   📁 Admin-related frontend files: {len(admin_components)}")
        for component in admin_components[:5]:  # Show first 5
            print(f"     - {component}")
        
        if admin_components:
            print("   ✅ Admin UI components found")
        else:
            self.add_issue("HIGH", "No admin UI components found in frontend")
        
        # Check API integration
        self._validate_admin_api_integration()
        
        return len(ui_issues) == 0

    def _validate_admin_api_integration(self):
        """Validate admin API integration"""
        print("\n   🔌 Admin API Integration:")
        
        # Look for API calls to admin endpoints
        api_files = list(Path('frontend').rglob('*api*')) + list(Path('frontend').rglob('*service*'))
        
        admin_api_calls = []
        
        for api_file in api_files:
            if api_file.is_file() and api_file.suffix in ['.js', '.ts']:
                content = api_file.read_text()
                
                # Look for admin API calls
                admin_endpoints = [
                    '/admin/', '/admin/robots', '/admin/users', 
                    '/admin/stats', '/bookings/all'
                ]
                
                for endpoint in admin_endpoints:
                    if endpoint in content:
                        admin_api_calls.append(f"{api_file.name}: {endpoint}")
        
        if admin_api_calls:
            print("     ✅ Admin API calls found:")
            for call in admin_api_calls:
                print(f"       - {call}")
        else:
            self.add_warning("No admin API calls found in frontend")

    def generate_admin_report(self) -> bool:
        """Generate comprehensive admin dashboard validation report"""
        print("\n" + "=" * 80)
        print("👨‍💼 ADMIN DASHBOARD DATA INTEGRITY REPORT")
        print("=" * 80)
        
        # Summary
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])
        medium_issues = len([i for i in self.issues if i['severity'] == 'MEDIUM'])
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   ❌ Critical Issues: {critical_issues}")
        print(f"   ⚠️  High Priority Issues: {high_issues}")
        print(f"   📋 Medium Issues: {medium_issues}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        # Issues breakdown
        if self.issues:
            print(f"\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"   {issue['severity']}: {issue['description']}")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning['description']}")
        
        # Dashboard statistics
        if self.dashboard_stats:
            print(f"\n📈 DASHBOARD STATISTICS:")
            for category, stats in self.dashboard_stats.items():
                print(f"   📊 {category.title()}: {stats}")
        
        # Overall assessment
        print(f"\n🎯 ADMIN DASHBOARD ASSESSMENT:")
        if critical_issues > 0:
            print("   ❌ CRITICAL ISSUES - Admin dashboard not functional")
            status = False
        elif high_issues > 0:
            print("   ⚠️  HIGH PRIORITY ISSUES - Admin functionality limited")
            status = False
        elif medium_issues > 2:
            print("   ⚠️  MULTIPLE MEDIUM ISSUES - Review recommended")
            status = False
        else:
            print("   ✅ ADMIN DASHBOARD FUNCTIONAL - Data integrity validated")
            status = True
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if critical_issues > 0:
            print("   🔧 Fix critical issues immediately")
        if high_issues > 0:
            print("   ⚙️  Address high priority issues before production")
        if len(self.warnings) > 0:
            print("   📝 Review warnings for optimization opportunities")
        
        # Save report
        self._save_admin_report()
        
        return status

    def _save_admin_report(self):
        """Save admin dashboard report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "admin_validation": {
                "issues": self.issues,
                "warnings": self.warnings,
                "dashboard_stats": self.dashboard_stats,
                "admin_data": self.admin_data
            }
        }
        
        report_file = Path('admin_dashboard_validation_report.json')
        report_file.write_text(json.dumps(report_data, indent=2))
        print(f"   📄 Admin report saved to: {report_file}")

def main():
    """Run admin dashboard validation"""
    print("👨‍💼 ADMIN DASHBOARD DATA INTEGRITY VALIDATION")
    print("Validating that admin dashboard data is real and functional")
    print("=" * 80)
    
    validator = AdminDashboardValidator()
    
    # Run validation tests
    endpoint_valid = validator.validate_admin_endpoints()
    data_valid = validator.validate_admin_data_integrity()
    ui_valid = validator.validate_admin_ui_components()
    
    # Generate comprehensive report
    overall_valid = validator.generate_admin_report()
    
    return 0 if overall_valid else 1

if __name__ == "__main__":
    sys.exit(main())