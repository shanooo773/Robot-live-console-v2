# user_code.py

import rclpy
from robot_utils import RobotMover, LidarHelper
import time


robot = RobotMover()
lidar = LidarHelper()

while lidar.get_front_distance() > 1.0:
    robot.forward()