import { Box, Button, Menu, MenuButton, MenuList, MenuItem, Text, Badge, HStack } from "@chakra-ui/react";
import { ChevronDownIcon } from "@chakra-ui/icons";

const FileSelector = ({ selectedFile, files, onSelect, isLoading }) => {
  const getFileIcon = (language) => {
    return language === "cpp" ? "🔧" : "🐍";
  };

  return (
    <Box mb={2} minW="200px">
      <Text mb={2} fontSize="sm" color="gray.400">
        Select File to Run:
      </Text>
      <Menu isLazy>
        <MenuButton 
          as={Button} 
          rightIcon={<ChevronDownIcon />}
          variant="outline" 
          color="gray.300" 
          bg="#1a1a2e" 
          _hover={{ bg: "#1e1e2e" }}
          size="sm"
          w="100%"
          textAlign="left"
          isLoading={isLoading}
        >
          {selectedFile ? (
            <HStack spacing={2}>
              <Text>{getFileIcon(selectedFile.language)}</Text>
              <Text isTruncated>{selectedFile.name}</Text>
            </HStack>
          ) : (
            "Select a file..."
          )}
        </MenuButton>
        <MenuList 
          bg="#1a1a2e" 
          border="1px solid #333"
          maxH="300px"
          overflowY="auto"
        >
          {files && files.length > 0 ? (
            files.map((file, index) => (
              <MenuItem
                key={index}
                color={selectedFile?.path === file.path ? "cyan.400" : "gray.300"}
                bg={selectedFile?.path === file.path ? "#2a2a3e" : "transparent"}
                _hover={{
                  color: "cyan.400",
                  bg: "#2a2a3e",
                }}
                onClick={() => onSelect(file)}
              >
                <HStack spacing={2} w="100%">
                  <Text>{getFileIcon(file.language)}</Text>
                  <Text flex="1" isTruncated>{file.name}</Text>
                  <Badge 
                    colorScheme={file.language === "cpp" ? "orange" : "green"} 
                    fontSize="xs"
                  >
                    {file.language === "cpp" ? "C++" : "Python"}
                  </Badge>
                </HStack>
              </MenuItem>
            ))
          ) : (
            <MenuItem isDisabled color="gray.500">
              No .py or .cpp files found
            </MenuItem>
          )}
        </MenuList>
      </Menu>
    </Box>
  );
};

export default FileSelector;
