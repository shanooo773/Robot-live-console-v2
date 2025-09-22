#!/usr/bin/env python3
"""
Master Data Validation Suite
Orchestrates comprehensive validation of all data integrity, MySQL configuration, 
and admin dashboard functionality.

This is the main script that addresses the problem statement:
"check that all data is real and dashboard data of admin is real 
and script to check in detail that MySQL section is correct"
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def run_validation_script(script_name: str, description: str) -> Dict[str, Any]:
    """Run a validation script and capture results"""
    print(f"\n{'='*80}")
    print(f"🔍 RUNNING: {description}")
    print(f"Script: {script_name}")
    print('='*80)
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check for JSON report files
        report_data = None
        potential_reports = [
            f"{script_name.replace('.py', '_report.json')}",
            f"{script_name.replace('_validation.py', '_validation_report.json')}",
            "data_validation_report.json",
            "mysql_detailed_validation_report.json",
            "admin_dashboard_validation_report.json"
        ]
        
        for report_file in potential_reports:
            if Path(report_file).exists():
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                    break
                except:
                    continue
        
        return {
            "script": script_name,
            "description": description,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "report_data": report_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "description": description,
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": "Script timed out after 5 minutes",
            "report_data": None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "script": script_name,
            "description": description,
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": f"Error running script: {e}",
            "report_data": None,
            "timestamp": datetime.now().isoformat()
        }

def validate_environment() -> bool:
    """Validate the environment is ready for testing"""
    print("🔧 ENVIRONMENT VALIDATION")
    print("-" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"   🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("   ❌ Python 3.8+ required")
        return False
    
    # Check required directories
    required_dirs = ['backend', 'frontend']
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"   ✅ Directory: {dir_name}")
        else:
            print(f"   ❌ Missing directory: {dir_name}")
            return False
    
    # Check .env file
    if Path('.env').exists():
        print("   ✅ Configuration: .env file found")
    else:
        print("   ⚠️  Configuration: .env file missing")
    
    # Check validation scripts
    validation_scripts = [
        'comprehensive_data_validation.py',
        'mysql_detailed_validation.py', 
        'admin_dashboard_validation.py'
    ]
    
    missing_scripts = []
    for script in validation_scripts:
        if Path(script).exists():
            print(f"   ✅ Script: {script}")
        else:
            print(f"   ❌ Missing script: {script}")
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"   ❌ Missing validation scripts: {missing_scripts}")
        return False
    
    print("   ✅ Environment validation passed")
    return True

def analyze_validation_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze validation results and generate comprehensive assessment"""
    
    total_scripts = len(results)
    successful_scripts = len([r for r in results if r['success']])
    
    # Aggregate issues from all reports
    all_issues = []
    all_warnings = []
    all_recommendations = []
    
    for result in results:
        if result['report_data']:
            # Extract issues from different report formats
            report = result['report_data']
            
            # Handle comprehensive_data_validation format
            if 'issues' in report:
                all_issues.extend(report['issues'])
            
            # Handle mysql_detailed_validation format
            if 'mysql_validation' in report:
                mysql_val = report['mysql_validation']
                if 'issues' in mysql_val:
                    all_issues.extend(mysql_val['issues'])
                if 'recommendations' in mysql_val:
                    all_recommendations.extend(mysql_val['recommendations'])
            
            # Handle admin_dashboard_validation format
            if 'admin_validation' in report:
                admin_val = report['admin_validation']
                if 'issues' in admin_val:
                    all_issues.extend(admin_val['issues'])
                if 'warnings' in admin_val:
                    all_warnings.extend(admin_val['warnings'])
            
            # Handle direct format
            if 'warnings' in report:
                all_warnings.extend(report['warnings'])
    
    # Categorize issues by severity
    critical_issues = [i for i in all_issues if i.get('severity') == 'CRITICAL']
    high_issues = [i for i in all_issues if i.get('severity') == 'HIGH']
    medium_issues = [i for i in all_issues if i.get('severity') == 'MEDIUM']
    
    # Overall assessment
    if len(critical_issues) > 0:
        overall_status = "CRITICAL_ISSUES"
        status_message = "❌ CRITICAL ISSUES FOUND - System not ready for production"
    elif len(high_issues) > 0:
        overall_status = "HIGH_PRIORITY_ISSUES"
        status_message = "⚠️  HIGH PRIORITY ISSUES - Review required before production"
    elif successful_scripts < total_scripts:
        overall_status = "VALIDATION_INCOMPLETE"
        status_message = "⚠️  VALIDATION INCOMPLETE - Some tests could not run"
    elif len(medium_issues) > 5:
        overall_status = "MULTIPLE_MEDIUM_ISSUES"
        status_message = "⚠️  MULTIPLE MEDIUM ISSUES - Review recommended"
    else:
        overall_status = "VALIDATION_PASSED"
        status_message = "✅ VALIDATION PASSED - System appears ready"
    
    return {
        "overall_status": overall_status,
        "status_message": status_message,
        "summary": {
            "total_scripts": total_scripts,
            "successful_scripts": successful_scripts,
            "success_rate": (successful_scripts / total_scripts * 100) if total_scripts > 0 else 0,
            "total_issues": len(all_issues),
            "critical_issues": len(critical_issues),
            "high_issues": len(high_issues),
            "medium_issues": len(medium_issues),
            "warnings": len(all_warnings),
            "recommendations": len(all_recommendations)
        },
        "issues_by_severity": {
            "critical": critical_issues,
            "high": high_issues,
            "medium": medium_issues
        },
        "warnings": all_warnings,
        "recommendations": all_recommendations
    }

