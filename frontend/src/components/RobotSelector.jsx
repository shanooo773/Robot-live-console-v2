import { Box, Button, Menu, MenuButton, MenuList, MenuItem, Text } from "@chakra-ui/react";
import { useState } from "react";

const ROBOT_NAMES = {
  arm: "Robot Arm",
  hand: "Robot Hand", 
  turtlebot: "TurtleBot3"
};

const RobotSelector = ({ robot, onSelect }) => {
  return (
    <Box mb={2} minW="150px">
      <Text mb={2} fontSize="lg" color="white">
        Robot Type:
      </Text>
      <Menu isLazy>
        <MenuButton as={Button} variant="outline" color="gray.400" bg="#110f1c" _hover={{ bg: "#1e1e2e" }}>
          {ROBOT_NAMES[robot] || "Select Robot"}
        </MenuButton>
        <MenuList bg="#110f1c" border="1px solid #333">
          {Object.entries(ROBOT_NAMES).map(([robotType, displayName]) => (
            <MenuItem
              key={robotType}
              color={robotType === robot ? "blue.400" : "gray.400"}
              bg={robotType === robot ? "#1e1e2e" : "transparent"}
              _hover={{
                color: "blue.400",
                bg: "#1e1e2e",
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