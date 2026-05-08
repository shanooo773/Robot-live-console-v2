## 🧠 From Topics to Code: Your First Robot Controller

## 📍 Level: Beginner  
## 📚 Topic: ROS2 Nodes, Publishers, Timers  

# Table of Contents

[🧠 Core Concept: What is a Node?](#-core-concept-what-is-a-node)

[🔄 What You Did Before](#-what-you-did-before)

[🚀 What You Will Do Now](#-what-you-will-do-now)

[⚙️ How It Works (Very Simple)](#%EF%B8%8F-how-it-works-very-simple)

[🧩 Final Code (Fully Completed)](#-final-code-fully-completed)

[🎯 Super Simple Explanation](#-super-simple-explanation)

[▶️ How to Run](#%EF%B8%8F-how-to-run)

[🧪 Mini Challenges (Fun Mode 🎮)](#-mini-challenges-fun-mode-)



---

# 🧠 Core Concept: What is a Node?

Think of a **robot like a human body**.

- Eyes → see
- Brain → think
- Hands → move

In ROS2:

👉 Each part is a **node**

A **Node** is like a single person in the neighborhood who is an expert at **one** thing.

- One node might be the "Eyes" (the camera).
- One node might be the "Legs" (the motors).
- One node might be the "Brain" (the logic).

![](../assets/module_2/ros2_node_concept.png)

------

### 💡 Simple Meaning

A **node = a small program that does one job**

Examples:

- One node moves the robot 🚗
- One node reads sensors 👀
- One node processes camera 📸

------

# 🔄 What You Did Before

Before, you told the robot what to do **manually**, like this:

```
ros2 topic pub /controller/cmd_vel ...
```

👉 That’s like pressing buttons on a remote control 🎮

------

# 🚀 What You Will Do Now

Now you will make a **robot program** that:

1. Moves forward automatically ⬆️
2. Waits for 3 seconds ⏱️
3. Stops 🛑

👉 No manual control needed!

------

# ⚙️ How It Works (Very Simple)

Your program will:

1. Create a **node (robot brain)**
2. Send movement commands
3. Keep checking time
4. Stop after 3 seconds

------

# 🧩 Final Code (Fully Completed)

Here is your finished program 👇

```
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class MoveForwardNode(Node):
    def __init__(self):
        super().__init__('move_forward_node')

        # Create publisher (this sends commands to robot)
        self.publisher_ = self.create_publisher(Twist, '/controller/cmd_vel', 10)

        # Run every 0.1 seconds
        self.timer = self.create_timer(0.1, self.timer_callback)

        # Save start time
        self.start_time = self.get_clock().now()

    def timer_callback(self):
        msg = Twist()

        # Move forward
        msg.linear.x = 0.2

        current_time = self.get_clock().now()
        elapsed = (current_time - self.start_time).nanoseconds / 1e9

        if elapsed < 3.0:
            # Keep moving
            self.publisher_.publish(msg)
        else:
            # Stop the robot
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.publisher_.publish(msg)

            self.get_logger().info("Stopping robot")
            self.timer.cancel()


def main(args=None):
    rclpy.init(args=args)

    node = MoveForwardNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

# 🎯 Super Simple Explanation

👉 Every **0.1 second**, the robot asks:

> "Should I keep moving?"

- If time < 3 seconds → keep moving 🚗
- If time ≥ 3 seconds → stop 🛑

![](../assets/module_2/ros2_communication.png)

------

# ▶️ How to Run

```
colcon build
source install/setup.bash
ros2 run exercise_1 move_forward_node
```

------

# 🧪 Mini Challenges (Fun Mode 🎮)

### 🟢 Easy

Change:

```
3.0 → 5.0
```

👉 Robot moves longer

------

### 🟡 Medium

After moving forward:
 👉 Make robot turn (use `angular.z`)

------

### 🔴 Advanced

Make robot move in a **square ⬜**
