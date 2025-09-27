import { useRef, useState, useEffect } from "react";
import { 
  Box, 
  HStack, 
  VStack, 
  Text, 
  Button, 
  Avatar, 
  Badge,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  IconButton,
  Tooltip,
} from "@chakra-ui/react";
import { 
  ViewIcon, 
  RepeatIcon, 
  CloseIcon, 
  SettingsIcon,
  InfoIcon,
  ChevronRightIcon,
  ViewOffIcon,
} from "@chakra-ui/icons";
import TheiaIDE from "./TheiaIDE";
import WebRTCVideoPlayer from "./WebRTCVideoPlayer";
import RobotSelector from "./RobotSelector";
import { checkAccess, getVideo, getMyActiveBookings, getAvailableRobots } from "../api";

const NeonRobotConsole = ({ user, slot, authToken, onBack, onLogout }) => {
  // Layout state
  const [panelLayout, setPanelLayout] = useState("split"); // "split", "ide-expanded", "video-expanded"
  const [dividerPosition, setDividerPosition] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);
  
  // Existing state
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [hasAccess, setHasAccess] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [videoLoading, setVideoLoading] = useState(false);
  const [activeBookings, setActiveBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotNames, setRobotNames] = useState({});
  
  // Modal state
  const { isOpen: isLogsOpen, onOpen: onLogsOpen, onClose: onLogsClose } = useDisclosure();
  
  const toast = useToast();
  const containerRef = useRef();

  // Load robot names and check access (existing logic)
  const loadRobotNames = async () => {
    try {
      const robotData = await getAvailableRobots();
      const robotDetails = robotData.details || {};
      
      const formattedRobots = {};
      Object.keys(robotDetails).forEach(robotType => {
        const robot = robotDetails[robotType];
        let emoji = "🤖";
        if (robotType.includes("arm")) emoji = "🦾";
        else if (robotType.includes("hand")) emoji = "🤲";
        else if (robotType.includes("turtle")) emoji = "🤖";
        
        formattedRobots[robotType] = {
          name: robot.display_name || robotType,
          emoji: emoji,
          description: robot.description || `${robotType} robot`,
        };
      });
      
      setRobotNames(formattedRobots);
    } catch (error) {
      console.error("Failed to load robot details:", error);
      // Fallback robot names
      const fallbackRobots = {
        turtlebot: { name: "TurtleBot3", emoji: "🤖", description: "Mobile navigation robot" },
        robot_arm: { name: "Robot Arm", emoji: "🦾", description: "6-DOF manipulation arm" },
        robot_hand: { name: "Robot Hand", emoji: "🤲", description: "Dexterous robotic hand" },
      };
      setRobotNames(fallbackRobots);
    }
  };

  useEffect(() => {
    const checkUserAccess = async () => {
      setLoading(true);
      await loadRobotNames();
      
      try {
        if (user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode || 
            localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin') || 
            localStorage.getItem('isDummy') || localStorage.getItem('isDemoMode')) {
            
          setHasAccess(true);
          setAvailableRobots(['turtlebot', 'robot_arm', 'robot_hand']);
        } else if (authToken) {
          try {
            const bookings = await getMyActiveBookings(authToken);
            setActiveBookings(bookings);
            
            const robotTypes = [...new Set(bookings.map(booking => booking.robot_type))];
            setAvailableRobots(robotTypes);
            setHasAccess(robotTypes.length > 0);
            
            if (robotTypes.length > 0 && !robotTypes.includes(robot)) {
              setRobot(robotTypes[0]);
            }
            
            if (robotTypes.length === 0) {
              toast({
                title: "No Active Bookings",
                description: "You need an active booking to access the development console.",
                status: "warning",
                duration: 5000,
                isClosable: true,
              });
            }
          } catch (error) {
            console.error("Failed to fetch active bookings:", error);
            setHasAccess(false);
            toast({
              title: "Error",
              description: "Failed to load your active bookings.",
              status: "error",
              duration: 5000,
              isClosable: true,
            });
          }
        } else {
          setHasAccess(false);
        }
      } catch (error) {
        console.error("Access check failed:", error);
        toast({
          title: "Access Check Failed",
          description: "Unable to verify access. Please try again.",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    };

    checkUserAccess();
  }, [authToken, user, toast, robot]);

  // Panel control functions
  const expandIDE = () => setPanelLayout("ide-expanded");
  const expandVideo = () => setPanelLayout("video-expanded");
  const resetSplit = () => {
    setPanelLayout("split");
    setDividerPosition(50);
  };

  // Drag handling for resizable divider
  const handleMouseDown = (e) => {
    setIsDragging(true);
    document.body.style.userSelect = 'none';
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
    
    // Constrain between 20% and 80%
    const constrainedPosition = Math.min(Math.max(newPosition, 20), 80);
    setDividerPosition(constrainedPosition);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    document.body.style.userSelect = '';
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging]);

  const onSelect = (robotType) => {
    setRobot(robotType);
    setShowVideo(false);
    setVideoUrl(null);
  };

  const handleGetRealResult = async () => {
    setVideoLoading(true);
    try {
      if (authToken) {
        const videoBlob = await getVideo(robot, authToken);
        const url = URL.createObjectURL(videoBlob);
        setVideoUrl(url);
        setShowVideo(true);
        toast({
          title: "Video Loaded",
          description: `${robotNames[robot].name} simulation video is now playing.`,
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else if (user?.isDemoMode || user?.isDemoUser || user?.isDemoAdmin || 
                 localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin') || 
                 localStorage.getItem('isDummy') || localStorage.getItem('isDemoMode')) {
        toast({
          title: "Demo Mode",
          description: `In demo mode, ${robotNames[robot]?.name || robot} simulation would display here. Video access depends on robot configuration.`,
          status: "info",
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Failed to load video:", error);
      toast({
        title: "Video Load Failed",
        description: error.response?.data?.detail || "Unable to load simulation video. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setVideoLoading(false);
    }
  };

  if (loading) {
    return (
      <Box h="100vh" w="100vw" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={6}>
          <Spinner size="xl" color="neon.cyan" />
          <Text variant="neonGlow" fontSize="lg">Initializing Robot Console...</Text>
        </VStack>
      </Box>
    );
  }

  if (!hasAccess) {
    return (
      <Box h="100vh" w="100vw" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={6} maxW="md" textAlign="center">
          <Alert status="warning" variant="glassPanel" borderRadius="12px">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold" color="white">Access Denied</Text>
              <Text color="gray.300">You need an active booking to access the development console.</Text>
            </Box>
          </Alert>
          <Button variant="neonPrimary" onClick={onBack}>
            Go Back to Booking
          </Button>
        </VStack>
      </Box>
    );
  }

  // Calculate panel widths based on layout mode
  const getLeftPanelWidth = () => {
    if (panelLayout === "ide-expanded") return "100%";
    if (panelLayout === "video-expanded") return "0%";
    return `${dividerPosition}%`;
  };

  const getRightPanelWidth = () => {
    if (panelLayout === "ide-expanded") return "0%";
    if (panelLayout === "video-expanded") return "100%";
    return `${100 - dividerPosition}%`;
  };

  return (
    <Box h="100vh" w="100vw" overflow="hidden" position="relative">
      {/* Neon Glass Top Bar */}
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        zIndex="1000"
        h="60px"
        bg="rgba(26, 32, 44, 0.2)"
        backdropFilter="blur(12px)"
        borderBottom="1px solid rgba(0,255,200,0.3)"
        display="flex"
        alignItems="center"
        px={6}
        boxShadow="0 4px 20px rgba(0,0,0,0.3)"
      >
        <HStack spacing={4} flex="1">
          {/* Left side - Robot info */}
          <HStack spacing={3}>
            <Avatar size="sm" name={user.name} />
            <VStack align="start" spacing={0}>
              <Text color="white" fontSize="sm" fontWeight="600" fontFamily="'Exo 2', sans-serif">
                {user.name}
              </Text>
              {(user?.isDemoUser || user?.isDemoAdmin || localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin')) && (
                <Badge colorScheme="orange" fontSize="xs">DEMO</Badge>
              )}
            </VStack>
            
            <Box w="1px" h="30px" bg="rgba(0,255,200,0.3)" />
            
            <HStack spacing={2}>
              <Text fontSize="lg">{robotNames[robot]?.emoji || "🤖"}</Text>
              <Text color="neon.cyan" fontSize="sm" fontWeight="600">
                {robotNames[robot]?.name || robot}
              </Text>
              <Badge variant="outline" colorScheme="green" fontSize="xs">ACTIVE</Badge>
            </HStack>
          </HStack>
          
          <Box flex="1" />
          
          {/* Center - Panel controls */}
          <HStack spacing={2}>
            <Tooltip label="Expand IDE" placement="bottom">
              <IconButton
                icon={<ChevronRightIcon />}
                size="sm"
                variant="ghost"
                onClick={expandIDE}
                isActive={panelLayout === "ide-expanded"}
                _active={{ bg: "rgba(0,255,200,0.2)" }}
              />
            </Tooltip>
            
            <Tooltip label="Expand Video" placement="bottom">
              <IconButton
                icon={<ViewIcon />}
                size="sm"
                variant="ghost"
                onClick={expandVideo}
                isActive={panelLayout === "video-expanded"}
                _active={{ bg: "rgba(0,255,200,0.2)" }}
              />
            </Tooltip>
            
            <Tooltip label="Reset Split View" placement="bottom">
              <IconButton
                icon={<ViewOffIcon />}
                size="sm"
                variant="ghost"
                onClick={resetSplit}
                isActive={panelLayout === "split"}
                _active={{ bg: "rgba(0,255,200,0.2)" }}
              />
            </Tooltip>
          </HStack>
          
          <Box flex="1" />
          
          {/* Right side - Controls */}
          <HStack spacing={3}>
            <RobotSelector robot={robot} onSelect={onSelect} availableRobots={availableRobots} />
            
            <Button
              size="sm"
              variant="solid"
              onClick={handleGetRealResult}
              isLoading={videoLoading}
              loadingText="Loading..."
            >
              Get Real Result
            </Button>
            
            <Tooltip label="View Logs & Instructions" placement="bottom">
              <IconButton
                icon={<InfoIcon />}
                size="sm"
                variant="ghost"
                onClick={onLogsOpen}
              />
            </Tooltip>
            
            <Tooltip label="Settings" placement="bottom">
              <IconButton
                icon={<SettingsIcon />}
                size="sm"
                variant="ghost"
              />
            </Tooltip>
            
            <Button size="sm" variant="ghost" onClick={onBack}>
              Back
            </Button>
            
            <Button size="sm" variant="ghost" onClick={onLogout}>
              Logout
            </Button>
          </HStack>
        </HStack>
      </Box>

      {/* Main Content Area */}
      <Box
        ref={containerRef}
        mt="60px"
        h="calc(100vh - 60px)"
        display="flex"
        position="relative"
      >
        {/* Left Panel - Eclipse Theia IDE */}
        <Box
          w={getLeftPanelWidth()}
          h="100%"
          display={panelLayout === "video-expanded" ? "none" : "block"}
          position="relative"
          overflow="hidden"
        >
          <Box h="100%" variant="glassPanel" borderRadius="0">
            <TheiaIDE 
              user={user} 
              authToken={authToken}
              onError={(error) => {
                toast({
                  title: "IDE Error",
                  description: error.message,
                  status: "error",
                  duration: 5000,
                  isClosable: true,
                });
              }}
            />
          </Box>
        </Box>

        {/* Draggable Divider */}
        {panelLayout === "split" && (
          <Box
            position="absolute"
            left={`${dividerPosition}%`}
            top="0"
            bottom="0"
            w="4px"
            bg="rgba(0,255,200,0.3)"
            cursor="col-resize"
            zIndex="10"
            _hover={{
              bg: "rgba(0,255,200,0.6)",
              boxShadow: "0 0 10px rgba(0,255,200,0.4)",
            }}
            onMouseDown={handleMouseDown}
            transform="translateX(-2px)"
          >
            <Box
              position="absolute"
              top="50%"
              left="50%"
              transform="translate(-50%, -50%)"
              w="20px"
              h="40px"
              bg="rgba(0,255,200,0.2)"
              borderRadius="4px"
              display="flex"
              alignItems="center"
              justifyContent="center"
              fontSize="xs"
              color="neon.cyan"
            >
              ⋮
            </Box>
          </Box>
        )}

        {/* Right Panel - WebRTC Video Feed */}
        <Box
          w={getRightPanelWidth()}
          h="100%"
          display={panelLayout === "ide-expanded" ? "none" : "block"}
          position="relative"
          overflow="hidden"
        >
          <Box h="100%" variant="glassPanel" borderRadius="0" p={4}>
            <VStack h="100%" spacing={4}>
              <Text variant="neonGlow" fontSize="lg">
                {showVideo ? `${robotNames[robot]?.name} Simulation Result` : "Robot Video Feed"}
              </Text>
              
              <Box 
                flex="1" 
                w="100%" 
                variant="neonBorder" 
                borderRadius="8px" 
                overflow="hidden"
                bg="rgba(0,0,0,0.5)"
              >
                {showVideo && videoUrl ? (
                  <video 
                    width="100%" 
                    height="100%" 
                    controls 
                    autoPlay
                    playsInline
                    muted
                    style={{ 
                      background: "#000",
                      objectFit: "contain"
                    }}
                  >
                    <source src={videoUrl} type="video/mp4" />
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <WebRTCVideoPlayer 
                    user={user}
                    authToken={authToken}
                    robotType={robot}
                    onError={(error) => {
                      toast({
                        title: "Video Stream Error",
                        description: error.message,
                        status: "error",
                        duration: 5000,
                        isClosable: true,
                      });
                    }}
                  />
                )}
              </Box>
              
              {showVideo && (
                <Button 
                  size="sm" 
                  variant="solid"
                  onClick={() => {
                    setShowVideo(false);
                    if (videoUrl) {
                      URL.revokeObjectURL(videoUrl);
                      setVideoUrl(null);
                    }
                  }}
                >
                  Back to Live Video Feed
                </Button>
              )}
            </VStack>
          </Box>
        </Box>
      </Box>

      {/* Logs Modal */}
      <Modal isOpen={isLogsOpen} onClose={onLogsClose} size="xl">
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent bg="rgba(26, 32, 44, 0.9)" backdropFilter="blur(12px)" border="1px solid rgba(0,255,200,0.3)">
          <ModalHeader color="white" fontFamily="'Orbitron', sans-serif">
            Robot Console Logs & Instructions
          </ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody pb={6} color="gray.300">
            <VStack spacing={4} align="start">
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Current Session:</Text>
                <Text>Robot Type: {robotNames[robot]?.name || robot}</Text>
                <Text>Status: Connected</Text>
                <Text>IDE: Eclipse Theia Ready</Text>
                <Text>Video Feed: {showVideo ? "Simulation Active" : "Live Stream Active"}</Text>
              </Box>
              
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Instructions:</Text>
                <VStack spacing={2} align="start" fontSize="sm">
                  <Text>• Use the IDE panel to write and execute robot code</Text>
                  <Text>• Monitor robot behavior through the video feed</Text>
                  <Text>• Use panel controls to expand/collapse views as needed</Text>
                  <Text>• Drag the center divider to resize panels</Text>
                  <Text>• Click "Get Real Result" to view simulation videos</Text>
                </VStack>
              </Box>
              
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Quick Actions:</Text>
                <HStack spacing={2} wrap="wrap">
                  <Button size="xs" variant="ghost">Refresh IDE</Button>
                  <Button size="xs" variant="ghost">Restart Robot</Button>
                  <Button size="xs" variant="ghost">Reset Session</Button>
                </HStack>
              </Box>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default NeonRobotConsole;