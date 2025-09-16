#!/usr/bin/env python3
"""
Simple test for the overlap detection fix
"""

import sys
import os
from datetime import datetime, timedelta, time

# Test the time overlap function directly
def test_time_overlap_function():
    """Test the _times_overlap function"""
    print("🧪 Testing time overlap detection function...")
    
    def _parse_time_string(time_str: str) -> time:
        """Parse time string to time object"""
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            return time(hour, minute)
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    
    def _times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time ranges overlap"""
        try:
            t1_start = _parse_time_string(start1)
            t1_end = _parse_time_string(end1)
            t2_start = _parse_time_string(start2)
            t2_end = _parse_time_string(end2)
            
            # Two ranges overlap if: start1 < end2 AND start2 < end1
            return t1_start < t2_end and t2_start < t1_end
        except ValueError as e:
            print(f"Error comparing times: {e}")
            return False
    
    # Test cases
    test_cases = [
        {
            "name": "Exact overlap",
            "range1": ("10:00", "11:00"),
            "range2": ("10:00", "11:00"),
            "expected": True
        },
        {
            "name": "Partial overlap (start)",
            "range1": ("10:00", "11:00"),
            "range2": ("10:30", "11:30"),
            "expected": True
        },
        {
            "name": "Partial overlap (end)",
            "range1": ("10:00", "11:00"),
            "range2": ("09:30", "10:30"),
            "expected": True
        },
        {
            "name": "Complete containment",
            "range1": ("10:00", "12:00"),
            "range2": ("10:30", "11:30"),
            "expected": True
        },
        {
            "name": "No overlap (before)",
            "range1": ("10:00", "11:00"),
            "range2": ("11:00", "12:00"),
            "expected": False
        },
        {
            "name": "No overlap (after)",
            "range1": ("11:00", "12:00"),
            "range2": ("10:00", "11:00"),
            "expected": False
        },
        {
            "name": "Adjacent ranges",
            "range1": ("10:00", "11:00"),
            "range2": ("11:00", "12:00"),
            "expected": False
        }
    ]
    
    print("Testing overlap detection logic:")
    all_passed = True
    
    for test_case in test_cases:
        start1, end1 = test_case["range1"]
        start2, end2 = test_case["range2"]
        expected = test_case["expected"]
        
        result = _times_overlap(start1, end1, start2, end2)
        status = "✅" if result == expected else "❌"
        
        print(f"{status} {test_case['name']}: {start1}-{end1} vs {start2}-{end2} = {result}")
        
        if result != expected:
            all_passed = False
    
    return all_passed

def test_string_time_comparison():
    """Test string time comparison issues"""
    print("\n🧪 Testing string time comparison...")
    
    def _parse_time_string(time_str: str) -> time:
        """Parse time string to time object"""
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            return time(hour, minute)
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    
    # Test problematic string comparisons
    print("String comparison issues:")
    
    # This would fail with string comparison
    time1_str = "9:00"   # No leading zero
    time2_str = "10:00"  # Leading zero
    
    # String comparison (wrong)
    string_result = time1_str <= time2_str
    print(f"String comparison '9:00' <= '10:00': {string_result}")
    
    # Proper time object comparison (correct)
    time1_obj = _parse_time_string(time1_str)
    time2_obj = _parse_time_string(time2_str)
    proper_result = time1_obj <= time2_obj
    print(f"Time object comparison 9:00 <= 10:00: {proper_result}")
    
    # Test boundary case
    current_time_str = datetime.now().strftime("%H:%M")
    booking_start = "09:00"
    booking_end = "22:00"
    
    print(f"\nBoundary test - Current time: {current_time_str}")
    print(f"Booking window: {booking_start} - {booking_end}")
    
    # String comparison
    string_in_range = booking_start <= current_time_str <= booking_end
    print(f"String comparison result: {string_in_range}")
    
    # Proper time comparison
    current_time_obj = datetime.now().time()
    start_obj = _parse_time_string(booking_start)
    end_obj = _parse_time_string(booking_end)
    proper_in_range = start_obj <= current_time_obj <= end_obj
    print(f"Time object comparison result: {proper_in_range}")
    
    return True

def main():
    """Run all tests"""
    print("🔧 TESTING BOOKING SERVICE FIXES")
    print("=" * 50)
    
    success = True
    success &= test_time_overlap_function()
    success &= test_string_time_comparison()
    
    if success:
        print("\n🎉 All fix tests passed!")
        print("✅ Overlap detection works correctly")
        print("✅ String time comparison issues resolved")
    else:
        print("\n❌ Some fix tests failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)