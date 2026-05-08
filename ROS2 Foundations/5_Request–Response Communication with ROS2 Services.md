## 🔄 Request–Response Communication with ROS2 Services

## 📍 Level: Beginner–Intermediate  
## 📚 Topic: Services, Clients, Request–Response  

---

## 🧠 1. Core Concept: What is a Service?

A **ROS2 service** is used when you want to:

> 👉 Send a command
>  👉 And get an immediate response

This is called **request → response communication**.

------

### 🔑 Key Idea

> Topics = continuous control (streaming)
>  Services = **change robot behavior instantly**

------

## 🤖 2. Real Robot Context (MentorPi LiDAR System)

In this module, you are controlling a **LiDAR-based robot behavior system**.

The robot has a built-in **LiDAR application (game system)** that runs different modes.

------

## 🎮 3. System Overview

You will control this system using services:

| Action          | Service                  |
| --------------- | ------------------------ |
| Enter LiDAR App | `/lidar_app/enter`       |
| Set Mode        | `/lidar_app/set_running` |

------

## ⚙️ 4. Step 1 — Enter the LiDAR Application

Before controlling modes, you must activate the system:

```
ros2 service call /lidar_app/enter std_srvs/srv/Trigger {}
```

------

### 🧠 What this does

- Starts LiDAR control application
- Initializes robot behavior system
- Prepares robot for mode switching

------

## 🎮 5. Step 2 — Understanding Modes

The robot supports **3 behavioral modes**:

| Mode | Behavior           |
| ---- | ------------------ |
| 0    | Idle / Stop        |
| 1    | Obstacle Avoidance |
| 2    | Target Following   |

------

## 🧩 6. Changing Robot Mode

All modes are controlled using this service:

```
/lidar_app/set_running
``` id="srv2"

Message type:
```

interfaces/srv/SetInt64

```
---

## 🧠 7. Mode Control Commands

---

### 🟡 Mode 0 → Stop Robot

```bash id="mode0"
ros2 service call /lidar_app/set_running interfaces/srv/SetInt64 "{data: 0}"
```

👉 Robot stops all motion

------

### 🟢 Mode 1 → Obstacle Avoidance

```
ros2 service call /lidar_app/set_running interfaces/srv/SetInt64 "{data: 1}"
```

👉 Robot:

- Moves automatically
- Avoids obstacles using LiDAR

------

### 🔵 Mode 2 → Target Following

```
ros2 service call /lidar_app/set_running interfaces/srv/SetInt64 "{data: 2}"
```

👉 Robot:

- Detects target
- Follows object/person

------

## 🔄 8. Full System Thinking

You (Service Client)
        │
        ▼
/lidar_app/set_running
        │
        ▼
Robot Behavior Controller
        │
        ▼
LiDAR-Based Motion System
        │
        ├── Mode 0 → Stop
        ├── Mode 1 → Avoid Obstacles
        └── Mode 2 → Follow Target



---

## 🧠 9. Why This is a Service (Not Topic)

This is NOT a topic because:

❌ You are not streaming data  
❌ You are not controlling continuously  

Instead:

✔ You are **changing system state**  
✔ You get **instant response behavior switch**  
✔ You send **one command → robot reacts**

---

## ⚙️ 10. Python Service Client (Conceptual)

Now imagine doing the same in code.

---

## 🧪 11. Your Task

You will build a ROS2 node that:

- Calls `/lidar_app/set_running`
- Sends a mode (0, 1, or 2)
- Prints confirmation

---

## 🧩 12. Code Template (Incomplete on Purpose)

``` id="flow1"
import rclpy
from rclpy.node import Node
from interfaces.srv import SetInt64


class LidarModeClient(Node):
    def __init__(self):
        super().__init__('lidar_mode_client')

        # TODO 1: Create service client
        self.client = None

    def send_mode(self, mode):
        # TODO 2: Create request
        request = None

        request.data = mode

        # TODO 3: Call service
        future = None

        # Wait for response
        rclpy.spin_until_future_complete(self, future)

        self.get_logger().info(f"Mode {mode} activated")


def main(args=None):
    rclpy.init(args=args)

    node = LidarModeClient()

    # TODO 4: Try different modes
    node.send_mode(1)  # obstacle avoidance

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

------

## 🧠 13. Hints

### ✅ Create Client

```
self.create_client(SetInt64, '/lidar_app/set_running')
```

------

### ✅ Create Request

```
SetInt64.Request()
```

------

### ✅ Call Service

```
self.client.call_async(request)
```

------

## 🧪 14. Mini Experiments

### 🟢 Easy

- Switch between mode 0 and 1

------

### 🟡 Medium

- Automatically switch modes every 5 seconds

------

### 🔴 Advanced

- Build “mode scheduler” (0 → 1 → 2 loop)
