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
  Divider,
  Flex,
  Tooltip
} from "@chakra-ui/react";
import TheiaIDE from "./TheiaIDE";
import WebRTCVideoPlayer from "./WebRTCVideoPlayer";
import RobotSelector from "./RobotSelector";
import { checkAccess, getVideo, getMyActiveBookings, getAvailableRobots } from "../api";

const CodeEditor = ({ user, slot, authToken, onBack, onLogout }) => {
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [hasAccess, setHasAccess] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [videoLoading, setVideoLoading] = useState(false);
  const [activeBookings, setActiveBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotNames, setRobotNames] = useState({});
  
  // New state for panel management
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const [panelView, setPanelView] = useState("split"); // "split", "ide-only", "video-only"
  
  const dividerRef = useRef(null);
  const containerRef = useRef(null);
  const toast = useToast();

  // Panel resize handlers
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !containerRef.current) return;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
    
    // Constrain between 20% and 80%
    const constrainedWidth = Math.max(20, Math.min(80, newLeftWidth));
    setLeftPanelWidth(constrainedWidth);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
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

  // Panel view handlers
  const handleExpandIDE = () => {
    setPanelView("ide-only");
  };

  const handleExpandVideo = () => {
    setPanelView("video-only");
  };

  const handleResetSplit = () => {
    setPanelView("split");
    setLeftPanelWidth(50);
  };

  const loadRobotNames = async () => {
    try {
      const robotData = await getAvailableRobots();
      const robotDetails = robotData.details || {};
      
      // Convert to format expected by CodeEditor
      const formattedRobots = {};
      Object.keys(robotDetails).forEach(robotType => {
        const robot = robotDetails[robotType];
        let emoji = "🤖"; // default emoji
        if (robotType.includes("arm")) emoji = "🦾";
        else if (robotType.includes("hand")) emoji = "🤲";
        else if (robotType.includes("turtle")) emoji = "🤖";
        
        formattedRobots[robotType] = {
          name: robot.name || robotType,
          emoji: emoji
        };
      });
      
      setRobotNames(formattedRobots);
    } catch (error) {
      console.error('Error loading robot names:', error);
      // Set fallback robot names for demo users or when API fails
      const fallbackRobotNames = {
        turtlebot: { name: "TurtleBot Navigation", emoji: "🤖" },
        robot_arm: { name: "6-DOF Robot Arm", emoji: "🦾" },
        dexterous_hand: { name: "Dexterous Hand", emoji: "🤲" }
      };
      setRobotNames(fallbackRobotNames);
    }
  };

  useEffect(() => {
    // Check if user has access to Monaco Editor and fetch active bookings
    const checkUserAccess = async () => {
      try {
        // Check for demo user access
        const isDemoUser = localStorage.getItem('isDemoUser');
        const isDemoAdmin = localStorage.getItem('isDemoAdmin');
        const isDummy = localStorage.getItem('isDummy');
        const isDemoMode = localStorage.getItem('isDemoMode');
        
        // Load robot names from API for all users (including demo users)
        await loadRobotNames();
        
        // Check for demo user access - give immediate access but only for admin-created robots
        if (isDemoUser || isDemoAdmin || isDummy || isDemoMode || user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode) {
          try {
            // Demo users get access to all available admin-created robots
            const robotData = await getAvailableRobots();
            const availableRobotTypes = robotData.robots || [];
            
            setAvailableRobots(availableRobotTypes);
            setHasAccess(availableRobotTypes.length > 0);
            
            if (availableRobotTypes.length > 0 && !availableRobotTypes.includes(robot)) {
              setRobot(availableRobotTypes[0]);
            }
            
            if (availableRobotTypes.length === 0) {
              toast({
                title: "No Robots Available",
                description: "No robots have been configured by admin yet.",
                status: "info",
                duration: 5000,
                isClosable: true,
              });
            }
          } catch (error) {
            // If API fails in demo mode, provide fallback demo robots
            console.warn("API failed in demo mode, using fallback robots:", error);
            const fallbackRobots = ["turtlebot", "robot_arm", "dexterous_hand"];
            setAvailableRobots(fallbackRobots);
            setHasAccess(true);
            setRobot(fallbackRobots[0]);
          }
        } else if (authToken) {
          // Regular access check for authenticated users
          try {
            const bookings = await getMyActiveBookings(authToken);
            setActiveBookings(bookings);
            
            // Extract unique robot types from active bookings
            const robotTypes = [...new Set(bookings.map(booking => booking.robot_type))];
            setAvailableRobots(robotTypes);
            
            // Set access based on having active bookings
            setHasAccess(robotTypes.length > 0);
            
            // If user has bookings but current robot is not available, switch to first available
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

  const onSelect = (robotType) => {
    setRobot(robotType);
    setShowVideo(false); // Reset video when robot changes
    setVideoUrl(null);
  };

  const handleGetRealResult = async () => {
    setVideoLoading(true);
    try {
      if (authToken) {
        // Regular video loading with authentication
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
        // Demo mode - show success message but no video (unless admin has configured videos)
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
      <Box 
        height="100vh" 
        width="100vw" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        bg="linear-gradient(135deg, #0a0f23 0%, #1a1a2e 50%, #16213e 100%)"
      >
        <VStack spacing={6}>
          <Spinner 
            size="xl" 
            color="rgba(0, 255, 200, 0.8)"
            thickness="4px"
            speed="0.8s"
          />
          <Text 
            color="rgba(0, 255, 200, 0.9)" 
            fontSize="lg"
            fontFamily="'Orbitron', sans-serif"
            animation="neonGlow 2s ease-in-out infinite alternate"
          >
            Initializing Neural Interface...
          </Text>
        </VStack>
      </Box>
    );
  }

  if (!hasAccess) {
    return (
      <Box 
        height="100vh" 
        width="100vw" 
        display="flex" 
        alignItems="center" 
        justifyContent="center"
        bg="linear-gradient(135deg, #0a0f23 0%, #1a1a2e 50%, #16213e 100%)"
      >
        <VStack spacing={6} maxW="md" textAlign="center">
          <Alert 
            status="warning" 
            bg="rgba(255, 165, 0, 0.1)" 
            border="1px solid rgba(255, 165, 0, 0.3)"
            borderRadius="16px"
            backdropFilter="blur(12px)"
          >
            <AlertIcon color="orange.300" />
            <Box>
              <Text fontWeight="bold" color="orange.300">Neural Link Denied</Text>
              <Text color="orange.200">Active booking required for console access.</Text>
            </Box>
          </Alert>
          <Button 
            variant="neonPill" 
            onClick={onBack}
            leftIcon={<FaHome />}
          >
            Return to Base
          </Button>
        </VStack>
      </Box>
    );
  }

  return (
    <Box 
      height="100vh" 
      width="100vw" 
      overflow="hidden"
      bg="linear-gradient(135deg, #0a0f23 0%, #1a1a2e 50%, #16213e 100%)"
      position="relative"
    >
      {/* Animated Background */}
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        opacity="0.05"
        background="linear-gradient(-45deg, rgba(0, 255, 200, 0.1), rgba(0, 191, 255, 0.1), rgba(138, 43, 226, 0.1), rgba(255, 20, 147, 0.1))"
        backgroundSize="400% 400%"
        animation="neonWave 15s ease infinite"
        zIndex="0"
      />

      {/* Top Navigation Bar */}
      <Box
        position="relative"
        zIndex="10"
        bg="rgba(10, 15, 35, 0.8)"
        backdropFilter="blur(16px)"
        borderBottom="1px solid rgba(0, 255, 200, 0.3)"
        boxShadow="0 4px 20px rgba(0, 255, 200, 0.1)"
        px={6}
        py={4}
      >
        <Flex justify="space-between" align="center">
          {/* Left: Session Info */}
          <HStack spacing={6}>
            <HStack spacing={3}>
              <Avatar 
                size="sm" 
                name={user.name}
                bg="rgba(0, 255, 200, 0.2)"
                color="rgba(0, 255, 200, 1)"
              />
              <VStack align="start" spacing={0}>
                <HStack spacing={2}>
                  <Text 
                    color="rgba(0, 255, 200, 0.9)" 
                    fontWeight="bold"
                    fontSize="sm"
                    fontFamily="'Orbitron', sans-serif"
                  >
                    {user.name}
                  </Text>
                  {(user?.isDemoUser || user?.isDemoAdmin || localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin')) && (
                    <Badge variant="neonPill" colorScheme="orange">
                      DEMO
                    </Badge>
                  )}
                </HStack>
                <Text color="rgba(255, 255, 255, 0.6)" fontSize="xs">
                  Neural Link Active
                </Text>
              </VStack>
            </HStack>

            <Divider orientation="vertical" h="40px" borderColor="rgba(0, 255, 200, 0.3)" />

            {/* Robot Info */}
            <HStack spacing={3}>
              <Text fontSize="lg">{robotNames[robot]?.emoji || "🤖"}</Text>
              <VStack align="start" spacing={0}>
                <Text 
                  color="rgba(0, 255, 200, 0.9)" 
                  fontWeight="600"
                  fontSize="sm"
                  fontFamily="'Orbitron', sans-serif"
                >
                  {robotNames[robot]?.name || robot}
                </Text>
                <Badge variant="neonPill" colorScheme="green">
                  ONLINE
                </Badge>
              </VStack>
            </HStack>
          </HStack>

          {/* Center: Main Controls */}
          <HStack spacing={3}>
            <RobotSelector 
              robot={robot} 
              onSelect={onSelect} 
              availableRobots={availableRobots} 
            />
            
            <Tooltip label="Execute Simulation">
              <Button 
                variant="solid"
                onClick={handleGetRealResult}
                isLoading={videoLoading}
                loadingText="Executing..."
                size="sm"
              >
                ▶ Execute
              </Button>
            </Tooltip>

            <Tooltip label="Connect Video Feed">
              <Button
                variant="solid"
                size="sm"
                aria-label="Video Feed"
              >
                📹
              </Button>
            </Tooltip>

            <Tooltip label="Refresh Console">
              <Button
                variant="solid"
                size="sm"
                aria-label="Refresh"
              >
                🔄
              </Button>
            </Tooltip>
          </HStack>

          {/* Right: Panel & System Controls */}
          <HStack spacing={3}>
            {/* Panel View Controls */}
            <HStack spacing={1}>
              <Tooltip label="Expand IDE">
                <Button
                  variant={panelView === "ide-only" ? "solid" : "ghost"}
                  size="sm"
                  onClick={handleExpandIDE}
                  aria-label="Expand IDE"
                >
                  ⬅
                </Button>
              </Tooltip>
              
              <Tooltip label="Reset Split View">
                <Button
                  variant={panelView === "split" ? "solid" : "ghost"}
                  size="sm"
                  onClick={handleResetSplit}
                  aria-label="Split View"
                >
                  ↔
                </Button>
              </Tooltip>
              
              <Tooltip label="Expand Video">
                <Button
                  variant={panelView === "video-only" ? "solid" : "ghost"}
                  size="sm"
                  onClick={handleExpandVideo}
                  aria-label="Expand Video"
                >
                  ➡
                </Button>
              </Tooltip>
            </HStack>

            <Divider orientation="vertical" h="40px" borderColor="rgba(0, 255, 200, 0.3)" />

            <Button 
              variant="ghost" 
              onClick={onBack}
              size="sm"
            >
              🏠 Base
            </Button>
            
            <Button 
              variant="ghost" 
              onClick={onLogout}
              size="sm"
            >
              🚪 Logout
            </Button>
          </HStack>
        </Flex>
      </Box>

      {/* Main Content Area */}
      <Box
        position="relative"
        height="calc(100vh - 80px)"
        width="100%"
        ref={containerRef}
        display="flex"
        zIndex="5"
      >
        {/* Left Panel - IDE */}
        <Box
          width={
            panelView === "ide-only" ? "100%" :
            panelView === "video-only" ? "0%" :
            `${leftPanelWidth}%`
          }
          height="100%"
          overflow="hidden"
          transition="width 0.3s ease"
          bg="rgba(10, 15, 35, 0.4)"
          backdropFilter="blur(8px)"
          border="1px solid rgba(0, 255, 200, 0.2)"
          borderRight={panelView === "split" ? "none" : "1px solid rgba(0, 255, 200, 0.2)"}
        >
          {(panelView === "ide-only" || panelView === "split") && (
            <Box height="100%" p={4}>
              <VStack spacing={4} height="100%">
                <HStack justify="space-between" width="100%">
                  <Text 
                    fontSize="lg" 
                    fontWeight="600"
                    color="rgba(0, 255, 200, 0.9)"
                    fontFamily="'Orbitron', sans-serif"
                    textShadow="0 0 10px rgba(0, 255, 200, 0.5)"
                  >
                    Neural Development Interface
                  </Text>
                  <Badge variant="neonPill">
                    Theia IDE
                  </Badge>
                </HStack>
                
                <Box 
                  width="100%" 
                  height="calc(100% - 60px)"
                  bg="rgba(0, 0, 0, 0.3)"
                  border="1px solid rgba(0, 255, 200, 0.3)"
                  borderRadius="12px"
                  overflow="hidden"
                  position="relative"
                >
                  <TheiaIDE 
                    user={user} 
                    authToken={authToken}
                    onError={(error) => {
                      toast({
                        title: "Neural Interface Error",
                        description: error.message,
                        status: "error",
                        duration: 5000,
                        isClosable: true,
                      });
                    }}
                  />
                </Box>
              </VStack>
            </Box>
          )}
        </Box>

        {/* Draggable Divider */}
        {panelView === "split" && (
          <Box
            ref={dividerRef}
            width="4px"
            height="100%"
            bg="rgba(0, 255, 200, 0.3)"
            cursor="col-resize"
            onMouseDown={handleMouseDown}
            _hover={{
              bg: "rgba(0, 255, 200, 0.5)",
              boxShadow: "0 0 10px rgba(0, 255, 200, 0.4)"
            }}
            transition="all 0.2s ease"
            position="relative"
            zIndex="10"
          >
            <Box
              position="absolute"
              top="50%"
              left="50%"
              transform="translate(-50%, -50%)"
              width="20px"
              height="40px"
              bg="rgba(0, 255, 200, 0.2)"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
              fontSize="12px"
              color="rgba(0, 255, 200, 0.8)"
            >
              ↔
            </Box>
          </Box>
        )}

        {/* Right Panel - Video Feed */}
        <Box
          width={
            panelView === "video-only" ? "100%" :
            panelView === "ide-only" ? "0%" :
            `${100 - leftPanelWidth}%`
          }
          height="100%"
          overflow="hidden"
          transition="width 0.3s ease"
          bg="rgba(10, 15, 35, 0.4)"
          backdropFilter="blur(8px)"
          border="1px solid rgba(0, 255, 200, 0.2)"
          borderLeft={panelView === "split" ? "none" : "1px solid rgba(0, 255, 200, 0.2)"}
        >
          {(panelView === "video-only" || panelView === "split") && (
            <Box height="100%" p={4}>
              <VStack spacing={4} height="100%">
                <HStack justify="space-between" width="100%">
                  <Text 
                    fontSize="lg" 
                    fontWeight="600"
                    color="rgba(0, 255, 200, 0.9)"
                    fontFamily="'Orbitron', sans-serif"
                    textShadow="0 0 10px rgba(0, 255, 200, 0.5)"
                  >
                    {showVideo ? `${robotNames[robot]?.name} Neural Feed` : "Robot Visual Interface"}
                  </Text>
                  <Badge variant="neonPill">
                    WebRTC
                  </Badge>
                </HStack>
                
                <Box 
                  width="100%" 
                  height="calc(100% - 60px)"
                  bg="rgba(0, 0, 0, 0.3)"
                  border="1px solid rgba(0, 255, 200, 0.3)"
                  borderRadius="12px"
                  overflow="hidden"
                  position="relative"
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
                        borderRadius: "12px"
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
                          title: "Video Neural Link Error",
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
                    variant="neonPill"
                    size="sm"
                    onClick={() => {
                      setShowVideo(false);
                      if (videoUrl) {
                        URL.revokeObjectURL(videoUrl);
                        setVideoUrl(null);
                      }
                    }}
                  >
                    Return to Live Feed
                  </Button>
                )}
              </VStack>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default CodeEditor;
