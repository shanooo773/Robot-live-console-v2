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
      
      // Use demo endpoint for demo users, regular endpoint for authenticated users
      const isDemoUser = user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode;
      const endpoint = isDemoUser ? '/theia/demo/status' : '/theia/status';
      const headers = isDemoUser ? 
        { 'Content-Type': 'application/json' } :
        { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' };
      
      const response = await fetch(endpoint, { headers });

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
        h={error ? "calc(100% - 80px)" : "100%"}
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
            {/* Always show starting state for non-running containers - removed the startup message */}
            <Spinner size="xl" color="blue.400" />
            <Text color="gray.300" fontSize="lg" fontWeight="bold">
              Starting IDE...
            </Text>
            <Text color="gray.500" fontSize="sm">
              Your development environment is being prepared.
            </Text>
          </VStack>
        )}
      </Box>
    </Box>
  );
};

export default TheiaIDE;