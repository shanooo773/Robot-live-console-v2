#!/usr/bin/env python3
"""
Validation script for production fix: Same-origin Theia, Array-safe Frontend, and Stable Auth
"""
import re
import sys
from pathlib import Path

def check_nginx_config():
    """Verify nginx configuration has SSL and Theia proxy"""
    print("✓ Checking nginx configuration...")
    nginx_path = Path(__file__).parent / "robot-console-app.nginx.conf"
    content = nginx_path.read_text()
    
    checks = [
        ("SSL certificate config", "ssl_certificate"),
        ("SSL certificate key", "ssl_certificate_key"),
        ("HTTPS redirect", "return 301 https://"),
        ("Theia dynamic port proxy", r"location ~ \^/theia/\(\?<port>"),
        ("WebSocket support", "proxy_set_header Upgrade"),
        ("API proxy", r"location ~ \^/\(auth\|admin"),
    ]
    
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ MISSING: {name}")
            return False
    return True

def check_backend_auth():
    """Verify backend /auth/me uses token sub"""
    print("\n✓ Checking backend /auth/me endpoint...")
    main_path = Path(__file__).parent / "backend" / "main.py"
    content = main_path.read_text()
    
    # Check for the auth/me endpoint with sub extraction
    if 'user_id = current_user.get("sub")' in content:
        print("  ✓ Uses token 'sub' as user ID")
    else:
        print("  ✗ MISSING: Token sub extraction")
        return False
    
    if 'isinstance(user_id, str) and user_id.isdigit()' in content:
        print("  ✓ String to int conversion present")
    else:
        print("  ✗ MISSING: User ID type conversion")
        return False
    
    return True

def check_theia_service():
    """Verify Theia service uses same-origin URLs"""
    print("\n✓ Checking Theia service URLs...")
    theia_path = Path(__file__).parent / "backend" / "services" / "theia_service.py"
    content = theia_path.read_text()
    
    if '/theia/' in content and 'BASE_URL' in content:
        print("  ✓ Uses same-origin URL pattern (/theia/<port>/)")
        return True
    else:
        print("  ✗ MISSING: Same-origin URL pattern")
        return False

def check_frontend_api():
    """Verify frontend API client has ensureArray"""
    print("\n✓ Checking frontend API client...")
    api_path = Path(__file__).parent / "frontend" / "src" / "api.js"
    content = api_path.read_text()
    
    if 'export const ensureArray' in content:
        print("  ✓ ensureArray helper defined")
    else:
        print("  ✗ MISSING: ensureArray helper")
        return False
    
    functions = ['getUserBookings', 'getAdminUsers', 'getAdminBookings', 'getRobots']
    for func in functions:
        pattern = rf'{func}.*ensureArray'
        if re.search(pattern, content, re.DOTALL):
            print(f"  ✓ {func} uses ensureArray")
        else:
            print(f"  ✗ MISSING: {func} does not use ensureArray")
            return False
    
    return True

def check_booking_page():
    """Verify BookingPage has array guards"""
    print("\n✓ Checking BookingPage component...")
    booking_path = Path(__file__).parent / "frontend" / "src" / "components" / "BookingPage.jsx"
    content = booking_path.read_text()
    
    guards = [
        'safeAnnouncements',
        'safeUpcoming',
        'safePast',
        'safeAvailableRobotsKeys'
    ]
    
    for guard in guards:
        if guard in content:
            print(f"  ✓ {guard} defined")
        else:
            print(f"  ✗ MISSING: {guard}")
            return False
    
    # Check that safe variables are used in map calls
    if 'safeAnnouncements.map' in content:
        print("  ✓ safeAnnouncements used in map")
    else:
        print("  ✗ MISSING: safeAnnouncements.map usage")
        return False
    
    return True

def check_utils():
    """Verify utils directory and theiaUrl helper exists"""
    print("\n✓ Checking frontend utils...")
    utils_path = Path(__file__).parent / "frontend" / "src" / "utils" / "theiaUrl.js"
    
    if utils_path.exists():
        content = utils_path.read_text()
        if 'buildTheiaUrl' in content:
            print("  ✓ theiaUrl.js with buildTheiaUrl function exists")
            return True
        else:
            print("  ✗ buildTheiaUrl function not found")
            return False
    else:
        print("  ✗ MISSING: theiaUrl.js file")
        return False

def main():
    print("=" * 60)
    print("Production Fix Validation")
    print("=" * 60)
    
    results = [
        check_nginx_config(),
        check_backend_auth(),
        check_theia_service(),
        check_frontend_api(),
        check_booking_page(),
        check_utils()
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All checks passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some checks failed!")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
