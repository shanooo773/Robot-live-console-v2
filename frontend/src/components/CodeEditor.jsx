import { useRef, useState, useEffect } from "react";
import { 
  Box, 
  HStack, 
  VStack, 
  Text, 
  Button, 
  Avatar, 
  Badge,
  Container,
  Card,
  CardBody,
  CardHeader,
  Divider,
  useToast,
  Spinner,
  Alert,
  AlertIcon
} from "@chakra-ui/react";
import TheiaIDE from "./TheiaIDE";
import WebRTCVideoPlayer from "./WebRTCVideoPlayer";
import RobotSelector from "./RobotSelector";
import { checkAccess, getVideo, getMyActiveBookings, getAvailableRobots } from "../api";

const CodeEditor = ({ user, slot, authToken, onBack, onLogout }) => {
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [showVideo, setShowVideo] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [videoLoading, setVideoLoading] = useState(false);
  const [activeBookings, setActiveBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotNames, setRobotNames] = useState({});
  const [userMode, setUserMode] = useState("preview"); // "preview" or "booking"
  const [hasActiveBooking, setHasActiveBooking] = useState(false);
  const [theiaStatus, setTheiaStatus] = useState(null);
  const toast = useToast();

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
      // Set empty robot names for non-demo users
      setRobotNames({});
    }
  };

  const checkTheiaStatusAndMode = async () => {
    try {
      // Check Theia status which now includes user mode information
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
        
        // Log the current mode for debugging
        console.log('User mode:', status.user_mode, 'Has active booking:', status.has_active_booking);
        
        return status;
      } else {
        console.error('Failed to check Theia status');
        return null;
      }
    } catch (error) {
      console.error('Error checking Theia status:', error);
      return null;
    }
  };

  useEffect(() => {
    // Check user access and mode - IDE access is now always available for authenticated users
    const checkUserAccessAndMode = async () => {
      try {
        // Load robot names from API for all users
        await loadRobotNames();
        
        // Check Theia status and user mode (preview vs booking)
        const theiaStatus = await checkTheiaStatusAndMode();
        
        // Check for demo user access
        const isDemoUser = localStorage.getItem('isDemoUser');
        const isDemoAdmin = localStorage.getItem('isDemoAdmin');
        const isDummy = localStorage.getItem('isDummy');
        const isDemoMode = localStorage.getItem('isDemoMode');
        
        if (isDemoUser || isDemoAdmin || isDummy || isDemoMode || user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode) {
          // Demo users get access to all available admin-created robots
          const robotData = await getAvailableRobots();
          const availableRobotTypes = robotData.robots || [];
          
          setAvailableRobots(availableRobotTypes);
          
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
        } else if (authToken) {
          // Regular users - IDE access is always available, but check for active bookings
          try {
            const bookings = await getMyActiveBookings(authToken);
            setActiveBookings(bookings);
            
            // Extract unique robot types from all bookings (not just active ones)
            const robotTypes = [...new Set(bookings.map(booking => booking.robot_type))];
            setAvailableRobots(robotTypes);
            
            // If user has bookings but current robot is not available, switch to first available
            if (robotTypes.length > 0 && !robotTypes.includes(robot)) {
              setRobot(robotTypes[0]);
            }
            
            // Show appropriate welcome message based on mode
            if (userMode === "preview") {
              toast({
                title: "Welcome to Preview Mode",
                description: "You can edit and save code. Book a session to run code on robot and view live feed.",
                status: "info", 
                duration: 5000,
                isClosable: true,
              });
            } else {
              toast({
                title: "Booking Mode Active",
                description: "Full robot access available - code execution and live video feed enabled.",
                status: "success",
                duration: 3000,
                isClosable: true,
              });
            }
            
          } catch (error) {
            console.error("Failed to fetch bookings:", error);
            // Even if booking check fails, IDE access is still available
            toast({
              title: "IDE Ready",
              description: "Development environment loaded. Some features may require booking.",
              status: "info",
              duration: 3000,
              isClosable: true,
            });
          }
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

  const onSelect = (robotType) => {
    setRobot(robotType);
    setShowVideo(false); // Reset video when robot changes
    setVideoUrl(null);
  };

  const handleGetRealResult = async () => {
    // In preview mode, show booking requirement message
    if (userMode === "preview" && !hasActiveBooking) {
      toast({
        title: "Booking Required",
        description: "👉 To access the real-time robot feed, please book the service.",
        status: "warning",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setVideoLoading(true);
    try {
      if (authToken) {
        // Video loading with authentication (booking mode)
        const videoBlob = await getVideo(robot, authToken);
        const url = URL.createObjectURL(videoBlob);
        setVideoUrl(url);
        setShowVideo(true);
        toast({
          title: "Video Loaded",
          description: `${robotNames[robot]?.name || robot} simulation video is now playing.`,
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
      const errorMessage = error.response?.data?.detail || "Unable to load video feed.";
      
      // Show booking-specific error message if it's a booking-related error
      if (errorMessage.includes("book")) {
        toast({
          title: "Booking Required", 
          description: "👉 " + errorMessage,
          status: "warning",
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Video Load Failed",
          description: errorMessage,
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } finally {
      setVideoLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxW="7xl" py={8}>
        <VStack spacing={6} justify="center" minH="60vh">
          <Spinner size="xl" color="blue.500" />
          <Text color="white">Initializing development environment...</Text>
        </VStack>
      </Container>
    );
  }

  // IDE access is now always available for authenticated users
  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6}>
        {/* Session Header */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <VStack spacing={4}>
              <HStack justify="space-between" w="full">
                <VStack align="start" spacing={2}>
                  <HStack>
                    <Avatar size="sm" name={user.name} />
                    <VStack align="start" spacing={0}>
                      <HStack spacing={2}>
                        <Text color="white" fontWeight="bold">{user.name}</Text>
                        {(user?.isDemoUser || user?.isDemoAdmin || localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin')) && (
                          <Badge colorScheme="orange" fontSize="xs">
                            DEMO MODE
                          </Badge>
                        )}
                      </HStack>
                      <Text color="gray.400" fontSize="sm">{user.email}</Text>
                    </VStack>
                  </HStack>
                  
                  {slot && (
                    <HStack spacing={4}>
                      <Badge colorScheme="green">Development Session Active</Badge>
                      <HStack>
                        <Text fontSize="lg">{robotNames[slot.robotType]?.emoji || "🤖"}</Text>
                        <Text color="gray.300">
                          {robotNames[slot.robotType]?.name || slot.robotType}
                        </Text>
                      </HStack>
                      <Text color="gray.400">
                        {new Date(slot.date).toLocaleDateString('en-US', { 
                          month: 'short', 
                          day: 'numeric' 
                        })} at {slot.startTime}
                      </Text>
                    </HStack>
                  )}
                </VStack>
                
                <HStack>
                  <Button variant="ghost" onClick={onBack} color="gray.400">
                    ← Back to Booking
                  </Button>
                  <Button variant="ghost" onClick={onLogout} color="gray.400">
                    Logout
                  </Button>
                </HStack>
              </HStack>
            </VStack>
          </CardHeader>
        </Card>

        {/* Main IDE and Video Panel */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between" align="center">
              <VStack align="start" spacing={1}>
                <HStack spacing={3}>
                  <Text fontSize="xl" fontWeight="bold" color="white">
                    Development Console
                  </Text>
                  {userMode === "preview" ? (
                    <Badge colorScheme="orange" fontSize="sm">
                      Preview Mode – Book to run code on robot and view live feed
                    </Badge>
                  ) : (
                    <Badge colorScheme="green" fontSize="sm">
                      Booking Mode – Full robot access available
                    </Badge>
                  )}
                </HStack>
                <HStack spacing={4}>
                  <RobotSelector robot={robot} onSelect={onSelect} availableRobots={availableRobots} />
                  <Badge colorScheme="blue" fontSize="xs">
                    Eclipse Theia IDE {userMode === "booking" ? "+ Robot Control" : "(Code Preview)"}
                  </Badge>
                </HStack>
              </VStack>
              <VStack spacing={2}>
                {userMode === "preview" ? (
                  <Button 
                    colorScheme="orange" 
                    onClick={onBack}
                    size="sm"
                  >
                    📅 Book Service for Robot Access
                  </Button>
                ) : (
                  <Button 
                    colorScheme="green" 
                    onClick={handleGetRealResult}
                    isLoading={videoLoading}
                    loadingText="Loading Video..."
                    disabled={videoLoading}
                    size="sm"
                  >
                    📹 Get Live Robot Feed
                  </Button>
                )}
              </VStack>
            </HStack>
          </CardHeader>
          <CardBody>
            <HStack spacing={6} align="start">
              {/* Left Panel - Eclipse Theia IDE */}
              <Box w="50%">
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
              
              {/* Right Panel - Robot Video Feed */}
              <Box w="50%">
                <VStack spacing={4} align="start" h="100%">
                  <HStack justify="space-between" w="full">
                    <Text fontSize="lg" color="white" fontWeight="bold">
                      {showVideo ? `${robotNames[robot]?.name || robot} Simulation Result` : "Robot Video Feed"}
                    </Text>
                    {userMode === "preview" && (
                      <Badge colorScheme="orange" fontSize="xs">
                        Booking Required
                      </Badge>
                    )}
                  </HStack>
                  
                  <Box w="full" h="75vh" border="1px solid" borderColor="gray.600" borderRadius="md" overflow="hidden">
                    {showVideo && videoUrl ? (
                      <video 
                        width="100%" 
                        height="100%" 
                        controls 
                        autoPlay
                        playsInline
                        muted
                        style={{ background: "#000" }}
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
                        bg="gray.900" 
                        borderRadius="md"
                        spacing={4}
                        p={8}
                      >
                        <Text fontSize="3xl">📹</Text>
                        <Text color="orange.200" textAlign="center" fontSize="lg" fontWeight="bold">
                          Preview Mode
                        </Text>
                        <Text color="gray.300" textAlign="center">
                          👉 To access the real-time robot feed, please book the service.
                        </Text>
                        <Button 
                          colorScheme="orange" 
                          onClick={onBack}
                          size="sm"
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
                      colorScheme="blue" 
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
            </HStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default CodeEditor;
