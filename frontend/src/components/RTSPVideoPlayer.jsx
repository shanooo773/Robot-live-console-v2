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
import io from 'socket.io-client';

const RTSPVideoPlayer = ({ user, authToken, onError, robotType = "turtlebot" }) => {
  const videoRef = useRef();
  const peerConnectionRef = useRef();
  const socketRef = useRef();
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [streamType, setStreamType] = useState("test"); // test, rtsp, webrtc
  const [webrtcStatus, setWebrtcStatus] = useState("disconnected"); // disconnected, connecting, connected
  
  // Test streams for different modes
  const testStreams = {
    test: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    // Future: RTSP stream will be configured here
    rtsp: "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov",
    // WebRTC will be handled by peer connection
    webrtc: null
  };

  // WebRTC Configuration
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  // Initialize WebRTC connection
  const initWebRTC = async () => {
    try {
      setWebrtcStatus("connecting");
      
      // Create peer connection
      const peerConnection = new RTCPeerConnection(rtcConfig);
      peerConnectionRef.current = peerConnection;

      // Set up video element to receive remote stream
      peerConnection.ontrack = (event) => {
        console.log('Received remote stream');
        if (videoRef.current && event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
          setIsConnected(true);
          setWebrtcStatus("connected");
        }
      };

      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && socketRef.current) {
          console.log('Sending ICE candidate');
          socketRef.current.emit('ice-candidate', {
            to: `robot_${robotType}`,
            candidate: event.candidate
          });
        }
      };

      // Connect to signaling server
      const socket = io('ws://localhost:8080', {
        transports: ['websocket'],
        auth: {
          token: authToken
        }
      });
      socketRef.current = socket;

      socket.on('connect', () => {
        console.log('Connected to signaling server');
        // Register as viewer
        socket.emit('register', {
          userId: user?.id || 'anonymous',
          userType: 'viewer'
        });
        
        // Join robot room
        socket.emit('join-room', {
          roomId: `robot_${robotType}_${user?.id || 'anonymous'}`
        });
      });

      socket.on('offer', async (data) => {
        console.log('Received offer from robot');
        try {
          await peerConnection.setRemoteDescription(data.offer);
          const answer = await peerConnection.createAnswer();
          await peerConnection.setLocalDescription(answer);
          
          socket.emit('answer', {
            to: data.from,
            answer: answer
          });
        } catch (err) {
          console.error('Error handling offer:', err);
          setError(`Failed to process video offer: ${err.message}`);
        }
      });

      socket.on('ice-candidate', async (data) => {
        console.log('Received ICE candidate');
        try {
          await peerConnection.addIceCandidate(data.candidate);
        } catch (err) {
          console.error('Error adding ICE candidate:', err);
        }
      });

      socket.on('robot-available', (data) => {
        console.log('Robot available:', data.userId);
        // Robot is ready to stream
      });

      socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
        setError(`Failed to connect to signaling server: ${error.message}`);
        setWebrtcStatus("disconnected");
      });

      // Create offer to start connection
      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      
      socket.emit('offer', {
        to: `robot_${robotType}`,
        offer: offer
      });

    } catch (err) {
      console.error('WebRTC initialization error:', err);
      setError(`WebRTC connection failed: ${err.message}`);
      setWebrtcStatus("disconnected");
    }
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
        // Initialize WebRTC connection
        await initWebRTC();
      }
    } catch (err) {
      setError(`Failed to connect to video stream: ${err.message}`);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = () => {
    // Clean up WebRTC connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    
    if (videoRef.current) {
      videoRef.current.src = "";
      videoRef.current.srcObject = null;
    }
    
    setIsConnected(false);
    setWebrtcStatus("disconnected");
    setError(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      handleDisconnect();
    };
  }, []);

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
          
          {streamType === "webrtc" && webrtcStatus !== "disconnected" && (
            <Badge 
              colorScheme={webrtcStatus === "connected" ? "green" : "yellow"} 
              fontSize="xs"
            >
              WebRTC: {webrtcStatus.toUpperCase()}
            </Badge>
          )}
        </HStack>

        {/* Stream Info */}
        <Text fontSize="xs" color="gray.400" textAlign="center">
          {streamType === "test" && "Test video stream for development"}
          {streamType === "rtsp" && "🤖 Raspberry Pi robot camera (RTSP) - Not yet implemented"}
          {streamType === "webrtc" && `🚀 Real-time robot video feed (WebRTC) - Robot: ${robotType}`}
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