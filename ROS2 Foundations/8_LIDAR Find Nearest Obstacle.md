# LiDAR: Find Nearest Obstacle

## 📍 Level: Beginner

## 📚 Topic: Sensor Processing → LaserScan Analysis

------

## 🧠 1. Core Concept: What is LaserScan?

A LIDAR publishes data as:

```
sensor_msgs/LaserScan
```

It contains an array:

```
msg.ranges = [r1, r2, r3, ..., rN]
```

Each value represents distance to an obstacle at a specific angle.

------

### ⚠️ Important Reality

Real LIDAR data is messy:

| Value         | Meaning      |
| ------------- | ------------ |
| `inf`         | No detection |
| `nan`         | Sensor error |
| `< range_min` | Invalid      |
| `> range_max` | Invalid      |

👉 You MUST filter before using it.

------

## 🏭 2. Industry Context

This exact pattern is used in:

- 🤖 iRobot Roomba → stop when object is close
- 🚗 Autonomous forklifts → collision avoidance
- 🦾 Boston Dynamics robots → reactive navigation
- 🧭 Nav2 costmaps → obstacle layer generation

------

## 🎯 3. Problem Statement

Create a node that:

- Reads LIDAR scan data
- Finds nearest obstacle
- Publishes distance

------

## 🧩 4. Requirements Breakdown

| Requirement  | Value                        |
| ------------ | ---------------------------- |
| Subscribe    | `/scan`                      |
| Message type | `LaserScan`                  |
| Publish      | `/nearest_obstacle_distance` |
| Output type  | `Float32`                    |
| Logic        | minimum valid range          |
| Extra        | log distance + angle         |

------

## 🧩 5. Full Working Code (Python)

```
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32
import math


class LidarProcessor(Node):
    def __init__(self):
        super().__init__('lidar_processor')

        # Publisher
        self.publisher_ = self.create_publisher(
            Float32,
            '/nearest_obstacle_distance',
            10
        )

        # Subscriber
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.get_logger().info("LIDAR Processor Ready")

    def scan_callback(self, msg: LaserScan):

        min_distance = float('inf')
        min_index = -1

        # Filter and find minimum valid range
        for i, r in enumerate(msg.ranges):

            # Skip invalid readings
            if (
                math.isnan(r)
                or math.isinf(r)
                or r <= msg.range_min
                or r >= msg.range_max
            ):
                continue

            if r < min_distance:
                min_distance = r
                min_index = i

        # No valid data case
        if min_index == -1:
            self.get_logger().warn("No valid LIDAR readings found")
            return

        # Compute angle
        angle = msg.angle_min + min_index * msg.angle_increment

        # Log result
        self.get_logger().info(
            f"Nearest Obstacle: {min_distance:.2f} m at {angle:.2f} rad"
        )

        # Publish result
        out_msg = Float32()
        out_msg.data = min_distance
        self.publisher_.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)

    node = LidarProcessor()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

------

## ▶️ 6. How to Run

```
colcon build
source install/setup.bash
ros2 run <your_package> lidar_processor
```

------

## 📡 7. Output Verification

### Distance output:

```
ros2 topic echo /nearest_obstacle_distance
data: 1.42
```

------

### Logs:

```
LIDAR Processor Ready
Nearest Obstacle: 1.42 m at 0.35 rad
```

------

## ⚠️ 8. Common Pitfalls

### ❌ Not filtering invalid values

```
min(msg.ranges)  # WRONG
```

------

### ❌ Ignoring NaN/inf

👉 This breaks real robot systems

------

### ❌ Wrong index handling

Must track index to compute angle:

```
angle = msg.angle_min + index * msg.angle_increment
```

------

## 🧠 9. Deep Understanding Notes

### 🔹 Why filtering matters

LIDAR raw data ALWAYS contains noise:

```
Valid → obstacle
inf → nothing there
nan → sensor error
```

------

### 🔹 Angle computation

Each beam corresponds to:

```
angle = start + i * step
```

This is how robots build spatial awareness.

------

### 🔹 Real Robotics Pipeline

```
LaserScan → Filter → Min Distance → Safety Decision
```

------

### 🔹 Nav2 Connection

Nav2 uses this same idea inside:

- Costmap obstacle layer
- Inflation layer
- Collision avoidance