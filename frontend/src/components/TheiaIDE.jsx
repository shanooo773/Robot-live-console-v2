import { useState, useEffect } from "react";
import { 
  Box, 
  Button, 
  Text, 
  Alert, 
  AlertIcon, 
  VStack,
  HStack,
  Badge,
  Spinner,
  useToast
} from "@chakra-ui/react";

const TheiaIDE = ({ user, authToken, onError }) => {
  const [theiaStatus, setTheiaStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);
  const toast = useToast();

  // Check Theia status on component mount
  useEffect(() => {
    checkTheiaStatus();
  }, []);

  // Auto-start for demo users - check every 5 seconds if container is starting
  useEffect(() => {
    if (user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode) {
      const interval = setInterval(() => {
        if (theiaStatus?.auto_start_attempted && theiaStatus?.status !== "running") {
          checkTheiaStatus();
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [theiaStatus, user]);

  const checkTheiaStatus = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/theia/status', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Read response text first to avoid "body stream already read" error
        const responseText = await response.text();
        try {
          const status = JSON.parse(responseText);
          setTheiaStatus(status);
          setError(null);
          
          // Show toast for demo user auto-start
          if (status.auto_start_attempted && status.status === "running") {
            toast({
              title: "IDE Auto-Started",
              description: "Your development environment has been automatically started!",
              status: "success",
              duration: 3000,
              isClosable: true,
            });
          } else if (status.auto_start_attempted && status.auto_start_error) {
            setError(`Auto-start failed: ${status.auto_start_error}`);
          }
        } catch (jsonError) {
          // Handle JSON parsing errors that might indicate HTML response
          if (responseText.includes('<!doctype') || responseText.includes('<html')) {
            throw new Error('Theia returned HTML instead of JSON - container may not be properly started');
          } else {
            throw new Error(`Invalid JSON response: ${jsonError.message}`);
          }
        }
      } else {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (err) {
      console.error('Error checking Theia status:', err);
      setError(err.message);
      if (onError) {
        onError(err);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const startTheiaContainer = async () => {
    try {
      setIsStarting(true);
      setError(null);
      
      const response = await fetch('/theia/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Read response text first to avoid "body stream already read" error
        const responseText = await response.text();
        try {
          const result = JSON.parse(responseText);
          toast({
            title: "Theia IDE Started",
            description: "Your development environment is now ready!",
            status: "success",
            duration: 3000,
            isClosable: true,
          });
          
          // Refresh status
          setTimeout(() => {
            checkTheiaStatus();
          }, 2000);
        } catch (jsonError) {
          if (responseText.includes('<!doctype') || responseText.includes('<html')) {
            throw new Error('Server returned HTML instead of JSON - Theia configuration issue');
          } else {
            throw new Error(`Invalid JSON response: ${jsonError.message}`);
          }
        }
      } else {
        // Read error response text first to avoid "body stream already read" error
        const errorText = await response.text();
        try {
          const errorData = JSON.parse(errorText);
          throw new Error(errorData.detail || 'Failed to start Theia container');
        } catch (jsonError) {
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
      }
    } catch (err) {
      console.error('Error starting Theia:', err);
      setError(err.message);
      toast({
        title: "Failed to Start IDE",
        description: err.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsStarting(false);
    }
  };

  const stopTheiaContainer = async () => {
    try {
      const response = await fetch('/theia/stop', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast({
          title: "Theia IDE Stopped",
          description: "Your development environment has been stopped.",
          status: "info",
          duration: 3000,
          isClosable: true,
        });
        checkTheiaStatus();
      } else {
        throw new Error('Failed to stop Theia container');
      }
    } catch (err) {
      setError(err.message);
      toast({
        title: "Failed to Stop IDE",
        description: err.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const restartTheiaContainer = async () => {
    try {
      setIsStarting(true);
      const response = await fetch('/theia/restart', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast({
          title: "Theia IDE Restarted",
          description: "Your development environment has been restarted.",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        setTimeout(() => {
          checkTheiaStatus();
        }, 3000);
      } else {
        throw new Error('Failed to restart Theia container');
      }
    } catch (err) {
      setError(err.message);
      toast({
        title: "Failed to Restart IDE",
        description: err.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsStarting(false);
    }
  };

  if (isLoading) {
    return (
      <Box w="100%" h="100%" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={3}>
          <Spinner size="lg" color="blue.400" />
          <Text color="gray.300">Checking IDE status...</Text>
        </VStack>
      </Box>
    );
  }

  return (
    <Box w="100%" h="100%">
      {/* IDE Controls */}
      <VStack spacing={3} mb={4}>
        <HStack spacing={3} w="full" justify="space-between">
          <VStack align="start" spacing={1}>
            <HStack spacing={2}>
              <Text fontSize="lg" color="white" fontWeight="bold">
                Eclipse Theia IDE
              </Text>
              {theiaStatus?.status === "running" && (
                <Badge colorScheme="green" fontSize="xs">
                  RUNNING
                </Badge>
              )}
              {theiaStatus?.status === "stopped" && (
                <Badge colorScheme="orange" fontSize="xs">
                  STOPPED
                </Badge>
              )}
              {theiaStatus?.status === "not_created" && (
                <Badge colorScheme="gray" fontSize="xs">
                  NOT STARTED
                </Badge>
              )}
            </HStack>
            <Text fontSize="xs" color="gray.400">
              Your personal development environment with Python, C++, Git, and Terminal
            </Text>
          </VStack>

          <HStack spacing={2}>
            {theiaStatus?.status === "running" ? (
              <>
                <Button size="sm" colorScheme="blue" onClick={checkTheiaStatus}>
                  Refresh
                </Button>
                <Button size="sm" colorScheme="orange" onClick={restartTheiaContainer} isLoading={isStarting}>
                  Restart
                </Button>
                <Button size="sm" colorScheme="red" onClick={stopTheiaContainer}>
                  Stop
                </Button>
              </>
            ) : (
              <Button 
                size="sm" 
                colorScheme="green" 
                onClick={startTheiaContainer}
                isLoading={isStarting}
                loadingText="Starting..."
              >
                Start IDE
              </Button>
            )}
          </HStack>
        </HStack>

        {/* Status Info */}
        {theiaStatus?.url && (
          <Text fontSize="xs" color="gray.500">
            IDE running at: {theiaStatus.url}
          </Text>
        )}
      </VStack>

      {/* Error Display */}
      {error && (
        <Alert status="error" size="sm" mb={3}>
          <AlertIcon />
          <VStack align="start" spacing={0}>
            <Text fontSize="sm" fontWeight="bold">IDE Error</Text>
            <Text fontSize="xs">{error}</Text>
          </VStack>
        </Alert>
      )}

      {/* Theia IDE Iframe */}
      <Box
        w="100%"
        h="calc(100% - 120px)"
        border="1px solid"
        borderColor="gray.600"
        borderRadius="md"
        bg="#1a1a1a"
        overflow="hidden"
        position="relative"
      >
        {theiaStatus?.status === "running" && theiaStatus?.url ? (
          <iframe
            src={theiaStatus.url}
            width="100%"
            height="100%"
            style={{ 
              border: "none",
              background: "#1e1e1e"
            }}
            title="Eclipse Theia IDE"
            onError={() => {
              setError("Failed to load Theia IDE. Please try restarting.");
              if (onError) {
                onError(new Error("Iframe load error"));
              }
            }}
          />
        ) : (
          <VStack 
            spacing={4} 
            justify="center" 
            align="center" 
            h="100%" 
            p={8} 
            textAlign="center"
          >
            {theiaStatus?.status === "not_created" && !theiaStatus?.auto_start_attempted && (
              <>
                <Text fontSize="4xl">🚀</Text>
                <Text color="gray.300" fontSize="lg" fontWeight="bold">
                  Eclipse Theia IDE
                </Text>
                <Text color="gray.500" fontSize="sm" maxW="md">
                  Your personal development environment is ready to start. 
                  Click "Start IDE" to launch your containerized workspace with Python, C++, Git, and terminal access.
                </Text>
                <VStack spacing={2} mt={4}>
                  <Text fontSize="xs" color="gray.600" fontWeight="bold">Features included:</Text>
                  <VStack spacing={1}>
                    <Text fontSize="xs" color="gray.500">🐍 Python development environment</Text>
                    <Text fontSize="xs" color="gray.500">⚡ C++ compiler and tools</Text>
                    <Text fontSize="xs" color="gray.500">📁 File explorer and editor</Text>
                    <Text fontSize="xs" color="gray.500">💻 Integrated terminal</Text>
                    <Text fontSize="xs" color="gray.500">🔄 Git version control</Text>
                  </VStack>
                </VStack>
              </>
            )}

            {theiaStatus?.auto_start_attempted && theiaStatus?.status !== "running" && (
              <>
                <Spinner size="xl" color="blue.400" />
                <Text color="gray.300" fontSize="lg" fontWeight="bold">
                  Auto-Starting IDE...
                </Text>
                <Text color="gray.500" fontSize="sm">
                  Your development environment is being automatically prepared for you.
                </Text>
              </>
            )}

            {theiaStatus?.status === "stopped" && (
              <>
                <Text fontSize="4xl">⏸️</Text>
                <Text color="gray.300" fontSize="lg" fontWeight="bold">
                  IDE Stopped
                </Text>
                <Text color="gray.500" fontSize="sm" maxW="md">
                  Your development environment is currently stopped. 
                  Click "Start IDE" to resume your work.
                </Text>
              </>
            )}

            {isStarting && (
              <>
                <Spinner size="xl" color="blue.400" />
                <Text color="gray.300" fontSize="lg" fontWeight="bold">
                  Starting Theia IDE...
                </Text>
                <Text color="gray.500" fontSize="sm">
                  Please wait while we prepare your development environment.
                </Text>
              </>
            )}
          </VStack>
        )}
      </Box>

      {/* Future Enhancement Info */}
      <VStack spacing={2} mt={3} align="start">
        <Text fontSize="xs" color="gray.500">
          🔧 Future enhancements:
        </Text>
        <VStack spacing={1} align="start" pl={4}>
          <Text fontSize="xs" color="gray.500">
            • Git-based version history for your projects
          </Text>
          <Text fontSize="xs" color="gray.500">
            • Resource limits and container security improvements
          </Text>
          <Text fontSize="xs" color="gray.500">
            • Extension marketplace integration
          </Text>
        </VStack>
      </VStack>
    </Box>
  );
};

export default TheiaIDE;