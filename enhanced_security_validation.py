#!/usr/bin/env python3
"""
Enhanced Security and Privilege Control Validation Script

This script validates the implementation of enhanced security measures:
1. Admin dashboard shows only real data (no demo fallback)
2. Booking system has proper authentication and audit logging
3. Demo and admin accounts maintain proper privileges
4. Real-time data accuracy for admin dashboards
5. Proper robot visibility controls

Addresses all requirements from the problem statement.
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database import DatabaseManager
    from services.booking_service import BookingService
    from auth import AuthManager
    from dotenv import load_dotenv
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Backend dependencies not available: {e}")
    BACKEND_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedSecurityValidator:
    def __init__(self):
        self.issues = []
        self.successes = []
        self.warnings = []
        self.admin_data_filtered = False
        self.booking_audit_logging = False
        self.privilege_validation = False
        
    def add_issue(self, severity: str, description: str):
        """Add validation issue"""
        self.issues.append({
            "severity": severity,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_success(self, description: str):
        """Add validation success"""
        self.successes.append({
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_warning(self, description: str):
        """Add validation warning"""
        self.warnings.append({
            "description": description,
            "timestamp": datetime.now().isoformat()
        })

    def validate_admin_data_filtering(self) -> bool:
        """Test 1: Validate that admin endpoints filter out demo data"""
        print(f"\n🔍 Testing Admin Data Filtering...")
        print("-" * 50)
        
        try:
            # Check main.py for enhanced admin endpoints
            main_py_path = os.path.join(os.path.dirname(__file__), 'backend', 'main.py')
            if not os.path.exists(main_py_path):
                self.add_issue("CRITICAL", "main.py not found - cannot validate admin data filtering")
                return False
                
            with open(main_py_path, 'r') as f:
                content = f.read()
                
            # Check for admin data filtering implementation
            if 'real_bookings = [b for b in bookings if not any(demo_indicator' in content:
                self.add_success("Admin bookings endpoint filters demo data")
                print("   ✅ Admin bookings endpoint has demo data filtering")
            else:
                self.add_issue("HIGH", "Admin bookings endpoint missing demo data filtering")
                
            if 'real_users = [u for u in users if not any(demo_indicator' in content:
                self.add_success("Admin users endpoint filters demo data")
                print("   ✅ Admin users endpoint has demo data filtering")
            else:
                self.add_issue("HIGH", "Admin users endpoint missing demo data filtering")
                
            # Check that demo fallbacks are removed
            if 'returning demo data' not in content.replace('# Return demo data when database is unavailable', ''):
                self.add_success("Demo data fallbacks removed from admin endpoints")
                print("   ✅ Demo data fallbacks removed")
            else:
                self.add_warning("Some demo data fallbacks may still exist")
                
            # Check for proper error handling instead of demo fallbacks
            if 'Database service unavailable' in content:
                self.add_success("Proper error handling for unavailable database")
                print("   ✅ Proper error handling implemented")
            else:
                self.add_issue("MEDIUM", "Missing proper error handling for database unavailability")
                
            return len([i for i in self.issues if i['severity'] in ['CRITICAL', 'HIGH']]) == 0
            
        except Exception as e:
            self.add_issue("CRITICAL", f"Failed to validate admin data filtering: {e}")
            return False

    def validate_booking_audit_logging(self) -> bool:
        """Test 2: Validate enhanced booking audit logging"""
        print(f"\n🔍 Testing Booking Audit Logging...")
        print("-" * 50)
        
        try:
            # Check booking_service.py for enhanced logging
            booking_service_path = os.path.join(os.path.dirname(__file__), 'backend', 'services', 'booking_service.py')
            if not os.path.exists(booking_service_path):
                self.add_issue("CRITICAL", "booking_service.py not found")
                return False
                
            with open(booking_service_path, 'r') as f:
                content = f.read()
                
            # Check for comprehensive audit logging
            audit_patterns = [
                '🔒 BOOKING ATTEMPT',
                '✅ BOOKING CREATED',
                '❌ BOOKING REJECTED',
                '🔄 STATUS UPDATE',
                '🔧 ADMIN ACTION'
            ]
            
            for pattern in audit_patterns:
                if pattern in content:
                    self.add_success(f"Audit logging found: {pattern}")
                    print(f"   ✅ {pattern} logging implemented")
                else:
                    self.add_issue("MEDIUM", f"Missing audit logging: {pattern}")
                    
            # Check for enhanced authentication validation
            if 'Invalid user authentication' in content:
                self.add_success("Enhanced user authentication validation")
                print("   ✅ Enhanced authentication validation")
            else:
                self.add_issue("HIGH", "Missing enhanced authentication validation")
                
            # Check for comprehensive conflict detection
            if 'BOOKING CONFLICT' in content:
                self.add_success("Enhanced booking conflict detection")
                print("   ✅ Enhanced conflict detection and logging")
            else:
                self.add_issue("MEDIUM", "Missing enhanced conflict detection logging")
                
            return len([i for i in self.issues if i['severity'] in ['CRITICAL', 'HIGH']]) == 0
            
        except Exception as e:
            self.add_issue("CRITICAL", f"Failed to validate booking audit logging: {e}")
            return False

    def validate_privilege_controls(self) -> bool:
        """Test 3: Validate enhanced privilege controls"""
        print(f"\n🔍 Testing Privilege Controls...")
        print("-" * 50)
        
        try:
            # Check auth.py for enhanced privilege validation
            auth_py_path = os.path.join(os.path.dirname(__file__), 'backend', 'auth.py')
            if not os.path.exists(auth_py_path):
                self.add_issue("CRITICAL", "auth.py not found")
                return False
                
            with open(auth_py_path, 'r') as f:
                content = f.read()
                
            # Check for enhanced admin privilege validation
            if '🔐 ADMIN ACCESS ATTEMPT' in content:
                self.add_success("Enhanced admin access logging")
                print("   ✅ Admin access attempts are logged")
            else:
                self.add_issue("HIGH", "Missing admin access attempt logging")
                
            if '🎯 DEMO ADMIN ACCESS' in content:
                self.add_success("Demo admin access tracking")
                print("   ✅ Demo admin access is tracked separately")
            else:
                self.add_issue("MEDIUM", "Missing demo admin access tracking")
                
            if 'Only administrators can access this resource' in content:
                self.add_success("Enhanced admin access error messages")
                print("   ✅ Clear admin access error messages")
            else:
                self.add_issue("MEDIUM", "Missing enhanced admin access error messages")
                
            return len([i for i in self.issues if i['severity'] in ['CRITICAL', 'HIGH']]) == 0
            
        except Exception as e:
            self.add_issue("CRITICAL", f"Failed to validate privilege controls: {e}")
            return False

    def validate_robot_visibility_controls(self) -> bool:
        """Test 4: Validate robot visibility controls"""
        print(f"\n🔍 Testing Robot Visibility Controls...")
        print("-" * 50)
        
        try:
            # Check main.py for robot visibility controls
            main_py_path = os.path.join(os.path.dirname(__file__), 'backend', 'main.py')
            with open(main_py_path, 'r') as f:
                content = f.read()
                
            # Check for admin-managed robot filtering
            if 'admin_managed_robots = [robot for robot in robots if robot.get(\'status\') in [\'active\', \'inactive\']]' in content:
                self.add_success("Robot visibility restricted to admin-managed robots")
                print("   ✅ Only admin-managed robots are visible")
            else:
                self.add_issue("HIGH", "Missing robot visibility controls")
                
            # Check that robot demo data fallbacks are removed
            if 'Demo TurtleBot' not in content or 'returning demo data' not in content:
                self.add_success("Robot demo data fallbacks removed")
                print("   ✅ Robot demo data fallbacks removed")
            else:
                self.add_warning("Robot demo data fallbacks may still exist")
                
            return len([i for i in self.issues if i['severity'] in ['CRITICAL', 'HIGH']]) == 0
            
        except Exception as e:
            self.add_issue("CRITICAL", f"Failed to validate robot visibility controls: {e}")
            return False

    def validate_demo_account_functionality(self) -> bool:
        """Test 5: Validate demo account functionality is preserved"""
        print(f"\n🔍 Testing Demo Account Functionality...")
        print("-" * 50)
        
        try:
            # Check frontend BookingPage.jsx for demo user features
            booking_page_path = os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'components', 'BookingPage.jsx')
            if os.path.exists(booking_page_path):
                with open(booking_page_path, 'r') as f:
                    content = f.read()
                    
                if 'user?.isDemoUser || user?.isDemoAdmin' in content:
                    self.add_success("Demo user detection preserved in frontend")
                    print("   ✅ Demo user detection maintained")
                else:
                    self.add_issue("HIGH", "Demo user detection missing in frontend")
                    
                if 'Demo Mode - Unrestricted Access' in content:
                    self.add_success("Demo mode unrestricted access maintained")
                    print("   ✅ Demo mode unrestricted access preserved")
                else:
                    self.add_issue("MEDIUM", "Demo mode access may be restricted")
                    
            # Check demo admin file
            demo_admin_path = os.path.join(os.path.dirname(__file__), 'projects', '-2', 'demo_admin_welcome.py')
            if os.path.exists(demo_admin_path):
                self.add_success("Demo admin workspace file exists")
                print("   ✅ Demo admin workspace preserved")
            else:
                self.add_warning("Demo admin workspace file not found")
                
            return True
            
        except Exception as e:
            self.add_issue("MEDIUM", f"Failed to validate demo account functionality: {e}")
            return False

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        total_tests = 5
        passed_tests = sum([
            self.validate_admin_data_filtering(),
            self.validate_booking_audit_logging(), 
            self.validate_privilege_controls(),
            self.validate_robot_visibility_controls(),
            self.validate_demo_account_functionality()
        ])
        
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])
        medium_issues = len([i for i in self.issues if i['severity'] == 'MEDIUM'])
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": total_tests,
            "tests_passed": passed_tests,
            "pass_rate": (passed_tests / total_tests) * 100,
            "issues": {
                "critical": critical_issues,
                "high": high_issues,
                "medium": medium_issues,
                "total": len(self.issues)
            },
            "successes": len(self.successes),
            "warnings": len(self.warnings),
            "detailed_issues": self.issues,
            "detailed_successes": self.successes,
            "detailed_warnings": self.warnings
        }
        
        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print validation summary"""
        print(f"\n{'='*80}")
        print(f"🔒 ENHANCED SECURITY VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        print(f"📊 Test Results: {report['tests_passed']}/{report['tests_run']} passed ({report['pass_rate']:.1f}%)")
        print(f"✅ Successes: {report['successes']}")
        print(f"⚠️  Warnings: {report['warnings']}")
        print(f"❌ Issues: {report['issues']['total']} (Critical: {report['issues']['critical']}, High: {report['issues']['high']}, Medium: {report['issues']['medium']})")
        
        if report['issues']['critical'] > 0:
            print(f"\n🚨 CRITICAL ISSUES - Immediate attention required:")
            for issue in [i for i in self.issues if i['severity'] == 'CRITICAL']:
                print(f"   🔴 {issue['description']}")
                
        elif report['issues']['high'] > 0:
            print(f"\n⚠️  HIGH PRIORITY ISSUES - Should be addressed:")
            for issue in [i for i in self.issues if i['severity'] == 'HIGH']:
                print(f"   🟠 {issue['description']}")
                
        if report['pass_rate'] >= 80:
            print(f"\n✅ VALIDATION PASSED - Enhanced security measures are properly implemented")
            status = True
        else:
            print(f"\n❌ VALIDATION FAILED - Enhanced security measures need improvement")
            status = False
            
        # Save detailed report
        report_file = Path("enhanced_security_validation_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📋 Detailed report saved to: {report_file}")
        
        return status

def main():
    """Run enhanced security validation"""
    print("🔒 ENHANCED SECURITY AND PRIVILEGE CONTROL VALIDATION")
    print("Validating implementation of enhanced security measures per problem statement")
    print("=" * 80)
    
    validator = EnhancedSecurityValidator()
    
    # Run all validation tests
    report = validator.generate_validation_report()
    
    # Print results and save report
    overall_success = validator.print_summary(report)
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())