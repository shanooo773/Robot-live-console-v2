#!/usr/bin/env python3
"""
Demo User Welcome File

This is the workspace for the demo user account.
Your work is automatically saved but will be reset periodically.

Demo Credentials:
- Email: demo@user.com  
- Password: password

Features available:
- Eclipse Theia IDE with Python/C++ support
- WebRTC video streaming (when robots are connected)
- Terminal access for command-line operations
- Git version control
- File management and project organization
"""

def main():
    print("🤖 Welcome to Robot Console Demo!")
    print("This is a demonstration workspace.")
    print("Your files will persist during this session.")
    
    # Demo robot control example
    robot_status = {
        "position": {"x": 0, "y": 0, "angle": 0},
        "battery": 100,
        "connected": False
    }
    
    print(f"Robot Status: {robot_status}")
    print("\n✨ Ready to start programming!")

if __name__ == "__main__":
    main()