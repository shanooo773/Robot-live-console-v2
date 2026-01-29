# user_code.py

import rclpy
from robot_utils import RobotMover, LidarHelper
import time


robot = RobotMover()
lidar = LidarHelper()

FORWARD_TIME = 10.0   # seconds
TURN_TIME = 2.0       # seconds (90-degree turn, tune this)
SIDES = 4

while lidar.get_front_distance() > 1.0:
    robot.forward()

