#!/usr/bin/env python3
"""
MySQL Section Detailed Validation Script
Specialized script to check in detail that MySQL section is correct
Validates MySQL configuration, schema, queries, and data integrity

Features:
- Detailed MySQL configuration validation
- Schema structure and syntax validation
- Query analysis and optimization suggestions
- Performance testing and benchmarking
- MySQL-specific feature validation
- Security configuration checks
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import hashlib

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from dotenv import load_dotenv
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  MySQL dependencies not available: {e}")
    MYSQL_AVAILABLE = False

load_dotenv()

class MySQLDetailedValidator:
    def __init__(self):
        self.issues = []
        self.recommendations = []
        self.performance_metrics = {}
        self.schema_analysis = {}
        self.connection = None
        
    def add_issue(self, severity: str, description: str):
        """Add validation issue"""
        self.issues.append({
            "severity": severity,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_recommendation(self, category: str, description: str):
        """Add optimization recommendation"""
        self.recommendations.append({
            "category": category,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })

    def validate_mysql_configuration(self) -> bool:
        """Comprehensive MySQL configuration validation"""
        print("🔧 Validating MySQL Configuration...")
        print("-" * 50)
        
        # 1. Environment variables validation
        self._validate_env_config()
        
        # 2. Connection parameters validation
        self._validate_connection_params()
        
        # 3. Database file validation
        self._validate_database_files()
        
        # 4. Configuration file validation
        self._validate_config_files()
        
        return len([i for i in self.issues if i['severity'] == 'CRITICAL']) == 0

    def _validate_env_config(self):
        """Validate environment configuration"""
        print("\n📋 Environment Configuration:")
        
        required_vars = {
            'DATABASE_TYPE': 'mysql',
            'MYSQL_HOST': None,
            'MYSQL_PORT': '3306',
            'MYSQL_USER': None,
            'MYSQL_PASSWORD': None,
            'MYSQL_DATABASE': None
        }
        
        for var, expected in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.add_issue("CRITICAL", f"Missing required environment variable: {var}")
                print(f"   ❌ {var}: Missing")
            elif expected and value != expected:
                self.add_issue("HIGH", f"{var} should be '{expected}', found '{value}'")
                print(f"   ⚠️  {var}: {value} (expected: {expected})")
            else:
                print(f"   ✅ {var}: {value}")
        
        # Advanced configuration checks
        charset = os.getenv('MYSQL_CHARSET', 'utf8mb4')
        if charset != 'utf8mb4':
            self.add_recommendation("Character Set", f"Use utf8mb4 instead of {charset} for full Unicode support")
        
        port = int(os.getenv('MYSQL_PORT', 3306))
        if port != 3306:
            self.add_recommendation("Security", f"Non-standard port {port} can improve security")

    def _validate_connection_params(self):
        """Validate connection parameters"""
        print("\n🔗 Connection Parameters:")
        
        config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', ''),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', ''),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # Validate host
        if config['host'] in ['localhost', '127.0.0.1']:
            print(f"   ✅ Host: {config['host']} (local connection)")
        else:
            print(f"   🌐 Host: {config['host']} (remote connection)")
            self.add_recommendation("Security", "Ensure remote MySQL connection is encrypted (SSL)")
        
        # Validate port
        if 1024 <= config['port'] <= 65535:
            print(f"   ✅ Port: {config['port']}")
        else:
            self.add_issue("HIGH", f"Invalid MySQL port: {config['port']}")
        
        # Validate user
        if config['user']:
            print(f"   ✅ User: {config['user']}")
            if config['user'] == 'root':
                self.add_issue("HIGH", "Using root user is not recommended for applications")
        else:
            self.add_issue("CRITICAL", "MySQL user not specified")
        
        # Validate database name
        if config['database']:
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', config['database']):
                print(f"   ✅ Database: {config['database']}")
            else:
                self.add_issue("MEDIUM", f"Database name '{config['database']}' contains special characters")
        else:
            self.add_issue("CRITICAL", "MySQL database not specified")

    def _validate_database_files(self):
        """Validate database-related files"""
        print("\n📁 Database Files:")
        
        # Check database.py
        db_file = Path('backend/database.py')
        if db_file.exists():
            print(f"   ✅ Found: {db_file}")
            self._analyze_database_py(db_file)
        else:
            self.add_issue("CRITICAL", "backend/database.py not found")
        
        # Check SQL schema files
        sql_files = ['robot_console.sql', 'schema.sql', 'init.sql']
        found_sql = False
        for sql_file in sql_files:
            if Path(sql_file).exists():
                print(f"   ✅ Found SQL file: {sql_file}")
                found_sql = True
                self._analyze_sql_file(Path(sql_file))
        
        if not found_sql:
            self.add_recommendation("Documentation", "Consider adding SQL schema file for documentation")

    def _analyze_database_py(self, file_path: Path):
        """Analyze database.py file"""
        content = file_path.read_text()
        
        # Check MySQL-specific features
        mysql_features = {
            'pymysql': 'MySQL driver import',
            'AUTO_INCREMENT': 'MySQL auto-increment syntax',
            'VARCHAR(': 'MySQL varchar with length',
            'TIMESTAMP': 'MySQL timestamp type',
            'DEFAULT CURRENT_TIMESTAMP': 'MySQL timestamp defaults',
            'FOREIGN KEY': 'Foreign key constraints',
            'ENGINE=InnoDB': 'InnoDB storage engine'
        }
        
        print("     🔍 MySQL Features in database.py:")
        for feature, description in mysql_features.items():
            if feature in content:
                print(f"       ✅ {description}")
            else:
                if feature == 'ENGINE=InnoDB':
                    self.add_recommendation("Performance", "Explicitly specify ENGINE=InnoDB for tables")
                elif feature == 'FOREIGN KEY':
                    self.add_recommendation("Data Integrity", "Consider adding foreign key constraints")
        
        # Check for SQLite leftovers
        sqlite_patterns = ['sqlite3', '.db', 'sqlite', 'INTEGER PRIMARY KEY']
        sqlite_found = []
        for pattern in sqlite_patterns:
            if pattern.lower() in content.lower():
                sqlite_found.append(pattern)
        
        if sqlite_found:
            self.add_issue("HIGH", f"SQLite references found in database.py: {sqlite_found}")
        else:
            print("     ✅ No SQLite leftovers found")

    def _analyze_sql_file(self, file_path: Path):
        """Analyze SQL schema file"""
        content = file_path.read_text()
        
        print(f"     🔍 Analyzing {file_path}:")
        
        # Count tables
        table_matches = re.findall(r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)', content, re.IGNORECASE)
        print(f"       📊 Tables defined: {len(table_matches)} ({', '.join(table_matches)})")
        
        # Check MySQL syntax
        mysql_syntax = [
            ('AUTO_INCREMENT', 'Auto-increment columns'),
            ('ENGINE=InnoDB', 'InnoDB storage engine'),
            ('DEFAULT CHARSET=utf8mb4', 'UTF8MB4 character set'),
            ('FOREIGN KEY', 'Foreign key constraints'),
            ('INDEX', 'Database indexes')
        ]
        
        for syntax, description in mysql_syntax:
            count = len(re.findall(syntax, content, re.IGNORECASE))
            if count > 0:
                print(f"       ✅ {description}: {count} occurrences")
            elif syntax in ['ENGINE=InnoDB', 'DEFAULT CHARSET=utf8mb4']:
                self.add_recommendation("Best Practices", f"Consider adding {description}")

    def _validate_config_files(self):
        """Validate configuration files"""
        print("\n⚙️  Configuration Files:")
        
        # Check .env files
        env_files = ['.env', '.env.template', '.env.production.template']
        for env_file in env_files:
            if Path(env_file).exists():
                print(f"   ✅ Found: {env_file}")
                self._check_env_file_mysql_config(Path(env_file))
        
        # Check Docker configuration
        docker_files = ['docker-compose.yml', 'Dockerfile']
        for docker_file in docker_files:
            if Path(docker_file).exists():
                print(f"   ✅ Found: {docker_file}")
                self._check_docker_mysql_config(Path(docker_file))

    def _check_env_file_mysql_config(self, file_path: Path):
        """Check MySQL configuration in .env file"""
        content = file_path.read_text()
        
        # Check for MySQL-specific variables
        mysql_vars = ['MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
        found_vars = []
        
        for var in mysql_vars:
            if f'{var}=' in content:
                found_vars.append(var)
        
        print(f"     📋 MySQL variables in {file_path}: {len(found_vars)}/{len(mysql_vars)}")
        
        if len(found_vars) < len(mysql_vars):
            missing = set(mysql_vars) - set(found_vars)
            self.add_recommendation("Configuration", f"Add missing MySQL variables to {file_path}: {missing}")

    def _check_docker_mysql_config(self, file_path: Path):
        """Check MySQL configuration in Docker files"""
        content = file_path.read_text()
        
        if 'mysql' in content.lower():
            print(f"     🐳 MySQL references found in {file_path}")
            
            # Check for version specification
            mysql_version_pattern = r'mysql:(\d+\.?\d*)'
            versions = re.findall(mysql_version_pattern, content, re.IGNORECASE)
            if versions:
                print(f"       📦 MySQL version: {versions[0]}")
            else:
                self.add_recommendation("Docker", "Specify MySQL version in Docker configuration")

    def validate_mysql_live_connection(self) -> bool:
        """Test live MySQL connection and features"""
        print("\n🔌 Live MySQL Connection Validation...")
        print("-" * 50)
        
        if not MYSQL_AVAILABLE:
            print("   ⚠️  PyMySQL not available - skipping live connection tests")
            return False
        
        config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', ''),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', ''),
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'autocommit': True
        }
        
        try:
            print(f"   🔄 Attempting connection to {config['host']}:{config['port']}...")
            self.connection = pymysql.connect(**config)
            cursor = self.connection.cursor()
            
            # Basic connection test
            cursor.execute("SELECT 1")
            print("   ✅ MySQL connection successful")
            
            # Detailed MySQL validation
            self._validate_mysql_server_info(cursor)
            self._validate_mysql_privileges(cursor)
            self._validate_mysql_performance(cursor)
            self._validate_mysql_security(cursor)
            self._validate_schema_live(cursor)
            
            return True
            
        except Exception as e:
            print(f"   ❌ MySQL connection failed: {e}")
            self.add_issue("CRITICAL", f"Cannot connect to MySQL: {e}")
            return False

    def _validate_mysql_server_info(self, cursor):
        """Validate MySQL server information"""
        print("\n📊 MySQL Server Information:")
        
        # Server version
        cursor.execute("SELECT VERSION() as version")
        version = cursor.fetchone()[0]
        print(f"   📦 Version: {version}")
        
        version_number = re.search(r'(\d+\.\d+)', version)
        if version_number:
            major_version = float(version_number.group(1))
            if major_version < 5.7:
                self.add_issue("HIGH", f"MySQL version {major_version} is outdated. Recommend 8.0+")
            elif major_version >= 8.0:
                print("     ✅ Modern MySQL version")
            else:
                self.add_recommendation("Upgrade", "Consider upgrading to MySQL 8.0 for better performance")
        
        # Character set and collation
        cursor.execute("SELECT @@character_set_server, @@collation_server")
        charset_info = cursor.fetchone()
        print(f"   📝 Server charset: {charset_info[0]}, collation: {charset_info[1]}")
        
        # Time zone
        cursor.execute("SELECT @@time_zone, NOW()")
        tz_info = cursor.fetchone()
        print(f"   🕐 Time zone: {tz_info[0]}, current time: {tz_info[1]}")
        
        # Storage engines
        cursor.execute("SHOW ENGINES")
        engines = cursor.fetchall()
        available_engines = [engine[0] for engine in engines if engine[1] == 'YES']
        print(f"   ⚙️  Available engines: {', '.join(available_engines)}")
        
        if 'InnoDB' not in available_engines:
            self.add_issue("HIGH", "InnoDB storage engine not available")

    def _validate_mysql_privileges(self, cursor):
        """Validate MySQL user privileges"""
        print("\n🔐 MySQL User Privileges:")
        
        # Current user
        cursor.execute("SELECT USER(), CURRENT_USER()")
        user_info = cursor.fetchone()
        print(f"   👤 Current user: {user_info[0]} (effective: {user_info[1]})")
        
        # User privileges
        cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
        grants = cursor.fetchall()
        
        required_privileges = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'INDEX']
        has_all_privileges = False
        
        for grant in grants:
            grant_str = grant[0]
            print(f"   🛡️  {grant_str}")
            
            if 'ALL PRIVILEGES' in grant_str:
                has_all_privileges = True
                break
        
        if not has_all_privileges:
            # Check individual privileges
            grant_text = ' '.join([grant[0] for grant in grants])
            missing_privileges = []
            
            for priv in required_privileges:
                if priv not in grant_text:
                    missing_privileges.append(priv)
            
            if missing_privileges:
                self.add_issue("HIGH", f"Missing required privileges: {missing_privileges}")
            else:
                print("     ✅ All required privileges granted")

    def _validate_mysql_performance(self, cursor):
        """Validate MySQL performance settings"""
        print("\n⚡ MySQL Performance Settings:")
        
        # Key performance variables
        performance_vars = {
            'innodb_buffer_pool_size': lambda x: self._check_buffer_pool_size(x),
            'max_connections': lambda x: self._check_max_connections(x),
            'query_cache_size': lambda x: self._check_query_cache(x),
            'innodb_log_file_size': lambda x: self._check_log_file_size(x),
            'innodb_flush_log_at_trx_commit': lambda x: self._check_flush_log(x)
        }
        
        for var, validator in performance_vars.items():
            cursor.execute(f"SHOW VARIABLES LIKE '{var}'")
            result = cursor.fetchone()
            
            if result:
                var_name, value = result
                print(f"   ⚙️  {var_name}: {value}")
                validator(value)
            else:
                print(f"   ⚠️  {var}: Not found")
        
        # Performance test
        self._performance_benchmark(cursor)

    def _check_buffer_pool_size(self, value):
        """Check InnoDB buffer pool size"""
        size_bytes = self._parse_size_value(value)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb < 128:
            self.add_recommendation("Performance", f"InnoDB buffer pool size ({size_mb:.0f}MB) is small. Consider increasing for better performance.")

    def _check_max_connections(self, value):
        """Check max connections setting"""
        max_conn = int(value)
        if max_conn < 100:
            self.add_recommendation("Scalability", f"Max connections ({max_conn}) might be too low for production.")
        elif max_conn > 1000:
            self.add_recommendation("Performance", f"Max connections ({max_conn}) is very high. Monitor connection usage.")

    def _check_query_cache(self, value):
        """Check query cache setting"""
        cache_size = self._parse_size_value(value)
        if cache_size == 0:
            print("     ℹ️  Query cache disabled (recommended for MySQL 8.0+)")
        else:
            print(f"     📊 Query cache enabled: {cache_size} bytes")

    def _check_log_file_size(self, value):
        """Check log file size"""
        size_bytes = self._parse_size_value(value)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb < 256:
            self.add_recommendation("Performance", f"InnoDB log file size ({size_mb:.0f}MB) is small. Consider increasing.")

    def _check_flush_log(self, value):
        """Check flush log setting"""
        flush_setting = int(value)
        if flush_setting == 1:
            print("     ✅ ACID compliant (flush_log_at_trx_commit=1)")
        else:
            self.add_recommendation("Reliability", f"flush_log_at_trx_commit={flush_setting} may risk data loss")

    def _parse_size_value(self, value):
        """Parse MySQL size value (e.g., '128M', '1G')"""
        if isinstance(value, int):
            return value
        
        value_str = str(value).upper()
        if value_str.endswith('K'):
            return int(value_str[:-1]) * 1024
        elif value_str.endswith('M'):
            return int(value_str[:-1]) * 1024 * 1024
        elif value_str.endswith('G'):
            return int(value_str[:-1]) * 1024 * 1024 * 1024
        else:
            return int(value_str)

    def _performance_benchmark(self, cursor):
        """Run performance benchmark"""
        print("\n🏃 Performance Benchmark:")
        
        # Simple query performance test
        start_time = datetime.now()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds() * 1000  # milliseconds
        print(f"   ⏱️  Simple query: {query_time:.2f}ms")
        
        self.performance_metrics['simple_query_ms'] = query_time
        
        if query_time > 100:
            self.add_issue("MEDIUM", f"Simple query took {query_time:.2f}ms (>100ms indicates performance issues)")

    def _validate_mysql_security(self, cursor):
        """Validate MySQL security settings"""
        print("\n🔒 MySQL Security Settings:")
        
        # SSL/TLS support
        cursor.execute("SHOW VARIABLES LIKE 'have_ssl'")
        ssl_result = cursor.fetchone()
        if ssl_result and ssl_result[1] == 'YES':
            print("   ✅ SSL/TLS support available")
        else:
            self.add_recommendation("Security", "Enable SSL/TLS for encrypted connections")
        
        # Validate users (don't show passwords)
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User != ''")
        users = cursor.fetchall()
        print(f"   👥 Database users: {len(users)}")
        
        for user, host in users:
            if user == 'root' and host == '%':
                self.add_issue("HIGH", "Root user allows connections from any host - security risk")
            elif user == 'root':
                print(f"     ⚠️  Root user: {user}@{host}")
            else:
                print(f"     👤 User: {user}@{host}")

    def _validate_schema_live(self, cursor):
        """Validate live database schema"""
        print("\n🏗️  Live Schema Validation:")
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"   📋 Tables found: {len(tables)} ({', '.join(tables)})")
        
        # Analyze each table
        for table in tables:
            self._analyze_table_structure(cursor, table)
        
        # Check for indexes
        self._analyze_indexes(cursor, tables)

    def _analyze_table_structure(self, cursor, table_name):
        """Analyze individual table structure"""
        print(f"\n   🔍 Table: {table_name}")
        
        # Table status
        cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
        status = cursor.fetchone()
        
        if status:
            rows, data_length, engine = status[4], status[6], status[1]
            print(f"     📊 Rows: {rows}, Size: {data_length} bytes, Engine: {engine}")
            
            if engine != 'InnoDB':
                self.add_recommendation("Performance", f"Table {table_name} uses {engine}, consider InnoDB")
        
        # Column analysis
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        for col in columns:
            col_name, col_type, nullable, key, default, extra = col
            issues = []
            
            # Check for proper indexing
            if col_name == 'id' and 'auto_increment' not in extra.lower():
                issues.append("ID column should be AUTO_INCREMENT")
            
            # Check nullable constraints
            if col_name in ['email', 'name', 'password_hash'] and nullable == 'YES':
                issues.append("Should be NOT NULL")
            
            if issues:
                print(f"     ⚠️  {col_name} ({col_type}): {', '.join(issues)}")

    def _analyze_indexes(self, cursor, tables):
        """Analyze database indexes"""
        print(f"\n   📊 Index Analysis:")
        
        total_indexes = 0
        for table in tables:
            cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = cursor.fetchall()
            table_indexes = len([idx for idx in indexes if idx[2] != 'PRIMARY'])
            total_indexes += table_indexes
            
            if table_indexes == 0:
                self.add_recommendation("Performance", f"Table {table} has no secondary indexes")
        
        print(f"     📈 Total indexes: {total_indexes}")

    def generate_mysql_report(self) -> bool:
        """Generate comprehensive MySQL validation report"""
        print("\n" + "=" * 80)
        print("🐬 MYSQL DETAILED VALIDATION REPORT")
        print("=" * 80)
        
        # Summary
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])
        total_issues = len(self.issues)
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   ❌ Critical Issues: {critical_issues}")
        print(f"   ⚠️  High Priority Issues: {high_issues}")
        print(f"   📋 Total Issues: {total_issues}")
        print(f"   💡 Recommendations: {len(self.recommendations)}")
        
        # Issues
        if self.issues:
            print(f"\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"   {issue['severity']}: {issue['description']}")
        
        # Recommendations
        if self.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            categories = {}
            for rec in self.recommendations:
                cat = rec['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(rec['description'])
            
            for category, recs in categories.items():
                print(f"   📂 {category}:")
                for rec in recs:
                    print(f"     • {rec}")
        
        # Performance metrics
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for metric, value in self.performance_metrics.items():
                print(f"   📈 {metric}: {value}")
        
        # Overall assessment
        print(f"\n🎯 MYSQL ASSESSMENT:")
        if critical_issues > 0:
            print("   ❌ CRITICAL ISSUES - MySQL setup requires immediate attention")
            status = False
        elif high_issues > 0:
            print("   ⚠️  HIGH PRIORITY ISSUES - Review before production")
            status = False
        elif total_issues == 0:
            print("   ✅ MYSQL CONFIGURATION EXCELLENT - Ready for production")
            status = True
        else:
            print("   ✅ MYSQL CONFIGURATION GOOD - Minor improvements recommended")
            status = True
        
        # Save report
        self._save_mysql_report()
        
        return status

    def _save_mysql_report(self):
        """Save MySQL report to file"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "mysql_validation": {
                "issues": self.issues,
                "recommendations": self.recommendations,
                "performance_metrics": self.performance_metrics,
                "schema_analysis": self.schema_analysis
            }
        }
        
        report_file = Path('mysql_detailed_validation_report.json')
        report_file.write_text(json.dumps(report_data, indent=2))
        print(f"   📄 MySQL report saved to: {report_file}")

def main():
    """Run MySQL detailed validation"""
    print("🐬 MYSQL SECTION DETAILED VALIDATION")
    print("Script to check in detail that MySQL section is correct")
    print("=" * 80)
    
    validator = MySQLDetailedValidator()
    
    # Phase 1: Configuration validation (always runs)
    print("\n🔧 PHASE 1: MySQL Configuration Validation")
    config_valid = validator.validate_mysql_configuration()
    
    # Phase 2: Live connection validation (if possible)
    print("\n🔌 PHASE 2: Live MySQL Connection Validation")
    connection_valid = validator.validate_mysql_live_connection()
    
    # Generate comprehensive report
    overall_valid = validator.generate_mysql_report()
    
    # Return appropriate exit code
    if config_valid and (connection_valid or not MYSQL_AVAILABLE):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())