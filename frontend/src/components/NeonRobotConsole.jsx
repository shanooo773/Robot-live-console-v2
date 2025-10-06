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
import FileSelector from "./FileSelector";
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
  const [codeLoading, setCodeLoading] = useState(false);
  const [theiaStatus, setTheiaStatus] = useState(null);
  const [activeBookings, setActiveBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotNames, setRobotNames] = useState({});
  const [userMode, setUserMode] = useState("preview"); // "preview" or "booking"
  const [hasActiveBooking, setHasActiveBooking] = useState(false);
  
  // File selection state
  const [workspaceFiles, setWorkspaceFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [filesLoading, setFilesLoading] = useState(false);
  
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

  const checkTheiaStatusAndMode = async () => {
    try {
      const response = await fetch('/theia/status', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const status = await response.json();
        setTheiaStatus(status);
        setUserMode(status.user_mode || "preview");
        setHasActiveBooking(status.has_active_booking || false);
        
        console.log('User mode:', status.user_mode, 'Has active booking:', status.has_active_booking);
        return status;
      }
    } catch (error) {
      console.error('Error checking Theia status:', error);
    }
    return null;
  };

  useEffect(() => {
    const checkUserAccessAndMode = async () => {
      setLoading(true);
      await loadRobotNames();
      
      try {
        // Check Theia status and user mode - IDE access is now always available
        await checkTheiaStatusAndMode();
        
        if (user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode || 
            localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin') || 
            localStorage.getItem('isDummy') || localStorage.getItem('isDemoMode')) {
            
          // Demo users always have access
          setHasAccess(true);
          setAvailableRobots(['turtlebot', 'robot_arm', 'robot_hand']);
        } else if (authToken) {
          // Regular users - IDE access is always available
          setHasAccess(true);
          
          try {
            const bookings = await getMyActiveBookings(authToken);
            setActiveBookings(bookings);
            
            // Get robot types from all bookings (not just active ones)
            const robotTypes = [...new Set(bookings.map(booking => booking.robot_type))];
            setAvailableRobots(robotTypes.length > 0 ? robotTypes : ['turtlebot']);
            
            if (robotTypes.length > 0 && !robotTypes.includes(robot)) {
              setRobot(robotTypes[0]);
            }
            
            // Show mode-specific welcome message
            if (userMode === "preview") {
              toast({
                title: "Preview Mode Active",
                description: "IDE ready for code editing. Book a session for robot execution and live video.",
                status: "info",
                duration: 4000,
                isClosable: true,
              });
            } else {
              toast({
                title: "Booking Mode Active", 
                description: "Full robot access enabled - code execution and live video available.",
                status: "success",
                duration: 3000,
                isClosable: true,
              });
            }
            
          } catch (error) {
            console.error("Failed to fetch active bookings:", error);
            // Even if booking check fails, IDE access is still available
            setAvailableRobots(['turtlebot']);
            toast({
              title: "IDE Ready",
              description: "Development environment loaded. Some features may require booking.",
              status: "info",
              duration: 3000,
              isClosable: true,
            });
          }
        } else {
          setHasAccess(false);
        }
      } catch (error) {
        console.error("Access check failed:", error);
        toast({
          title: "IDE Access Error",
          description: "Unable to fully initialize. Please refresh the page.",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    };

    checkUserAccessAndMode();
  }, [authToken, user, toast, robot]);

  // Load workspace files when Theia status changes to running
  useEffect(() => {
    if (theiaStatus?.status === "running" && authToken) {
      loadWorkspaceFiles();
    }
  }, [theiaStatus?.status, authToken]);

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

  const loadWorkspaceFiles = async () => {
    setFilesLoading(true);
    try {
      const response = await fetch('/theia/workspace/files', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setWorkspaceFiles(data.files || []);
        
        // Auto-select first file if none selected
        if (!selectedFile && data.files && data.files.length > 0) {
          setSelectedFile(data.files[0]);
        }
      } else {
        console.error("Failed to load workspace files");
      }
    } catch (error) {
      console.error("Error loading workspace files:", error);
    } finally {
      setFilesLoading(false);
    }
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

  const handleRunCode = async () => {
    // Check if a file is selected
    if (!selectedFile) {
      toast({
        title: "No File Selected",
        description: "Please select a .py or .cpp file to run.",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    // Check if user is in preview mode and block robot execution
    if (userMode === "preview" && !hasActiveBooking) {
      toast({
        title: "Booking Required",
        description: "👉 Code execution on robot requires booking. You can still use the IDE to edit and save code.",
        status: "warning",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setCodeLoading(true);
    try {
      // This will push user code from workspace to the robot endpoint
      // Auto-start Theia container if not running
      const theiaResponse = await fetch('/theia/status', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (theiaResponse.ok) {
        const theiaStatusData = await theiaResponse.json();
        setTheiaStatus(theiaStatusData);
        
        // Update user mode based on response
        setUserMode(theiaStatusData.user_mode || "preview");
        setHasActiveBooking(theiaStatusData.has_active_booking || false);
        
        // Auto-start Theia if not running
        if (theiaStatusData.status !== "running") {
          toast({
            title: "Starting IDE",
            description: "Auto-starting development environment...",
            status: "info",
            duration: 3000,
            isClosable: true,
          });
          
          await fetch('/theia/start', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            }
          });
        }
      }

      // Fetch the actual file content from the workspace
      // Encode the path properly to handle subdirectories
      const encodedPath = selectedFile.path.split('/').map(encodeURIComponent).join('/');
      const fileResponse = await fetch(`/theia/workspace/file/${encodedPath}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!fileResponse.ok) {
        throw new Error('Failed to read file from workspace');
      }

      const fileData = await fileResponse.json();
      const fileContent = fileData.content;

      // Determine language from file extension
      const language = selectedFile.language;
      
      // Execute robot code with actual file content
      const response = await fetch('/robot/execute', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          robot_type: robot,
          code: fileContent,
          language: language,
          filename: selectedFile.name
        })
      });
      
      if (response.ok) {
        toast({
          title: "Code Executed",
          description: `${selectedFile.name} successfully sent to ${robotNames[robot]?.name || robot} robot.`,
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else {
        throw new Error('Failed to execute code');
      }
      
    } catch (error) {
      console.error("Failed to run code:", error);
      
      // Check if it's a booking-related error
      const errorMessage = error.message || "Unable to execute code";
      if (errorMessage.includes("booking") || errorMessage.includes("Book")) {
        toast({
          title: "Booking Required",
          description: "👉 " + errorMessage,
          status: "warning",
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Code Execution Failed",
          description: errorMessage,
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } finally {
      setCodeLoading(false);
    }
  };

  if (loading) {
    return (
      <Box h="100vh" w="100vw" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={6}>
          <Spinner size="xl" color="neon.cyan" />
          <Text variant="neonGlow" fontSize="lg">Initializing Development Environment...</Text>
        </VStack>
      </Box>
    );
  }

  // IDE access is now always available for authenticated users
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
      {/* Simplified Top Bar */}
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
          {/* Left side - User info */}
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
          </HStack>
          
          <Box flex="1" />
          
          {/* Center - Panel controls (keep resizer functionality) */}
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
          
          {/* Right side - Main actions (simplified to two main buttons) */}
          <HStack spacing={3}>
            <FileSelector 
              selectedFile={selectedFile}
              files={workspaceFiles}
              onSelect={setSelectedFile}
              isLoading={filesLoading}
              onRefresh={loadWorkspaceFiles}
            />
            
            {userMode === "preview" ? (
              <>
                <Tooltip 
                  label="👉 Code execution on robot requires booking."
                  placement="top"
                  bg="orange.500"
                >
                  <Button
                    size="sm"
                    colorScheme="gray"
                    onClick={handleRunCode}
                    isDisabled={true}
                  >
                    🚀 Run Code (Booking Required)
                  </Button>
                </Tooltip>
                <Button
                  size="sm"
                  colorScheme="orange"
                  onClick={onBack}
                >
                  📅 Book Service
                </Button>
              </>
            ) : (
              <Button
                size="sm"
                colorScheme="green"
                onClick={handleRunCode}
                isLoading={codeLoading}
                loadingText="Running..."
                disabled={codeLoading}
              >
                🚀 Run Code on Robot
              </Button>
            )}
            
            <Button
              size="sm"
              variant="outline"
              onClick={onLogsOpen}
            >
              View Logs
            </Button>
            
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
                ) : userMode === "preview" ? (
                  // Preview mode - show booking requirement message
                  <VStack 
                    justify="center" 
                    align="center" 
                    h="100%" 
                    spacing={6}
                    p={8}
                  >
                    <Text fontSize="4xl">📹</Text>
                    <VStack spacing={3} textAlign="center">
                      <Badge colorScheme="orange" fontSize="md" p={2}>
                        Preview Mode
                      </Badge>
                      <Text color="neon.cyan" fontSize="lg" fontWeight="bold">
                        Live Robot Feed
                      </Text>
                      <Text color="gray.300" maxW="300px">
                        👉 To access the real-time robot feed, please book the service.
                      </Text>
                    </VStack>
                    <Button 
                      colorScheme="orange" 
                      onClick={onBack}
                      size="md"
                      variant="neonPrimary"
                    >
                      📅 Book Robot Session
                    </Button>
                  </VStack>
                ) : (
                  // Booking mode - show WebRTC video player
                  <WebRTCVideoPlayer 
                    user={user}
                    authToken={authToken}
                    robotType={robot}
                    hasAccess={hasAccess}
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
              
              {/* Small Get Real Result button for simulation videos */}
              {hasAccess && (
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={handleGetRealResult}
                  isLoading={videoLoading}
                  loadingText="Loading..."
                >
                  Get Real Result
                </Button>
              )}
              
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
                  Back to Live Feed
                </Button>
              )}
            </VStack>
          </Box>
        </Box>
      </Box>

      {/* Enhanced Logs Modal */}
      <Modal isOpen={isLogsOpen} onClose={onLogsClose} size="xl">
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent bg="rgba(26, 32, 44, 0.9)" backdropFilter="blur(12px)" border="1px solid rgba(0,255,200,0.3)">
          <ModalHeader color="white" fontFamily="'Orbitron', sans-serif">
            Development Console Logs
          </ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody pb={6} color="gray.300">
            <VStack spacing={4} align="start">
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Current Session:</Text>
                <Text>Robot Type: {robotNames[robot]?.name || robot}</Text>
                <Text>IDE Status: Eclipse Theia {theiaStatus?.status === "running" ? "Running" : "Stopped"}</Text>
                <Text>WebRTC Status: {hasAccess ? "Available" : "Booking Required"}</Text>
                <Text>User: {user.name} {(user?.isDemoUser || user?.isDemoAdmin) ? "(Demo)" : ""}</Text>
              </Box>
              
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Container Lifecycle:</Text>
                <VStack spacing={1} align="start" fontSize="sm">
                  <Text color="gray.400">• IDE auto-starts on first access</Text>
                  <Text color="gray.400">• Available 24/7 for code preview and editing</Text>
                  <Text color="gray.400">• Persistent workspace in isolated container</Text>
                  <Text color="gray.400">• Auto-cleanup after configurable timeout</Text>
                </VStack>
              </Box>
              
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>WebRTC Events:</Text>
                <VStack spacing={1} align="start" fontSize="sm">
                  {hasAccess ? (
                    <>
                      <Text color="green.300">✓ WebRTC access granted - active booking detected</Text>
                      <Text color="gray.400">• Live robot feed available during session</Text>
                      <Text color="gray.400">• Direct WebRTC connection to robot</Text>
                    </>
                  ) : (
                    <>
                      <Text color="orange.300">⚠ WebRTC access restricted</Text>
                      <Text color="gray.400">• To access the robot feed, please book a session</Text>
                      <Text color="gray.400">• IDE remains available for code development</Text>
                    </>
                  )}
                </VStack>
              </Box>
              
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Code Push Results:</Text>
                <VStack spacing={1} align="start" fontSize="sm">
                  <Text color="gray.400">• "Run Code" pushes workspace code to robot endpoint</Text>
                  <Text color="gray.400">• Code execution logged for debugging</Text>
                  <Text color="gray.400">• Results available in robot simulation videos</Text>
                </VStack>
              </Box>
              
              <Box>
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Usage Instructions:</Text>
                <VStack spacing={1} align="start" fontSize="sm">
                  <Text>• Use the IDE panel to write and test robot code (always available)</Text>
                  <Text>• {userMode === "preview" ? "Book a session to execute code on robot" : "Click 'Run Code' to execute code on the robot"}</Text>
                  <Text>• Monitor execution through the video feed (booking mode only)</Text>
                  <Text>• Drag the center divider to resize panels</Text>
                  <Text>• Preview Mode: Code editing only | Booking Mode: Full robot access</Text>
                </VStack>
              </Box>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default NeonRobotConsole;