#!/usr/bin/env python3
"""
Test the fixed booking service
"""

import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend/services'))

from test_database_sqlite import TestDatabaseManager

def test_fixed_booking_service():
    """Test the fixed booking service"""
    print("🧪 Testing FIXED booking service...")
    
    try:
        # Create fresh database
        db = TestDatabaseManager("test_fixed_booking.db")
        
        # Import fixed booking service  
        from booking_service import BookingService
        booking_service = BookingService(db)
        
        demo_user = db.get_user_by_email("demo@example.com")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        print(f"Testing with date: {tomorrow}")
        
        # Test 1: Create valid booking
        print("\n1. Testing valid booking creation...")
        booking1 = booking_service.create_booking(
            demo_user["id"], "test_robot", tomorrow, "10:00", "11:00"
        )
        print(f"✅ Created booking: {booking1['robot_type']} {booking1['start_time']}-{booking1['end_time']}")
        
        # Test 2: Try exact duplicate (should fail)
        print("\n2. Testing exact duplicate prevention...")
        try:
            booking_service.create_booking(
                demo_user["id"], "test_robot", tomorrow, "10:00", "11:00"
            )
            print("❌ Exact duplicate was allowed!")
            return False
        except Exception as e:
            print(f"✅ Exact duplicate prevented: {str(e)[:70]}...")
        
        # Test 3: Try partial overlap (should fail with fixed version)
        print("\n3. Testing partial overlap prevention...")
        try:
            booking_service.create_booking(
                demo_user["id"], "test_robot", tomorrow, "10:30", "11:30"
            )
            print("❌ Partial overlap was allowed!")
            return False
        except Exception as e:
            print(f"✅ Partial overlap prevented: {str(e)[:70]}...")
        
        # Test 4: Try different robot (should work)
        print("\n4. Testing different robot booking...")
        booking2 = booking_service.create_booking(
            demo_user["id"], "different_robot", tomorrow, "10:00", "11:00"
        )
        print(f"✅ Different robot booking works: {booking2['robot_type']}")
        
        # Test 5: Test time comparison fix
        print("\n5. Testing time comparison fix...")
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        
        # Create booking that's active right now
        active_start = (now - timedelta(minutes=30)).strftime("%H:%M")
        active_end = (now + timedelta(minutes=30)).strftime("%H:%M")
        
        active_booking = booking_service.create_booking(
            demo_user["id"], "active_robot", today, active_start, active_end
        )
        print(f"✅ Created active booking: {active_start}-{active_end}")
        
        # Test session detection
        has_session = booking_service.has_active_session(demo_user["id"], "active_robot")
        print(f"✅ Active session detected: {has_session}")
        
        if not has_session:
            print("❌ Active session not detected!")
            return False
        
        # Test no session for different robot
        no_session = booking_service.has_active_session(demo_user["id"], "inactive_robot")
        print(f"✅ No session for different robot: {not no_session}")
        
        if no_session:
            print("❌ False positive for inactive robot!")
            return False
        
        print("\n🎉 All tests passed! Fixes are working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixed_booking_service()
    if success:
        print("\n✅ BOOKING SERVICE FIXES VERIFIED")
    else:
        print("\n❌ BOOKING SERVICE FIXES FAILED")
    sys.exit(0 if success else 1)