def generate_master_report(results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
    """Generate comprehensive master validation report"""
    
    report_lines = []
    report_lines.append("=" * 100)
    report_lines.append("🔍 MASTER DATA VALIDATION REPORT")
    report_lines.append("Comprehensive validation of all data integrity, MySQL configuration, and admin dashboard")
    report_lines.append("=" * 100)
    
    # Executive Summary
    report_lines.append("\n📊 EXECUTIVE SUMMARY")
    report_lines.append("-" * 50)
    summary = analysis['summary']
    report_lines.append(f"Scripts Run: {summary['total_scripts']}")
    report_lines.append(f"Successful: {summary['successful_scripts']}")
    report_lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
    report_lines.append(f"Total Issues: {summary['total_issues']}")
    report_lines.append(f"  - Critical: {summary['critical_issues']}")
    report_lines.append(f"  - High: {summary['high_issues']}")
    report_lines.append(f"  - Medium: {summary['medium_issues']}")
    report_lines.append(f"Warnings: {summary['warnings']}")
    report_lines.append(f"Recommendations: {summary['recommendations']}")
    
    # Overall Status
    report_lines.append(f"\n🎯 OVERALL STATUS")
    report_lines.append("-" * 50)
    report_lines.append(analysis['status_message'])
    
    # Detailed Results by Script
    report_lines.append(f"\n📋 DETAILED RESULTS BY SCRIPT")
    report_lines.append("-" * 50)
    
    for result in results:
        status_emoji = "✅" if result['success'] else "❌"
        report_lines.append(f"\n{status_emoji} {result['description']}")
        report_lines.append(f"   Script: {result['script']}")
        report_lines.append(f"   Exit Code: {result['exit_code']}")
        report_lines.append(f"   Timestamp: {result['timestamp']}")
        
        if result['stderr']:
            report_lines.append(f"   Errors: {result['stderr'][:200]}...")
    
    # Critical Issues
    if analysis['issues_by_severity']['critical']:
        report_lines.append(f"\n❌ CRITICAL ISSUES (MUST FIX)")
        report_lines.append("-" * 50)
        for issue in analysis['issues_by_severity']['critical']:
            report_lines.append(f"• {issue.get('description', issue)}")
    
    # High Priority Issues
    if analysis['issues_by_severity']['high']:
        report_lines.append(f"\n⚠️  HIGH PRIORITY ISSUES")
        report_lines.append("-" * 50)
        for issue in analysis['issues_by_severity']['high']:
            report_lines.append(f"• {issue.get('description', issue)}")
    
    # Key Recommendations
    if analysis['recommendations']:
        report_lines.append(f"\n💡 KEY RECOMMENDATIONS")
        report_lines.append("-" * 50)
        # Group recommendations by category
        rec_by_category = {}
        for rec in analysis['recommendations']:
            category = rec.get('category', 'General')
            if category not in rec_by_category:
                rec_by_category[category] = []
            rec_by_category[category].append(rec.get('description', rec))
        
        for category, recs in rec_by_category.items():
            report_lines.append(f"\n{category}:")
            for rec in recs[:3]:  # Limit to top 3 per category
                report_lines.append(f"  • {rec}")
    
    # Next Steps
    report_lines.append(f"\n🚀 NEXT STEPS")
    report_lines.append("-" * 50)
    
    if analysis['overall_status'] == 'CRITICAL_ISSUES':
        report_lines.append("1. 🔧 Fix all critical issues immediately")
        report_lines.append("2. 🔄 Re-run validation to verify fixes")
        report_lines.append("3. ⚙️  Address high priority issues")
        report_lines.append("4. 🚀 Deploy to staging for further testing")
    elif analysis['overall_status'] == 'HIGH_PRIORITY_ISSUES':
        report_lines.append("1. ⚙️  Address high priority issues")
        report_lines.append("2. 🔄 Re-run validation to verify fixes")
        report_lines.append("3. 📝 Review and address recommendations")
        report_lines.append("4. 🚀 Deploy to staging for testing")
    elif analysis['overall_status'] == 'VALIDATION_PASSED':
        report_lines.append("1. 🚀 System ready for production deployment")
        report_lines.append("2. 📝 Consider implementing recommendations for optimization")
        report_lines.append("3. 🔄 Set up automated validation in CI/CD")
        report_lines.append("4. 📊 Monitor system performance post-deployment")
    else:
        report_lines.append("1. 🔍 Investigate incomplete validations")
        report_lines.append("2. 🛠️  Set up MySQL connection for complete testing")
        report_lines.append("3. 🔄 Re-run validation with full environment")
        report_lines.append("4. 📝 Address any identified issues")
    
    report_lines.append(f"\nReport generated: {datetime.now().isoformat()}")
    report_lines.append("=" * 100)
    
    return "\n".join(report_lines)

def main():
    """Run comprehensive validation suite"""
    print("🔍 MASTER DATA VALIDATION SUITE")
    print("Comprehensive validation addressing the problem statement:")
    print("- Check that all data is real")
    print("- Dashboard data of admin is real") 
    print("- Script to check in detail that MySQL section is correct")
    print("=" * 100)
    
    # Validate environment
    if not validate_environment():
        print("\n❌ Environment validation failed. Cannot proceed.")
        return 1
    
    # Define validation scripts to run
    validation_suite = [
        {
            "script": "comprehensive_data_validation.py",
            "description": "Comprehensive Data Validation - Real data integrity, admin dashboard data, MySQL validation"
        },
        {
            "script": "mysql_detailed_validation.py", 
            "description": "MySQL Detailed Validation - MySQL section correctness, configuration, performance"
        },
        {
            "script": "admin_dashboard_validation.py",
            "description": "Admin Dashboard Validation - Admin data integrity, endpoint validation, UI components"
        },
        {
            "script": "validate_database.py",
            "description": "Database Schema Validation - Schema syntax, completeness, MySQL compliance"
        }
    ]
    
    # Run all validation scripts
    results = []
    
    for validation in validation_suite:
        if Path(validation["script"]).exists():
            result = run_validation_script(validation["script"], validation["description"])
            results.append(result)
        else:
            print(f"\n⚠️  Skipping {validation['script']} - not found")
            results.append({
                "script": validation["script"],
                "description": validation["description"],
                "exit_code": -2,
                "success": False,
                "stdout": "",
                "stderr": "Script not found",
                "report_data": None,
                "timestamp": datetime.now().isoformat()
            })
    
    # Analyze results
    analysis = analyze_validation_results(results)
    
    # Generate master report
    master_report = generate_master_report(results, analysis)
    
    # Display master report
    print("\n" + master_report)
    
    # Save master report
    report_file = Path('master_validation_report.txt')
    report_file.write_text(master_report)
    print(f"\n📄 Master report saved to: {report_file}")
    
    # Save detailed JSON report
    detailed_report = {
        "timestamp": datetime.now().isoformat(),
        "problem_statement": {
            "requirement_1": "check that all data is real",
            "requirement_2": "dashboard data of admin is real", 
            "requirement_3": "script to check in detail that MySQL section is correct"
        },
        "validation_results": results,
        "analysis": analysis,
        "master_report": master_report
    }
    
    json_report_file = Path('master_validation_report.json')
    json_report_file.write_text(json.dumps(detailed_report, indent=2))
    print(f"📄 Detailed JSON report saved to: {json_report_file}")
    
    # Return appropriate exit code
    if analysis['overall_status'] in ['VALIDATION_PASSED']:
        return 0
    elif analysis['overall_status'] in ['VALIDATION_INCOMPLETE']:
        return 2  # Partial success
    else:
        return 1  # Issues found

if __name__ == "__main__":
    sys.exit(main())