## 🛠️ Setting Up Your ROS2 Workspace and First Package (Python)

## 📍 Level: Beginner  
## 📚 Topic: Workspaces, Packages, ROS2 Structure  

---

## 🧠 1. Core Concept: What is a Workspace?

A **ROS2 workspace** is your development environment.

It is where:
- You write code  
- You build packages  
- You run your robot applications  

---

### 🔑 Key Idea

> A workspace is a **container for ROS2 projects**

---

## 📦 2. Workspace Structure

A typical workspace looks like: 

```
ros2_ws/
│
├── src/ ← your packages go here
├── build/ ← build files (auto-generated)
├── install/ ← compiled packages
└── log/ ← build logs
```

---

### 🧠 Important

- You only create `src/`
- Everything else is created by ROS2

---

## 🚀 3. Creating a Workspace

```bash id="ws_create"
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

## ⚙️ 4. Building the Workspace

```
colcon build
```

### 🔄 After Build

```
source install/setup.bash
```

### 🔑 Why Source?

> It tells your system:
> “Use packages from this workspace”

## 📦 5. What is a Package?

A **package** is a unit of functionality in ROS2.

Examples:

- Robot controller
- Sensor processing
- Navigation system

------

### 🔑 Key Idea

> Workspace = container
>  Package = actual code

------

## 🛠️ 6. Creating Your First Package

Go inside `src/`:

```
cd ~/ros2_ws/src
```

### Create Python Package

```
ros2 pkg create --build-type ament_python my_first_package
```

### 🧠 What This Does

Creates:

```
my_first_package/
├── my_first_package/
├── package.xml
├── setup.py
└── setup.cfg
``` id="pkg_struct"
```

---

## 🔍 7. Important Files

---

### 📄 package.xml

- Defines dependencies  
- Metadata about package  

---

### ⚙️ setup.py

- Python entry points  
- Defines executables  

---

### 📁 my_first_package/

- Your Python code lives here  

---

## ▶️ 8. Build Your Package

```bash id="pkg_build"
cd ~/ros2_ws
colcon build
source install/setup.bash
```

## 🧪 9. Verify Package

```
ros2 pkg list | grep my_first_package
```

## 🚀 10. Run Your Package (Later)

You will eventually run nodes like:

```
ros2 run my_first_package my_node
```

## ⚠️ 11. Common Mistakes

### ❌ Forgetting to source

```
ros2 run ...   # fails
```

✅ Fix:

```
source install/setup.bash
```

### ❌ Creating package outside src/

Packages MUST be inside:

```
ros2_ws/src/
```

