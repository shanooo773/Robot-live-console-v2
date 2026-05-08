# 🤖 ROS2 Foundations

# Table of Contents

[🚀 Control the Robot with Topics](#-control-the-robot-with-topics)

[🧠 1. What’s Going On Here?](#-1-whats-going-on-here)

[📡 2. How Do We Talk to the Robot?](#-2-how-do-we-talk-to-the-robot)

[🤖 3. Your Robot is Already Running](#-3-your-robot-is-already-running)

[🎯 4. Your Goal](#-4-your-goal)

[⚙️ 5. How Movement Works](#%EF%B8%8F-5-how-movement-works)

[🚗 6. Your First Command](#-6-your-first-command)

[👀 7. See What Robot is Doing](#-7-see-what-robot-is-doing)

[🔄 8. What Just Happened (Super Simple)](#-8-what-just-happened-super-simple)

[🧪 9. Try It Yourself](#-9-try-it-yourself)

[🏁 10. What You Learned](#-10-what-you-learned)

[🚀 What’s Next?](#-whats-next)



## 🚀 Control the Robot with Topics

📍 **Level:** Absolute Beginner
 📚 **Topic:** How to Send Commands to a Robot

------

## 🧠 1. What’s Going On Here?

Right now, you are connected to a **real robot system** using AnyBot.

Your goal is simple:

👉 **Send a command → Robot moves**

`Note: Execute all commands in Terminal/Command Line Interface`

------

## 📡 2. How Do We Talk to the Robot?

Robots don’t understand normal language.
 They use something called **topics**.

### 💡 Think of it like WhatsApp:

- You send a message → 📤
- Someone receives it → 📥

In ROS2:

- You send data → **Publisher**
- Robot receives it → **Subscriber**

### 🔑 Simple Idea

```
You send command → Robot receives → Robot moves
```

## 🤖 3. Your Robot is Already Running

Good news — you don’t need to start anything.

The robot is already:

- ✅ Running
- ✅ Listening for commands
- ✅ Ready to move

### 📡 Important Channels (Topics)

| Topic                           | What it does           |
| ------------------------------- | ---------------------- |
| `/controller/cmd_vel`           | Send movement commands |
| `/odom_raw`                     | See robot position     |
| `/joint_states`                 | See robot joints       |
| `/ros_robot_controller/imu_raw` | Sensor data            |

👉 For now, we only care about:

```
/controller/cmd_vel
```

------

## 🎯 4. Your Goal

You will:

- Send a command
- Make the robot move
- See what happens

------

## ⚙️ 5. How Movement Works

We send a **movement message** to the robot.

This message is called:

```
Twist
```

------

### 🧩 What Does It Mean?

It has two parts:

#### ➤ Move Forward / Backward

```
linear.x
```

#### ➤ Turn Left / Right

```
angular.z
```

------

### 🧠 Simple Mapping

| Action       | What to change |
| ------------ | -------------- |
| Move forward | `linear.x`     |
| Turn         | `angular.z`    |

------

## 🚗 6. Your First Command

### ▶️ Move Forward

Run this in terminal:

```
ros2 topic pub /controller/cmd_vel geometry_msgs/Twist "{
linear: {x: 0.2, y: 0.0, z: 0.0},
angular: {z: 0.0}
}"
```

👉 What happens?

- Robot moves forward slowly

`Note: The command Move Forward should be stopped / canceled before running another one. All previous commands should be stopped before running new one`

### Stop the Command

`Press CTRL + C in terminal to stop the command`

------

### 🔄 Rotate (Turn)

```
ros2 topic pub /controller/cmd_vel geometry_msgs/Twist "{
linear: {x: 0.0, y: 0.0, z: 0.0},
angular: {z: 0.5}
}"
```

👉 What happens?

- Robot rotates in place

------

## 👀 7. See What Robot is Doing

Now let’s **listen to the robot**.

Run:

```
ros2 topic echo /odom_raw
```

------

### 🧠 What is this?

The robot is telling you:

- Where it is
- How fast it’s moving

👉 You are now **receiving data from the robot**

------

## 🔄 8. What Just Happened (Super Simple)

```
You send command → Robot moves → Robot sends data back → You see it
```

------

## 🧪 9. Try It Yourself

### 🟢 Easy

- Move slowly → `0.1`
- Move faster → `0.5`

------

### 🟡 Medium

- Move forward + turn at the same time

------

### 🔴 Advanced

- Make a circle

👉 Hint:

```
Use BOTH linear.x AND angular.z
```

------

## 🏁 10. What You Learned

- You can control a robot using simple commands
- You don’t need to write code yet
- Sending data = controlling
- Receiving data = understanding

------

## 🚀 What’s Next?

Right now, you are typing commands manually.

👉 Next, you will:

- Create your **own program (node)**
- Make the robot move automatically
- Stop typing commands again and again
