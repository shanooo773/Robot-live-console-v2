import { Box, Button, Menu, MenuButton, MenuList, MenuItem, Text } from "@chakra-ui/react";
import { useState } from "react";

const ROBOT_NAMES = {
  arm: "Robot Arm",
  hand: "Robot Hand", 
  turtlebot: "TurtleBot3"
};

const RobotSelector = ({ robot, onSelect, availableRobots = [] }) => {
  // Filter ROBOT_NAMES to only show available robots
  const availableRobotEntries = Object.entries(ROBOT_NAMES).filter(([robotType]) => 
    availableRobots.includes(robotType)
  );

  // If no robots are available, show a message
  if (availableRobots.length === 0) {
    return (
      <Box mb={2} minW="150px">
        <Text mb={2} fontSize="lg" color="white">
          Robot Type:
        </Text>
        <Button variant="outline" color="gray.500" bg="#110f1c" disabled>
          No Active Bookings
        </Button>
      </Box>
    );
  }

  return (
    <Box mb={2} minW="150px">
      <Text mb={2} fontSize="lg" color="white">
        Robot Type:
      </Text>
      <Menu isLazy>
        <MenuButton 
          as={Button} 
          variant="solid"
          color="rgba(0, 255, 200, 0.9)" 
          bg="rgba(0, 0, 0, 0.3)"
          border="1px solid rgba(0, 255, 200, 0.4)"
          _hover={{ 
            bg: "rgba(0, 255, 200, 0.1)",
            border: "1px solid rgba(0, 255, 200, 0.7)"
          }}
        >
          {ROBOT_NAMES[robot] || "Select Robot"}
        </MenuButton>
        <MenuList 
          bg="rgba(10, 15, 35, 0.9)" 
          border="1px solid rgba(0, 255, 200, 0.3)"
          backdropFilter="blur(12px)"
        >
          {availableRobotEntries.map(([robotType, displayName]) => (
            <MenuItem
              key={robotType}
              color={robotType === robot ? "rgba(0, 255, 200, 1)" : "rgba(255, 255, 255, 0.7)"}
              bg={robotType === robot ? "rgba(0, 255, 200, 0.1)" : "transparent"}
              _hover={{
                color: "rgba(0, 255, 200, 1)",
                bg: "rgba(0, 255, 200, 0.1)",
              }}
              onClick={() => onSelect(robotType)}
            >
              {displayName}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </Box>
  );
};

export default RobotSelector;