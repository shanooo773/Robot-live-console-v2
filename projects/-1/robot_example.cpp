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
