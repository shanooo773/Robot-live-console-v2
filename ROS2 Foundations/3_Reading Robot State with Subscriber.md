## 👂 Reading Robot State with ROS2 Subscribers

## 📍 Level: Beginner  
## 📚 Topic: Subscribers, Topics, Odometry  

---

## 🧠 1. Core Concept: Subscribers

In ROS2, a **subscriber** listens to data published on a topic.

- Publisher → sends data  
- Subscriber → receives data  

---

### 🔑 Key Idea

> If publishers **control** the robot, subscribers help you **understand** the robot.

---

## 🔄 2. What You Did Before

- You **published commands** to move the robot  
- You controlled motion using `/controller/cmd_vel`

But…

👉 How do you know:
- Where the robot is?  
- How fast it is moving?  

---

## 🚀 3. What You Will Do Now

You will:

- Subscribe to robot state  
- Read **odometry data**  
- Print robot position in real time  

---

## 🤖 4. The Topic You Will Use 

```
/odom_raw
```

---

## 📦 5. Message Type

```
nav_msgs/Odometry
```

---

## 🧠 6. What is Odometry?

Odometry gives you:

- 📍 Position (x, y)
- 🔄 Orientation (rotation)
- ⚡ Velocity

---

### 📊 Simplified Structure

```
pose:
position:
x
y
z

twist:
linear velocity
angular velocity
```

---

## 🔄 7. Data Flow

Robot Sensors
 │
 ▼
 /odom_raw (Publisher)
 │
 ▼
 Your Node (Subscriber)
 │
 ▼
 You see robot state 📡

---

## 🧪 8. Your Task

Create a node that:

- Subscribes to `/odom_raw`
- Extracts robot position
- Prints `(x, y)` in real time

---

## 🧩 9. Code Template (Complete the Missing Parts)

```python id="z9g2tq"
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class OdomSubscriber(Node):
    def __init__(self):
        super().__init__('odom_subscriber')

        # TODO 1: Create subscriber to '/odom_raw'
        self.subscription = None

    def odom_callback(self, msg):
        # TODO 2: Extract x and y position
        x = None
        y = None

        # Print position
        self.get_logger().info(f"Robot Position -> x: {x:.2f}, y: {y:.2f}")


def main(args=None):
    rclpy.init(args=args)

    node = OdomSubscriber()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## 🧠 10. Hints

### ✅ Creating Subscriber

```
self.create_subscription(
    Odometry,
    '/odom_raw',
    self.odom_callback,
    10
)
```

### ✅ Extract Position

```
msg.pose.pose.position.x
msg.pose.pose.position.y
```

## ▶️ 11. How to Run

```
colcon build
source install/setup.bash

ros2 run exercise_2 odom_subscriber
```

## 📡 12. Expected Output

```
Robot Position -> x: 0.12, y: -0.03
Robot Position -> x: 0.15, y: -0.05
...
```

## 🧪 13. Mini Exercises

### 🟢 Easy

- Print only `x` position

------

### 🟡 Medium

- Print velocity from `twist`

------

### 🔴 Advanced

- Detect when robot is stopped (velocity ≈ 0)
