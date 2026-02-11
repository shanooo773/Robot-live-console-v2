#!/usr/bin/env python3

from robot_utils import RobotMover, LidarHelper


robot = RobotMover()


while True:
    robot.forward()
    robot.backward()
