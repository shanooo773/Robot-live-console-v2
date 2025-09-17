import { Box, Button, Menu, MenuButton, MenuList, MenuItem, Text, Spinner } from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { getAvailableRobots } from "../api";

const RobotSelector = ({ robot, onSelect }) => {
  const [robots, setRobots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fallback robot names for backward compatibility
  const FALLBACK_ROBOT_NAMES = {
    arm: "Robot Arm",
    hand: "Robot Hand", 
    turtlebot: "TurtleBot3"
  };

  useEffect(() => {
    const fetchRobots = async () => {
      try {
        setLoading(true);
        const data = await getAvailableRobots();
        
        // Use the new robot list format if available, otherwise fall back to old format
        if (data.robots && Array.isArray(data.robots) && data.robots.length > 0) {
          // Check if robots array contains objects with id, name, type
          if (typeof data.robots[0] === 'object' && data.robots[0].id) {
            setRobots(data.robots);
          } else {
            // Old format: convert robot types to robot objects
            const robotObjects = data.robots.map((type, index) => ({
              id: index + 1,
              name: FALLBACK_ROBOT_NAMES[type] || type,
              type: type
            }));
            setRobots(robotObjects);
          }
        } else {
          // Fallback to hardcoded robots
          setRobots([
            { id: 1, name: "TurtleBot3", type: "turtlebot" },
            { id: 2, name: "Robot Arm", type: "arm" },
            { id: 3, name: "Robot Hand", type: "hand" }
          ]);
        }
      } catch (err) {
        console.error("Error fetching robots:", err);
        setError("Failed to load robots");
        // Fallback to hardcoded robots
        setRobots([
          { id: 1, name: "TurtleBot3", type: "turtlebot" },
          { id: 2, name: "Robot Arm", type: "arm" },
          { id: 3, name: "Robot Hand", type: "hand" }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchRobots();
  }, []);

  // Find current robot by ID or type
  const getCurrentRobot = () => {
    if (typeof robot === 'number') {
      // robot is an ID
      return robots.find(r => r.id === robot);
    } else {
      // robot is a type (backward compatibility)
      return robots.find(r => r.type === robot);
    }
  };

  const currentRobot = getCurrentRobot();

  return (
    <Box mb={2} minW="150px">
      <Text mb={2} fontSize="lg" color="white">
        Robot:
      </Text>
      <Menu isLazy>
        <MenuButton 
          as={Button} 
          variant="outline" 
          color="gray.400" 
          bg="#110f1c" 
          _hover={{ bg: "#1e1e2e" }}
          disabled={loading}
        >
          {loading ? (
            <Spinner size="sm" />
          ) : (
            currentRobot?.name || "Select Robot"
          )}
        </MenuButton>
        <MenuList bg="#110f1c" border="1px solid #333">
          {robots.map((robotItem) => (
            <MenuItem
              key={robotItem.id}
              color={robotItem.id === robot || robotItem.type === robot ? "blue.400" : "gray.400"}
              bg={robotItem.id === robot || robotItem.type === robot ? "#1e1e2e" : "transparent"}
              _hover={{
                color: "blue.400",
                bg: "#1e1e2e",
              }}
              onClick={() => onSelect(robotItem.id, robotItem)}
            >
              {robotItem.name}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
      {error && (
        <Text color="red.400" fontSize="sm" mt={1}>
          {error}
        </Text>
      )}
    </Box>
  );
};

export default RobotSelector;