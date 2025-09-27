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
import { getWebRTCConfig, getRobotWebRTCUrl, sendOfferToRobot, sendICECandidateToRobot } from '../api';

const WebRTCVideoPlayer = ({ user, authToken, onError, robotType = "turtlebot" }) => {
  const videoRef = useRef();
  const peerConnectionRef = useRef();
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [streamType, setStreamType] = useState("webrtc"); // test, webrtc
  const [webrtcStatus, setWebrtcStatus] = useState("disconnected"); // disconnected, connecting, connected
  const [peerId, setPeerId] = useState(null); // Store peer ID for robot connection
  
  // Test streams for different modes
  const testStreams = {
    test: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    // WebRTC stream is handled directly through robot connection
    webrtc: null
  };

  // WebRTC Configuration - will be fetched from backend
  const [rtcConfig, setRtcConfig] = useState({
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  });

  // State for direct robot WebRTC connection
  const [robotWebRTCUrl, setRobotWebRTCUrl] = useState(null);

  // Initialize WebRTC connection with direct robot connection
  const initWebRTC = async () => {
    try {
      setWebrtcStatus("connecting");
      
      // Step 1: Fetch WebRTC configuration from backend
      try {
        const config = await getWebRTCConfig(authToken);
        if (config.ice_servers) {
          setRtcConfig({ iceServers: config.ice_servers });
          console.log('Fetched WebRTC config from backend:', config);
        }
      } catch (configError) {
        console.warn('Failed to fetch WebRTC config from backend, using defaults:', configError);
      }
      
      // Step 2: Get robot WebRTC URL from backend (with auth/booking validation)
      let robotWebRTCInfo;
      try {
        console.log('Getting robot WebRTC URL from backend...');
        robotWebRTCInfo = await getRobotWebRTCUrl(robotType, authToken);
        console.log('Robot WebRTC info:', robotWebRTCInfo);
      } catch (urlError) {
        console.error('Failed to get robot WebRTC URL:', urlError);
        
        if (urlError.response) {
          const status = urlError.response.status;
          const detail = urlError.response.data?.detail || urlError.message;
          
          if (status === 403) {
            setError(`Access denied: ${detail}`);
          } else if (status === 404) {
            setError(`Robot not found or WebRTC not configured: ${detail}`);
          } else {
            setError(`Failed to get robot WebRTC URL: ${detail}`);
          }
        } else {
          setError(`Failed to get robot WebRTC URL: ${urlError.message}`);
        }
        
        setWebrtcStatus("disconnected");
        return;
      }
      
      const robotWebRTCUrl = robotWebRTCInfo.webrtc_url;
      if (!robotWebRTCUrl) {
        setError('Robot WebRTC URL not configured');
        setWebrtcStatus("disconnected");
        return;
      }
      
      // Step 3: Create peer connection with fetched configuration
      const peerConnection = new RTCPeerConnection(rtcConfig);
      peerConnectionRef.current = peerConnection;

      // Set up connection timeout (30 seconds)
      const connectionTimeout = setTimeout(() => {
        if (webrtcStatus === "connecting") {
          console.warn('WebRTC connection timed out');
          setError('Connection timed out. The robot may not be available.');
          setWebrtcStatus("disconnected");
          if (peerConnection) {
            peerConnection.close();
          }
        }
      }, 30000);

      // Step 4: Set up video element to receive remote stream
      peerConnection.ontrack = (event) => {
        console.log('Received remote stream from robot');
        clearTimeout(connectionTimeout); // Clear timeout on successful connection
        if (videoRef.current && event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
          setIsConnected(true);
          setWebrtcStatus("connected");
        }
      };

      // Step 5: Handle ICE candidates - send directly to robot
      let robotPeerId = null;
      peerConnection.onicecandidate = async (event) => {
        if (event.candidate && robotPeerId) {
          console.log('Sending ICE candidate directly to robot');
          try {
            await sendICECandidateToRobot(robotWebRTCUrl, robotPeerId, event.candidate);
          } catch (iceError) {
            console.error('Failed to send ICE candidate to robot:', iceError);
          }
        }
      };

      // Step 6: Create offer and send directly to robot
      const offer = await peerConnection.createOffer({
        offerToReceiveVideo: true,  // Ensure we request video from robot
        offerToReceiveAudio: false  // We only need video for robot cameras
      });
      await peerConnection.setLocalDescription(offer);
      
      try {
        console.log('Sending SDP offer directly to robot at:', robotWebRTCUrl);
        const answerResponse = await sendOfferToRobot(robotWebRTCUrl, offer);
        console.log('Received answer from robot:', answerResponse);
        
        // Store robot peer ID for ICE candidates
        if (answerResponse.peer_id) {
          robotPeerId = answerResponse.peer_id;
          setPeerId(answerResponse.peer_id);
        }
        
        // Apply the answer from robot
        if (answerResponse.sdp && answerResponse.type) {
          await peerConnection.setRemoteDescription({
            sdp: answerResponse.sdp,
            type: answerResponse.type
          });
          console.log('Applied remote description from robot');
        } else {
          throw new Error('Invalid answer received from robot');
        }
        
      } catch (offerError) {
        console.error('Failed to connect to robot WebRTC server:', offerError);
        setError(`Failed to connect to robot: ${offerError.message}. The robot may be offline or not configured.`);
        setWebrtcStatus("disconnected");
        clearTimeout(connectionTimeout);
        return;
      }

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
    
    // Note: socketRef was removed as WebRTC now connects directly to robot
    // No socket connection cleanup needed for direct robot WebRTC
    
    if (videoRef.current) {
      videoRef.current.src = "";
      videoRef.current.srcObject = null;
    }
    
    setIsConnected(false);
    setWebrtcStatus("disconnected");
    setError(null);
    setPeerId(null); // Reset peer ID
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
            <option value="webrtc">WebRTC (Real-time)</option>
          </Select>
          
          {!isConnected ? (
            <Button
              variant="solid"
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
              variant="neonPill"
              size="sm"
              onClick={handleDisconnect}
            >
              Disconnect
            </Button>
          )}
          
          {isConnected && (
            <Badge variant="neonPill" colorScheme="green" fontSize="xs">
              LIVE
            </Badge>
          )}
          
          {streamType === "webrtc" && webrtcStatus !== "disconnected" && (
            <Badge 
              variant="neonPill"
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
            playsInline
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

      {/* Enhancement Status */}
      <VStack spacing={2} mt={3} align="start">
        <Text fontSize="xs" color="gray.500">
          ✅ Current features:
        </Text>
        <VStack spacing={1} align="start" pl={4}>
          <Text fontSize="xs" color="gray.500">
            • Direct WebRTC streaming from robot
          </Text>
          <Text fontSize="xs" color="gray.500">
            • Real-time low-latency video connection
          </Text>
          <Text fontSize="xs" color="gray.500">
            • Automatic ICE candidate handling
          </Text>
        </VStack>
      </VStack>
    </Box>
  );
};

export default WebRTCVideoPlayer;