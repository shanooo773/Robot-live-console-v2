## ⚙️ Creating Your First ROS2 C++ Package

## 📍 Level: Beginner–Intermediate  
## 📚 Topic: C++ Packages, ament_cmake, Build System  

---

## 🧠 1. Why C++ in ROS2?

So far, you have used Python (`rclpy`).

But ROS2 also supports C++ (`rclcpp`).

---

### 🔑 Key Idea

> Python = easy & fast to develop  
> C++ = fast & efficient at runtime  

---

### 🤖 When to Use C++?

- Real-time control  
- High-frequency sensors (LiDAR, cameras)  
- Performance-critical systems  

---

## 📦 2. Package Types in ROS2

| Type   | Build System   | Language |
| ------ | -------------- | -------- |
| Python | `ament_python` | Python   |
| C++    | `ament_cmake`  | C++      |

---

## 🚀 3. Create a C++ Package

Go to your workspace:

```bash id="cpp_create"
cd ~/ros2_ws/src
```

### Create Package

```
ros2 pkg create --build-type ament_cmake my_cpp_package
```

------

## 📁 4. Package Structure

```
my_cpp_package/
├── CMakeLists.txt
├── package.xml
├── include/
└── src/

```

## 🧠 5. Key Files

### 📄 CMakeLists.txt

- Build configuration  
- Compiles C++ code  

### 📄 package.xml

- Dependencies  
- Metadata  

### 📁 src/

- Your `.cpp` files  

## 🧪 6. Create Your First C++ Node

Create a file:

``` id="cpp_struct2"
cd ros2_ws/src
touch simple_node.cpp
```

------

## 🧩 7. Basic C++ Node Code

```
#include "rclcpp/rclcpp.hpp"

class SimpleNode : public rclcpp::Node
{
public:
    SimpleNode() : Node("simple_node")
    {
        RCLCPP_INFO(this->get_logger(), "Hello from C++ node!");
    }
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SimpleNode>());
    rclcpp::shutdown();
    return 0;
}
```

------

## ⚙️ 8. Update CMakeLists.txt

Add this:

```
find_package(rclcpp REQUIRED)

add_executable(simple_node src/simple_node.cpp)

ament_target_dependencies(simple_node rclcpp)

install(TARGETS
  simple_node
  DESTINATION lib/${PROJECT_NAME}
)
```

------

## ⚙️ 9. Update package.xml

Add dependency:

```
<depend>rclcpp</depend>
```

------

## ▶️ 10. Build Package

```
cd ~/ros2_ws
colcon build
source install/setup.bash
```

------

## 🚀 11. Run Node

```
ros2 run my_cpp_package simple_node
```

------

## 📡 12. Expected Output

```
[INFO] [simple_node]: Hello from C++ node!
```
