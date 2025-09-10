#!/bin/bash

# Script to start a user-specific Theia container
# Usage: ./start-user-container.sh <user_id> [port]

USER_ID=$1
PORT=${2:-3000}

if [ -z "$USER_ID" ]; then
    echo "Usage: $0 <user_id> [port]"
    exit 1
fi

CONTAINER_NAME="theia-user-${USER_ID}"
PROJECT_DIR="../projects/${USER_ID}"
NETWORK_NAME="robot-console-network"

# Create project directory if it doesn't exist
mkdir -p "$PROJECT_DIR"

# Create default files for new users
if [ ! -f "$PROJECT_DIR/welcome.py" ]; then
    cat > "$PROJECT_DIR/welcome.py" << 'EOF'
#!/usr/bin/env python3
"""
Welcome to your Robot Console workspace!

This is your personal development environment where you can:
- Write Python and C++ code for robot control
- Access Git version control
- Use the integrated terminal
- Manage your project files

Your work is automatically saved and will persist between sessions.
"""

def main():
    print("Welcome to Robot Console!")
    print("Your development environment is ready.")
    
    # Example robot code snippet
    print("\n--- Example Robot Code ---")
    robot_position = {"x": 0, "y": 0, "angle": 0}
    print(f"Robot position: {robot_position}")

if __name__ == "__main__":
    main()
EOF
fi

# Create a simple C++ example
if [ ! -f "$PROJECT_DIR/robot_example.cpp" ]; then
    cat > "$PROJECT_DIR/robot_example.cpp" << 'EOF'
#include <iostream>
#include <vector>

class Robot {
public:
    double x, y, angle;
    
    Robot(double x = 0, double y = 0, double angle = 0) 
        : x(x), y(y), angle(angle) {}
    
    void move(double distance) {
        x += distance * cos(angle);
        y += distance * sin(angle);
        std::cout << "Robot moved to (" << x << ", " << y << ")" << std::endl;
    }
    
    void rotate(double angle_change) {
        angle += angle_change;
        std::cout << "Robot rotated to " << angle << " radians" << std::endl;
    }
};

int main() {
    std::cout << "Robot C++ Example" << std::endl;
    Robot robot(0, 0, 0);
    robot.move(1.0);
    robot.rotate(0.5);
    return 0;
}
EOF
fi

# Stop existing container if running
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# Create network if it doesn't exist
docker network create "$NETWORK_NAME" 2>/dev/null || true

# Start new container
echo "Starting Theia container for user $USER_ID on port $PORT..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -p "$PORT:3000" \
    -v "$(pwd)/$PROJECT_DIR:/home/project" \
    --restart unless-stopped \
    robot-console-theia:latest

echo "Container $CONTAINER_NAME started successfully!"
echo "Theia IDE will be available at: http://localhost:$PORT"