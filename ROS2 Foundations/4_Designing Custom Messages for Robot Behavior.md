## 🧩 Designing Custom Messages for Robot Behavior

## 📍 Level: Intermediate  
## 📚 Topic: Custom Messages, ROS2 Interfaces, Data Design  

---

## 🧠 1. Core Concept: What is a Message?

In ROS2, a **message** defines the structure of data exchanged between nodes.

Examples you’ve already used:

- `geometry_msgs/Twist` → velocity  
- `nav_msgs/Odometry` → robot state  

---

### 🔑 Key Idea

> A message is a **data contract** between nodes

It defines:
- What data is sent  
- In what format  
- With what meaning  

---

## 🧠 2. Why Custom Messages?

Standard messages are useful, but limited.

What if you want to send:

- A full robot command (speed + duration)?  
- A complex behavior (like square movement)?  
- Multiple parameters together?  

👉 That’s where **custom messages** come in.

---

### ❌ Without Custom Message

You would need:
- Multiple topics  
- Complex coordination  
- Hard-to-manage logic  

---

### ✅ With Custom Message

You can send:

Move forward 0.2 m/s for 3 seconds

as **one structured message**

---

## 🧩 3. Designing Our Message

We will create a custom message:

`SquareCommand.msg`

---

### 📦 Message Definition

``` id="msgdef"
float64 linear_speed
float64 angular_speed
float64 side_duration
int32 repetitions
```

### 🧠 Meaning

| Field           | Purpose           |
| --------------- | ----------------- |
| `linear_speed`  | Forward speed     |
| `angular_speed` | Turning speed     |
| `side_duration` | Time per side     |
| `repetitions`   | Number of squares |

## ⚙️ 4. Creating Custom Message (ROS2)

### Step 1: Create msg folder

```
mkdir msg
```

### Step 2: Add file

```
msg/SquareCommand.msg
```

### Step 3: Update `CMakeLists.txt`

```
find_package(exercise_3_custom_message REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)

find_package(rosidl_default_generators REQUIRED)
find_package(${PROJECT_NAME} REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SquareCommand.msg"
)
```

### Step 4: Update `package.xml`

```
<build_depend>rosidl_default_generators</build_depend>

<exec_depend>rosidl_default_runtime</exec_depend>

<member_of_group>rosidl_interface_packages</member_of_group>
```

### Step 5: Build

```
colcon build
source install/setup.bash
```

## 🧠 5. What Happens Internally?

ROS2 generates:

- Python classes
- C++ classes
- Serialization logic

👉 Your `.msg` becomes usable like any built-in message

## 🚀 6. Applying to MentorPi: Square Movement

Now we use this message to control the robot.

## 🎯 Goal

Create a node that:

- Subscribes to `/square_command`
- Receives `SquareCommand`
- Moves robot in a square

## 🔄 7. Behavior Logic

A square has 4 sides:

Forward → Turn → Forward → Turn → ...

## 🧩 8. Code Template (Incomplete)

```
#!/usr/bin/env python3

import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from exercise_3_custom_message.msg import SquareCommand


class SquareController(Node):
    def __init__(self):
        super().__init__('square_controller')

        # Publisher to robot
        self.cmd_pub = self.create_publisher(
            Twist,
            '/controller/cmd_vel',
            10
        )

        # Subscriber for square command
        self.sub = self.create_subscription(
            SquareCommand,
            '/square_command',
            self.command_callback,
            10
        )

    def command_callback(self, msg):
        self.get_logger().info("Starting square movement")

        # ✅ Extract parameters
        linear_speed = msg.linear_speed
        angular_speed = msg.angular_speed
        duration = msg.side_duration
        repetitions = msg.repetitions

        twist = Twist()

        for _ in range(repetitions):
            for _ in range(4):  # 4 sides of square

                # 🔹 Move forward
                twist.linear.x = linear_speed
                twist.angular.z = 0.0

                start_time = time.time()
                while time.time() - start_time < duration:
                    self.cmd_pub.publish(twist)
                    time.sleep(0.1)

                # 🔹 Stop before turning
                twist.linear.x = 0.0
                self.cmd_pub.publish(twist)
                time.sleep(0.5)

                # 🔹 Rotate 90 degrees
                twist.angular.z = angular_speed

                # Time to rotate ~90 degrees
                turn_time = 1.57 / angular_speed  # radians / rad/s

                start_time = time.time()
                while time.time() - start_time < turn_time:
                    self.cmd_pub.publish(twist)
                    time.sleep(0.1)

                # 🔹 Stop after turn
                twist.angular.z = 0.0
                self.cmd_pub.publish(twist)
                time.sleep(0.5)

        self.get_logger().info("Square movement complete")


def main(args=None):
    rclpy.init(args=args)

    node = SquareController()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## 🧠 9. Hints

### ✅ Subscriber

```
self.create_subscription(
    SquareCommand,
    '/square_command',
    self.command_callback,
    10
)
```

### ✅ Extract Data

```
msg.linear_speed
msg.angular_speed
msg.side_duration
```

### ✅ Square Logic Idea

```
for _ in range(4):
    # move forward
    # sleep(duration)

    # rotate 90 deg
    # sleep(turn_time)
```

## ▶️ 10. Sending Command

```
ros2 topic pub /square_command exercise_3_custom_message/msg/SquareCommand "{
  linear_speed: 0.2,
  angular_speed: 0.5,
  side_duration: 2.0,
  repetitions: 1
}"
```

## 📡 11. Expected Behavior

- Robot moves in a square
- Each side runs for given duration
- Turns at corners