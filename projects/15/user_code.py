from robot_utils import RobotMover, LidarHelper



robot = RobotMover()
lidar = LidarHelper()


while True:
    robot.forward()