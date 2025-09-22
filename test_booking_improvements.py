#!/usr/bin/env python3

"""
Test Booking Improvements
Tests the enhanced booking service functionality
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_working_hours_validation():
    """Test working hours validation logic"""
    print("🔍 Testing working hours validation...")
    
    from services.booking_service import BookingService
    
    # Create a mock database manager for testing
    class MockDB:
        def get_bookings_for_date_range(self, start_date, end_date):
            return []
    
    booking_service = BookingService(MockDB())
    
    # Test scenarios with future dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    test_cases = [
        {
            "name": "Valid working hours booking",
            "date": tomorrow,
            "start_time": "10:00",
            "end_time": "11:00",
            "expected": True
        },
        {
            "name": "Too early - before 9 AM",
            "date": tomorrow, 
            "start_time": "08:00",
            "end_time": "09:00",
            "expected": False
        },
        {
            "name": "Too late - after 6 PM",
            "date": tomorrow,
            "start_time": "18:00", 
            "end_time": "19:00",
            "expected": False
        },
        {
            "name": "Exceeds working hours",
            "date": tomorrow,
            "start_time": "17:00",
            "end_time": "19:00", 
            "expected": False
        },
        {
            "name": "Too long duration (3 hours)",
            "date": day_after,
            "start_time": "09:00",
            "end_time": "12:00",
            "expected": False
        },
        {
            "name": "Too short duration (30 min) - should be valid for 30+ min",
            "date": day_after, 
            "start_time": "10:00",
            "end_time": "10:30",
            "expected": True  # 30 minutes should be allowed
        },
        {
            "name": "Valid 2-hour booking",
            "date": day_after,
            "start_time": "14:00",
            "end_time": "16:00", 
            "expected": True
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        result = booking_service.validate_booking_time(
            test_case["date"], 
            test_case["start_time"], 
            test_case["end_time"]
        )
        
        if result == test_case["expected"]:
            print(f"✅ {test_case['name']}: PASSED")
        else:
            print(f"❌ {test_case['name']}: FAILED (expected {test_case['expected']}, got {result})")
            all_passed = False
    
    return all_passed

def test_available_slots_generation():
    """Test available slots generation logic"""
    print("\n🔍 Testing available slots generation...")
    
    from services.booking_service import BookingService
    
    # Create a mock database manager with some existing bookings
    class MockDB:
        def get_bookings_for_date_range(self, start_date, end_date):
            return [
                {
                    "robot_type": "turtlebot",
                    "start_time": "10:00",
                    "end_time": "11:00", 
                    "status": "active"
                },
                {
                    "robot_type": "arm",
                    "start_time": "14:00",
                    "end_time": "15:00",
                    "status": "active"
                }
            ]
    
    booking_service = BookingService(MockDB())
    
    # Test getting available slots for a future date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Test for turtlebot (has one booking)
    turtlebot_slots = booking_service.get_available_time_slots(tomorrow, "turtlebot")
    print(f"Available turtlebot slots: {len(turtlebot_slots)}")
    
    # Should have slots from 9-18, excluding 10-11 (8 slots total)
    expected_turtlebot_slots = 8  # 9 hours minus 1 booked slot
    
    # Test for hand (no bookings)
    hand_slots = booking_service.get_available_time_slots(tomorrow, "hand")
    print(f"Available hand slots: {len(hand_slots)}")
    
    # Should have all 9 slots (9-18)
    expected_hand_slots = 9
    
    success = True
    if len(turtlebot_slots) != expected_turtlebot_slots:
        print(f"❌ Turtlebot slots mismatch: expected {expected_turtlebot_slots}, got {len(turtlebot_slots)}")
        success = False
    else:
        print(f"✅ Turtlebot slots correct: {len(turtlebot_slots)}")
    
    if len(hand_slots) != expected_hand_slots:
        print(f"❌ Hand slots mismatch: expected {expected_hand_slots}, got {len(hand_slots)}")
        success = False  
    else:
        print(f"✅ Hand slots correct: {len(hand_slots)}")
    
    return success

if __name__ == "__main__":
    print("🤖 Booking System Improvements Test\n")
    
    success = True
    success &= test_working_hours_validation()
    success &= test_available_slots_generation()
    
    if success:
        print("\n🎉 All booking improvement tests passed!")
        print("✅ Working hours validation working correctly")
        print("✅ Available slots generation working correctly")
        print("✅ Business rules properly implemented")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)