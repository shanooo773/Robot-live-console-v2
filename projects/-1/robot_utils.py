# robot_utils.py

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import LaserScan
import threading


def _start_spin(node):
    rclpy.spin(node)


class RobotMover(Node):
    def __init__(self):
        if not rclpy.ok():
            rclpy.init()

        super().__init__('robot_mover')

        self.publisher = self.create_publisher(
            TwistStamped,
            '/real_robot/real_diff_controller/cmd_vel',
            10
        )

        threading.Thread(target=_start_spin, args=(self,), daemon=True).start()

    def _publish(self, lin=0.0, ang=0.0):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = lin
        msg.twist.angular.z = ang
        self.publisher.publish(msg)

    def forward(self, speed=0.3):
        self._publish(lin=speed)

    def backward(self, speed=0.3):
        self._publish(lin=-speed)

    def left(self, speed=0.5):
        self._publish(ang=speed)

    def right(self, speed=0.5):
        self._publish(ang=-speed)

    def stop(self):
        self._publish(0.0, 0.0)


class LidarHelper(Node):
    def __init__(self):
        if not rclpy.ok():
            rclpy.init()

        super().__init__('lidar_helper')

        self.scan = None
        self.lock = threading.Lock()

        self.create_subscription(
            LaserScan,
            '/scan',
            self._callback,
            10
        )

        threading.Thread(target=_start_spin, args=(self,), daemon=True).start()

    def _callback(self, msg):
        with self.lock:
            self.scan = msg

    def get_front_distance(self):
        with self.lock:
            if self.scan is None:
                return float('inf')
            return min(self.scan.ranges)
