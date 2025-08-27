import { useState, useEffect } from "react";
import { 
  Box, 
  Button, 
  Text, 
  Spinner, 
  Alert, 
  AlertIcon, 
  AlertTitle,
  AlertDescription,
  VStack,
  Badge
} from "@chakra-ui/react";
import { executeRobotCode } from "../api";

const VideoPlayer = ({ editorRef, robot, codeValue, serviceStatus }) => {
  const [videoUrl, setVideoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState("");
  const [executionId, setExecutionId] = useState("");
  const [videoLoadError, setVideoLoadError] = useState(false);
  const [simulationType, setSimulationType] = useState(null);

  // Reset video load error when videoUrl changes
  useEffect(() => {
    setVideoLoadError(false);
  }, [videoUrl]);

  const isDockerAvailable = serviceStatus?.services?.docker?.available;
  const systemStatus = serviceStatus?.health?.status;

  const runCode = async () => {
    // Get source code from editor or fallback to prop value
    let sourceCode = "";
    
    if (editorRef.current) {
      try {
        sourceCode = editorRef.current.getValue();
      } catch (err) {
        console.warn("Could not get code from editor, using fallback value");
        sourceCode = codeValue;
      }
    } else {
      sourceCode = codeValue;
    }

    if (!sourceCode || sourceCode.trim() === "") {
      setIsError(true);
      setError("Please enter some code to run");
      return;
    }

    if (!robot) {
      setIsError(true);
      setError("Please select a robot type first");
      return;
    }

    try {
      setIsLoading(true);
      setIsError(false);
      setVideoUrl("");
      setError("");
      setExecutionId("");
      setVideoLoadError(false);
      setSimulationType(null);

      const result = await executeRobotCode(sourceCode, robot);
      
      if (result.success && result.video_url) {
        setVideoUrl(result.video_url);
        setExecutionId(result.execution_id || "");
        
        // Detect simulation type from result or service status
        if (result.simulation_type) {
          setSimulationType(result.simulation_type);
        } else if (!isDockerAvailable) {
          setSimulationType('mock');
        } else {
          setSimulationType('docker');
        }
      } else {
        setIsError(true);
        setError(result.error || "Failed to execute code");
      }
    } catch (error) {
      console.error("Execution error:", error);
      setIsError(true);
      setError(error.response?.data?.detail || error.message || "An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVideoError = () => {
    console.warn("Video failed to load");
    setVideoLoadError(true);
  };

  return (
    <Box w="100%" h="100%">
      {/* Status Info */}
      {!isDockerAvailable && (
        <Alert status="warning" size="sm" mb={2}>
          <AlertIcon />
          <VStack align="start" spacing={1}>
            <AlertTitle fontSize="sm">Limited Simulation Mode</AlertTitle>
            <AlertDescription fontSize="xs">
              Robot simulation service is unavailable. Code will run in fallback mode.
            </AlertDescription>
          </VStack>
        </Alert>
      )}

      <Button
        colorScheme={isDockerAvailable ? "green" : "orange"}
        mb={4}
        isLoading={isLoading}
        loadingText="Running Simulation..."
        onClick={runCode}
        size="md"
        w="full"
      >
        {isDockerAvailable ? "Run Gazebo Simulation" : "Run Code (Limited Mode)"}
      </Button>

      {isError && (
        <Alert status="error" mb={2} size="sm">
          <AlertIcon />
          <VStack align="start" spacing={1}>
            <AlertTitle fontSize="sm">Execution Failed</AlertTitle>
            <AlertDescription fontSize="xs">{error}</AlertDescription>
          </VStack>
        </Alert>
      )}

      {isLoading && (
        <Box
          height="calc(100% - 80px)"
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          border="1px solid #333"
          borderRadius="md"
          bg="#1a1a1a"
        >
          <Spinner size="lg" color="blue.400" mb={2} />
          <Text color="gray.300" fontSize="md" mb={1}>
            {isDockerAvailable ? "Running Robot Simulation..." : "Running Code..."}
          </Text>
          <Text color="gray.500" fontSize="xs" textAlign="center" maxW="sm">
            {isDockerAvailable 
              ? "Your code is being executed in the robot simulation environment."
              : "Your code is running in fallback mode."}
          </Text>
        </Box>
      )}

      {videoUrl && !isLoading && (
        <Box
          height="calc(100% - 80px)"
          border="1px solid #333"
          borderRadius="md"
          bg="#1a1a1a"
          overflow="hidden"
          position="relative"
        >
          {/* Simulation Type Badge */}
          {simulationType && (
            <Badge
              position="absolute"
              top={2}
              right={2}
              zIndex={10}
              colorScheme={simulationType === 'mock' ? 'orange' : 'green'}
              fontSize="xs"
            >
              {simulationType === 'mock' ? 'Fallback Mode' : 'Real Simulation'}
            </Badge>
          )}
          
          {videoLoadError ? (
            <Box
              height="100%"
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              p={4}
            >
              <Text color="yellow.400" fontSize="md" mb={2}>
                ⚠️ Video Unavailable
              </Text>
              <Text color="gray.300" textAlign="center" mb={2} fontSize="sm">
                The simulation completed successfully, but the video couldn't be loaded.
              </Text>
              <Text color="gray.400" fontSize="xs" textAlign="center">
                Execution ID: {executionId}
              </Text>
            </Box>
          ) : (
            <video
              width="100%"
              height="100%"
              controls
              autoPlay
              style={{ objectFit: "contain" }}
              onError={handleVideoError}
              onLoadStart={() => console.log('Video load started')}
              onCanPlay={() => console.log('Video can play')}
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          )}
        </Box>
      )}

      {!videoUrl && !isLoading && !isError && (
        <Box
          height="calc(100% - 80px)"
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          border="1px solid #333"
          borderRadius="md"
          bg="#1a1a1a"
          p={4}
        >
          <Text color="gray.300" fontSize="md" mb={2}>
            🚀 Ready to Simulate
          </Text>
          <Text color="gray.500" fontSize="sm" textAlign="center" maxW="sm">
            {isDockerAvailable 
              ? "Click 'Run Gazebo Simulation' to execute your code in the robot simulation environment."
              : "Click 'Run Code' to execute your code in fallback mode. Real simulation is currently unavailable."}
          </Text>
        </Box>
      )}
    </Box>
  );
};

export default VideoPlayer;