export const ROBOT_TYPES = ["arm", "hand", "turtlebot"];
export const PROGRAMMING_LANGUAGES = ["python", "cpp"];

export const ROBOT_CODE_SNIPPETS = {
  python: {
    arm: `#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float64
import time

def move_arm():
    # Initialize ROS node
    rospy.init_node('arm_controller', anonymous=True)
    
    # Publishers for joint control
    joint1_pub = rospy.Publisher('/robot_arm/joint1_position_controller/command', Float64, queue_size=10)
    joint2_pub = rospy.Publisher('/robot_arm/joint2_position_controller/command', Float64, queue_size=10)
    
    # Wait for publishers to initialize
    rospy.sleep(1)
    
    # Move joint 1 to 45 degrees (0.785 radians)
    joint1_pub.publish(0.785)
    rospy.sleep(2)
    
    # Move joint 2 to 30 degrees (0.524 radians)
    joint2_pub.publish(0.524)
    rospy.sleep(2)
    
    # Return to home position
    joint1_pub.publish(0.0)
    joint2_pub.publish(0.0)
    
    print("Arm movement completed!")

if __name__ == '__main__':
    try:
        move_arm()
    except rospy.ROSInterruptException:
        pass`,

    hand: `#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float64
import time

def control_hand():
    # Initialize ROS node
    rospy.init_node('hand_controller', anonymous=True)
    
    # Publishers for finger control
    finger1_pub = rospy.Publisher('/robot_hand/finger1_position_controller/command', Float64, queue_size=10)
    finger2_pub = rospy.Publisher('/robot_hand/finger2_position_controller/command', Float64, queue_size=10)
    thumb_pub = rospy.Publisher('/robot_hand/thumb_position_controller/command', Float64, queue_size=10)
    
    # Wait for publishers to initialize
    rospy.sleep(1)
    
    # Open hand
    finger1_pub.publish(0.0)
    finger2_pub.publish(0.0)
    thumb_pub.publish(0.0)
    rospy.sleep(2)
    
    # Close fingers to grasp
    finger1_pub.publish(1.2)
    finger2_pub.publish(1.2)
    thumb_pub.publish(0.3)
    rospy.sleep(2)
    
    # Open hand again
    finger1_pub.publish(0.0)
    finger2_pub.publish(0.0)
    thumb_pub.publish(0.0)
    
    print("Hand grasping completed!")

if __name__ == '__main__':
    try:
        control_hand()
    except rospy.ROSInterruptException:
        pass`,

    turtlebot: `#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
import time

def move_turtlebot():
    # Initialize ROS node
    rospy.init_node('turtlebot_controller', anonymous=True)
    
    # Publisher for velocity commands
    vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    
    # Create velocity message
    move_cmd = Twist()
    
    # Wait for publisher to initialize
    rospy.sleep(1)
    
    # Move forward
    move_cmd.linear.x = 0.2
    move_cmd.angular.z = 0.0
    vel_pub.publish(move_cmd)
    rospy.sleep(2)
    
    # Turn left
    move_cmd.linear.x = 0.0
    move_cmd.angular.z = 0.5
    vel_pub.publish(move_cmd)
    rospy.sleep(2)
    
    # Move forward again
    move_cmd.linear.x = 0.2
    move_cmd.angular.z = 0.0
    vel_pub.publish(move_cmd)
    rospy.sleep(2)
    
    # Stop
    move_cmd.linear.x = 0.0
    move_cmd.angular.z = 0.0
    vel_pub.publish(move_cmd)
    
    print("TurtleBot movement completed!")

if __name__ == '__main__':
    try:
        move_turtlebot()
    except rospy.ROSInterruptException:
        pass`
  },

  cpp: {
    arm: `#include <ros/ros.h>
#include <std_msgs/Float64.h>
#include <unistd.h>

class ArmController {
private:
    ros::NodeHandle nh_;
    ros::Publisher joint1_pub_;
    ros::Publisher joint2_pub_;

public:
    ArmController() {
        // Initialize publishers for joint control
        joint1_pub_ = nh_.advertise<std_msgs::Float64>("/robot_arm/joint1_position_controller/command", 10);
        joint2_pub_ = nh_.advertise<std_msgs::Float64>("/robot_arm/joint2_position_controller/command", 10);
        
        // Wait for publishers to initialize
        sleep(1);
    }
    
    void moveArm() {
        std_msgs::Float64 joint_command;
        
        // Move joint 1 to 45 degrees (0.785 radians)
        joint_command.data = 0.785;
        joint1_pub_.publish(joint_command);
        sleep(2);
        
        // Move joint 2 to 30 degrees (0.524 radians)
        joint_command.data = 0.524;
        joint2_pub_.publish(joint_command);
        sleep(2);
        
        // Return to home position
        joint_command.data = 0.0;
        joint1_pub_.publish(joint_command);
        joint2_pub_.publish(joint_command);
        
        ROS_INFO("Arm movement completed!");
    }
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "arm_controller");
    
    ArmController controller;
    controller.moveArm();
    
    return 0;
}`,

    hand: `#include <ros/ros.h>
#include <std_msgs/Float64.h>
#include <unistd.h>

class HandController {
private:
    ros::NodeHandle nh_;
    ros::Publisher finger1_pub_;
    ros::Publisher finger2_pub_;
    ros::Publisher thumb_pub_;

public:
    HandController() {
        // Initialize publishers for finger control
        finger1_pub_ = nh_.advertise<std_msgs::Float64>("/robot_hand/finger1_position_controller/command", 10);
        finger2_pub_ = nh_.advertise<std_msgs::Float64>("/robot_hand/finger2_position_controller/command", 10);
        thumb_pub_ = nh_.advertise<std_msgs::Float64>("/robot_hand/thumb_position_controller/command", 10);
        
        // Wait for publishers to initialize
        sleep(1);
    }
    
    void controlHand() {
        std_msgs::Float64 finger_command;
        
        // Open hand
        finger_command.data = 0.0;
        finger1_pub_.publish(finger_command);
        finger2_pub_.publish(finger_command);
        thumb_pub_.publish(finger_command);
        sleep(2);
        
        // Close fingers to grasp
        finger_command.data = 1.2;
        finger1_pub_.publish(finger_command);
        finger2_pub_.publish(finger_command);
        finger_command.data = 0.3;
        thumb_pub_.publish(finger_command);
        sleep(2);
        
        // Open hand again
        finger_command.data = 0.0;
        finger1_pub_.publish(finger_command);
        finger2_pub_.publish(finger_command);
        thumb_pub_.publish(finger_command);
        
        ROS_INFO("Hand grasping completed!");
    }
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "hand_controller");
    
    HandController controller;
    controller.controlHand();
    
    return 0;
}`,

    turtlebot: `#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <unistd.h>

class TurtleBotController {
private:
    ros::NodeHandle nh_;
    ros::Publisher vel_pub_;

public:
    TurtleBotController() {
        // Initialize publisher for velocity commands
        vel_pub_ = nh_.advertise<geometry_msgs::Twist>("/cmd_vel", 10);
        
        // Wait for publisher to initialize
        sleep(1);
    }
    
    void moveTurtleBot() {
        geometry_msgs::Twist move_cmd;
        
        // Move forward
        move_cmd.linear.x = 0.2;
        move_cmd.angular.z = 0.0;
        vel_pub_.publish(move_cmd);
        sleep(2);
        
        // Turn left
        move_cmd.linear.x = 0.0;
        move_cmd.angular.z = 0.5;
        vel_pub_.publish(move_cmd);
        sleep(2);
        
        // Move forward again
        move_cmd.linear.x = 0.2;
        move_cmd.angular.z = 0.0;
        vel_pub_.publish(move_cmd);
        sleep(2);
        
        // Stop
        move_cmd.linear.x = 0.0;
        move_cmd.angular.z = 0.0;
        vel_pub_.publish(move_cmd);
        
        ROS_INFO("TurtleBot movement completed!");
    }
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "turtlebot_controller");
    
    TurtleBotController controller;
    controller.moveTurtleBot();
    
    return 0;
}`
  }
};
