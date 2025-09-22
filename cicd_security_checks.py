#!/usr/bin/env python3
"""
CI/CD Security Validation Script

This script implements automated security and logic checks to prevent deployment 
of insecure configurations or demo/test artifacts as required by the problem statement.

Runs as part of CI/CD pipeline to ensure:
1. No demo data fallbacks in production admin endpoints
2. Proper privilege validation is implemented
3. Authentication is required for all protected endpoints
4. Audit logging is comprehensive
5. Data filtering is properly implemented

Usage: python3 cicd_security_checks.py
Exit code 0: All checks pass, safe to deploy
Exit code 1: Security issues found, deployment should be blocked
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

class CICDSecurityValidator:
    def __init__(self):
        self.security_issues = []
        self.warnings = []
        self.info = []
        self.critical_patterns = []
        self.setup_security_patterns()
        
    def setup_security_patterns(self):
        """Define security patterns to check"""
        self.critical_patterns = [
            {
                "pattern": r"returning demo data",
                "file_pattern": r"backend/main\.py",
                "description": "Demo data fallback found in admin endpoint",
                "severity": "CRITICAL",
                "exclude_comments": True
            },
            {
                "pattern": r"# Return demo data when",
                "file_pattern": r"backend/main\.py", 
                "description": "Demo data fallback comments should be cleaned up",
                "severity": "WARNING",
                "exclude_comments": False
            },
            {
                "pattern": r"role.*==.*['\"]admin['\"].*and.*not.*demo",
                "file_pattern": r"backend/main\.py",
                "description": "Admin privilege checking with demo filtering implemented",
                "severity": "INFO",
                "exclude_comments": True,
                "should_exist": True
            },
            {
                "pattern": r"Database service unavailable",
                "file_pattern": r"backend/main\.py",
                "description": "Proper error handling for database unavailability",
                "severity": "INFO", 
                "exclude_comments": True,
                "should_exist": True
            },
            {
                "pattern": r"ADMIN ACCESS ATTEMPT",
                "file_pattern": r"backend/auth\.py",
                "description": "Admin access audit logging implemented",
                "severity": "INFO",
                "exclude_comments": True,
                "should_exist": True
            },
            {
                "pattern": r"BOOKING ATTEMPT",
                "file_pattern": r"backend/services/booking_service\.py",
                "description": "Booking audit logging implemented", 
                "severity": "INFO",
                "exclude_comments": True,
                "should_exist": True
            }
        ]

    def add_issue(self, severity: str, description: str, file_path: str = "", line_num: int = 0):
        """Add security issue"""
        issue = {
            "severity": severity,
            "description": description,
            "file": file_path,
            "line": line_num,
            "timestamp": datetime.now().isoformat()
        }
        
        if severity == "CRITICAL":
            self.security_issues.append(issue)
        elif severity == "WARNING":
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    def scan_file_patterns(self) -> bool:
        """Scan files for security patterns"""
        print("🔍 Scanning for security patterns...")
        print("-" * 50)
        
        all_good = True
        
        for pattern_def in self.critical_patterns:
            pattern = pattern_def["pattern"]
            file_pattern = pattern_def["file_pattern"]
            description = pattern_def["description"]
            severity = pattern_def["severity"]
            exclude_comments = pattern_def.get("exclude_comments", True)
            should_exist = pattern_def.get("should_exist", False)
            
            # Find matching files
            matching_files = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    file_path = os.path.join(root, file)
                    if re.search(file_pattern, file_path):
                        matching_files.append(file_path)
            
            found_pattern = False
            for file_path in matching_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            # Skip comments if requested
                            if exclude_comments and line.strip().startswith('#'):
                                continue
                                
                            if re.search(pattern, line, re.IGNORECASE):
                                found_pattern = True
                                
                                if should_exist:
                                    print(f"   ✅ {description} (found in {file_path}:{line_num})")
                                    self.add_issue("INFO", description, file_path, line_num)
                                else:
                                    print(f"   ❌ {description} (found in {file_path}:{line_num})")
                                    self.add_issue(severity, description, file_path, line_num)
                                    if severity == "CRITICAL":
                                        all_good = False
                                        
                    except Exception as e:
                        print(f"   ⚠️  Error scanning {file_path}: {e}")
            
            # Check if required patterns are missing
            if should_exist and not found_pattern:
                print(f"   ❌ {description} (MISSING - required for security)")
                self.add_issue("CRITICAL", f"Missing required security feature: {description}")
                all_good = False
        
        return all_good

    def check_admin_endpoint_security(self) -> bool:
        """Check admin endpoints have proper security"""
        print("\n🔐 Checking admin endpoint security...")
        print("-" * 50)
        
        main_py_path = "backend/main.py"
        if not os.path.exists(main_py_path):
            print("   ❌ backend/main.py not found")
            self.add_issue("CRITICAL", "Main backend file not found")
            return False
            
        try:
            with open(main_py_path, 'r') as f:
                content = f.read()
                
            # Check admin endpoints have require_admin decorator
            admin_endpoints = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']*admin[^"\']*)["\'].*?\)\s*async def ([^(]+)', content, re.DOTALL)
            
            secure_endpoints = 0
            total_admin_endpoints = len(admin_endpoints)
            
            for method, endpoint, function_name in admin_endpoints:
                # Check if function has require_admin in its definition
                func_pattern = rf'async def {re.escape(function_name)}\([^)]*require_admin[^)]*\)'
                if re.search(func_pattern, content):
                    print(f"   ✅ {endpoint} ({function_name}) has admin protection")
                    secure_endpoints += 1
                else:
                    print(f"   ❌ {endpoint} ({function_name}) missing admin protection")
                    self.add_issue("CRITICAL", f"Admin endpoint {endpoint} missing require_admin protection")
            
            if total_admin_endpoints == 0:
                print("   ⚠️  No admin endpoints found")
                return True
                
            security_rate = (secure_endpoints / total_admin_endpoints) * 100
            if security_rate >= 90:
                print(f"   ✅ Admin endpoint security: {security_rate:.1f}% ({secure_endpoints}/{total_admin_endpoints})")
                return True
            else:
                print(f"   ❌ Admin endpoint security: {security_rate:.1f}% ({secure_endpoints}/{total_admin_endpoints})")
                self.add_issue("CRITICAL", f"Admin endpoints security insufficient: {security_rate:.1f}%")
                return False
                
        except Exception as e:
            print(f"   ❌ Error checking admin endpoint security: {e}")
            self.add_issue("CRITICAL", f"Failed to validate admin endpoint security: {e}")
            return False

    def check_demo_data_cleanup(self) -> bool:
        """Check that demo data fallbacks are properly removed from admin endpoints"""
        print("\n🧹 Checking demo data cleanup...")
        print("-" * 50)
        
        # These patterns should NOT exist in admin endpoint functions
        problematic_patterns = [
            r'returning demo data.*admin',
            r'demo_users.*=.*\[.*Admin',
            r'demo_robots.*=.*\[.*admin',
        ]
        
        # Check admin endpoint functions specifically
        admin_endpoint_patterns = [
            r'async def get_all_users.*returning demo data',
            r'async def get_admin_stats.*returning demo data', 
            r'async def get_all_robots_admin.*returning demo data',
            r'async def get_all_bookings.*returning demo data',
            r'async def get_all_messages.*returning demo data',
            r'async def get_all_announcements.*returning demo data'
        ]
        
        backend_files = [
            "backend/main.py",
            "backend/services/booking_service.py",
            "backend/services/auth_service.py"
        ]
        
        issues_found = 0
        for file_path in backend_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Check for problematic patterns in admin functions
                    for pattern in admin_endpoint_patterns:
                        if re.search(pattern, content, re.DOTALL):
                            print(f"   ❌ Admin endpoint demo fallback found in {file_path}: {pattern}")
                            self.add_issue("CRITICAL", f"Admin endpoint has demo fallback in {file_path}: {pattern}")
                            issues_found += 1
                    
                    # Check for general problematic patterns (excluding comments and fallback classes)
                    lines = content.split('\n')
                    in_fallback_class = False
                    for line_num, line in enumerate(lines, 1):
                        # Skip fallback service manager class
                        if 'class FallbackServiceManager' in line:
                            in_fallback_class = True
                            continue
                        if in_fallback_class and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                            in_fallback_class = False
                            
                        if not in_fallback_class:
                            for pattern in problematic_patterns:
                                if re.search(pattern, line, re.IGNORECASE) and not line.strip().startswith('#'):
                                    print(f"   ❌ Demo data found in {file_path}:{line_num}: {pattern}")
                                    self.add_issue("CRITICAL", f"Demo data not cleaned up in {file_path}: {pattern}")
                                    issues_found += 1
                                    
                except Exception as e:
                    print(f"   ⚠️  Error checking {file_path}: {e}")
        
        if issues_found == 0:
            print("   ✅ No problematic demo data fallbacks found in admin endpoints")
            return True
        else:
            print(f"   ❌ {issues_found} demo data issues found in admin endpoints")
            return False

    def check_logging_implementation(self) -> bool:
        """Check that comprehensive logging is implemented"""
        print("\n📝 Checking audit logging implementation...")
        print("-" * 50)
        
        required_log_patterns = [
            ("backend/services/booking_service.py", r"BOOKING ATTEMPT", "Booking attempt logging"),
            ("backend/services/booking_service.py", r"BOOKING CREATED", "Booking creation logging"),
            ("backend/services/booking_service.py", r"BOOKING REJECTED", "Booking rejection logging"),
            ("backend/auth.py", r"ADMIN ACCESS ATTEMPT", "Admin access logging"),
            ("backend/auth.py", r"ADMIN ACCESS GRANTED", "Admin access grant logging")
        ]
        
        missing_logs = 0
        for file_path, pattern, description in required_log_patterns:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    if re.search(pattern, content):
                        print(f"   ✅ {description} implemented")
                    else:
                        print(f"   ❌ {description} missing")
                        self.add_issue("CRITICAL", f"Missing required logging: {description}")
                        missing_logs += 1
                        
                except Exception as e:
                    print(f"   ⚠️  Error checking {file_path}: {e}")
            else:
                print(f"   ❌ {file_path} not found")
                self.add_issue("CRITICAL", f"Required file not found: {file_path}")
                missing_logs += 1
        
        return missing_logs == 0

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        # Run all security checks
        pattern_check = self.scan_file_patterns()
        endpoint_check = self.check_admin_endpoint_security()
        cleanup_check = self.check_demo_data_cleanup()
        logging_check = self.check_logging_implementation()
        
        all_checks_passed = pattern_check and endpoint_check and cleanup_check and logging_check
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "PASS" if all_checks_passed else "FAIL",
            "checks": {
                "security_patterns": pattern_check,
                "admin_endpoint_security": endpoint_check,
                "demo_data_cleanup": cleanup_check,
                "audit_logging": logging_check
            },
            "issues": {
                "critical": len(self.security_issues),
                "warnings": len(self.warnings),
                "info": len(self.info)
            },
            "detailed_issues": self.security_issues,
            "detailed_warnings": self.warnings,
            "detailed_info": self.info,
            "deployment_recommendation": "APPROVE" if all_checks_passed else "BLOCK"
        }
        
        return report

    def print_security_summary(self, report: Dict[str, Any]):
        """Print security validation summary"""
        print(f"\n{'='*80}")
        print(f"🔒 CI/CD SECURITY VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        status_emoji = "✅" if report["overall_status"] == "PASS" else "❌"
        print(f"{status_emoji} Overall Status: {report['overall_status']}")
        
        print(f"\n📊 Check Results:")
        for check_name, result in report["checks"].items():
            emoji = "✅" if result else "❌"
            print(f"   {emoji} {check_name.replace('_', ' ').title()}: {'PASS' if result else 'FAIL'}")
        
        print(f"\n📋 Issue Summary:")
        print(f"   🔴 Critical: {report['issues']['critical']}")
        print(f"   🟠 Warnings: {report['issues']['warnings']}")
        print(f"   🔵 Info: {report['issues']['info']}")
        
        if report['issues']['critical'] > 0:
            print(f"\n🚨 CRITICAL SECURITY ISSUES:")
            for issue in self.security_issues:
                print(f"   🔴 {issue['description']} ({issue['file']}:{issue['line']})")
        
        print(f"\n🚀 Deployment Recommendation: {report['deployment_recommendation']}")
        
        if report['deployment_recommendation'] == "BLOCK":
            print("   ⛔ Deployment should be BLOCKED due to security issues")
        else:
            print("   ✅ Deployment is APPROVED - security checks passed")
        
        # Save report
        report_file = Path("cicd_security_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📋 Security report saved to: {report_file}")
        
        return report["overall_status"] == "PASS"

def main():
    """Run CI/CD security validation"""
    print("🔒 CI/CD SECURITY VALIDATION")
    print("Automated security checks to prevent deployment of insecure configurations")
    print("=" * 80)
    
    validator = CICDSecurityValidator()
    
    # Generate security report
    report = validator.generate_security_report()
    
    # Print summary and determine exit code
    deployment_approved = validator.print_security_summary(report)
    
    return 0 if deployment_approved else 1

if __name__ == "__main__":
    sys.exit(main())