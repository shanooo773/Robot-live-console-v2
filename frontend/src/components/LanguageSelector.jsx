import { Box, Button, Menu, MenuButton, MenuList, MenuItem, Text } from "@chakra-ui/react";

const LANGUAGE_NAMES = {
  python: "Python",
  cpp: "C++"
};

const LanguageSelector = ({ language, onSelect }) => {
  return (
    <Box mb={2} minW="150px">
      <Text mb={2} fontSize="lg" color="white">
        Language:
      </Text>
      <Menu isLazy>
        <MenuButton as={Button} variant="outline" color="gray.400" bg="#110f1c" _hover={{ bg: "#1e1e2e" }}>
          {LANGUAGE_NAMES[language] || "Select Language"}
        </MenuButton>
        <MenuList bg="#110f1c" border="1px solid #333">
          {Object.entries(LANGUAGE_NAMES).map(([langType, displayName]) => (
            <MenuItem
              key={langType}
              color={langType === language ? "blue.400" : "gray.400"}
              bg={langType === language ? "#1e1e2e" : "transparent"}
              _hover={{
                color: "blue.400",
                bg: "#1e1e2e",
              }}
              onClick={() => onSelect(langType)}
            >
              {displayName}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </Box>
  );
};

export default LanguageSelector;