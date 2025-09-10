import { useState, useEffect, useRef } from "react";
import { 
  Box, 
  Button, 
  Text, 
  Alert, 
  AlertIcon, 
  VStack,
  Badge,
  Spinner,
  HStack,
  Select
} from "@chakra-ui/react";

const RTSPVideoPlayer = ({ user, authToken, onError }) => {
  const videoRef = useRef();
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [streamType, setStreamType] = useState("test"); // test, rtsp, webrtc
  
  // Test streams for different modes
  const testStreams = {
    test: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    // Future: RTSP stream will be configured here
    rtsp: "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov",
    // Future: WebRTC stream configuration
    webrtc: null
  };

  const handleConnect = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (streamType === "test") {
        // Use test video stream
        if (videoRef.current) {
          videoRef.current.src = testStreams.test;
          setIsConnected(true);
        }
      } else if (streamType === "rtsp") {
        // TODO: Implement RTSP stream connection
        // For now, show placeholder
        setError("RTSP streaming is not yet implemented. This will connect to the Raspberry Pi robot camera.");
      } else if (streamType === "webrtc") {
        // TODO: Implement WebRTC connection
        setError("WebRTC streaming is not yet implemented. This will provide real-time robot camera feed.");
      }
    } catch (err) {
      setError(`Failed to connect to video stream: ${err.message}`);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    if (videoRef.current) {
      videoRef.current.src = "";
    }
    setIsConnected(false);
    setError(null);
  };

  const handleVideoError = (e) => {
    console.error("Video error:", e);
    setError("Video stream error. Please try reconnecting.");
    setIsConnected(false);
    if (onError) {
      onError(e);
    }
  };

  const handleVideoLoad = () => {
    setIsConnected(true);
    setError(null);
  };

  return (
    <Box w="100%" h="100%">
      {/* Stream Controls */}
      <VStack spacing={3} mb={4}>
        <HStack spacing={3} w="full">
          <Select 
            value={streamType} 
            onChange={(e) => setStreamType(e.target.value)}
            size="sm"
            maxW="200px"
          >
            <option value="test">Test Stream</option>
            <option value="rtsp">RTSP (Robot Camera)</option>
            <option value="webrtc">WebRTC (Real-time)</option>
          </Select>
          
          {!isConnected ? (
            <Button
              colorScheme="blue"
              size="sm"
              onClick={handleConnect}
              isLoading={isLoading}
              loadingText="Connecting..."
              disabled={isLoading}
            >
              Connect Video Feed
            </Button>
          ) : (
            <Button
              colorScheme="red"
              size="sm"
              onClick={handleDisconnect}
            >
              Disconnect
            </Button>
          )}
          
          {isConnected && (
            <Badge colorScheme="green" fontSize="xs">
              LIVE
            </Badge>
          )}
        </HStack>

        {/* Stream Info */}
        <Text fontSize="xs" color="gray.400" textAlign="center">
          {streamType === "test" && "Test video stream for development"}
          {streamType === "rtsp" && "🤖 Future: Raspberry Pi robot camera (RTSP)"}
          {streamType === "webrtc" && "🚀 Future: Real-time robot video feed (WebRTC)"}
        </Text>
      </VStack>

      {/* Error Display */}
      {error && (
        <Alert status="warning" size="sm" mb={3}>
          <AlertIcon />
          <VStack align="start" spacing={0}>
            <Text fontSize="sm" fontWeight="bold">Video Stream Error</Text>
            <Text fontSize="xs">{error}</Text>
          </VStack>
        </Alert>
      )}

      {/* Video Player */}
      <Box
        w="100%"
        h="calc(100% - 120px)"
        border="1px solid"
        borderColor="gray.600"
        borderRadius="md"
        bg="#1a1a1a"
        overflow="hidden"
        position="relative"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        {isLoading && (
          <VStack spacing={3}>
            <Spinner size="lg" color="blue.400" />
            <Text color="gray.300" fontSize="sm">
              Connecting to video stream...
            </Text>
          </VStack>
        )}

        {!isConnected && !isLoading && !error && (
          <VStack spacing={3} p={6} textAlign="center">
            <Text fontSize="2xl">📹</Text>
            <Text color="gray.300" fontSize="md" fontWeight="bold">
              Robot Video Feed
            </Text>
            <Text color="gray.500" fontSize="sm" maxW="sm">
              Select a stream type and click "Connect Video Feed" to start viewing the robot camera.
            </Text>
          </VStack>
        )}

        {isConnected && (
          <video
            ref={videoRef}
            width="100%"
            height="100%"
            controls
            autoPlay
            muted
            style={{ 
              objectFit: "contain",
              background: "#000"
            }}
            onError={handleVideoError}
            onLoadedData={handleVideoLoad}
            onLoadStart={() => setIsLoading(true)}
            onCanPlay={() => setIsLoading(false)}
          >
            Your browser does not support the video tag.
          </video>
        )}
      </Box>

      {/* Future Enhancement Markers */}
      <VStack spacing={2} mt={3} align="start">
        <Text fontSize="xs" color="gray.500">
          🔧 Future enhancements:
        </Text>
        <VStack spacing={1} align="start" pl={4}>
          <Text fontSize="xs" color="gray.500">
            • Connect to Raspberry Pi robot camera via RTSP
          </Text>
          <Text fontSize="xs" color="gray.500">
            • Real-time WebRTC streaming for low latency
          </Text>
          <Text fontSize="xs" color="gray.500">
            • Multiple camera angles and robot sensors
          </Text>
        </VStack>
      </VStack>
    </Box>
  );
};

export default RTSPVideoPlayer;