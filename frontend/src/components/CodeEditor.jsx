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
  const [hasAccess, setHasAccess] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [videoLoading, setVideoLoading] = useState(false);
  const [activeBookings, setActiveBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotNames, setRobotNames] = useState({});
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
      <Container maxW="7xl" py={8}>
        <VStack spacing={6} justify="center" minH="60vh">
          <Spinner size="xl" color="blue.500" />
          <Text color="white">Checking access permissions...</Text>
        </VStack>
      </Container>
    );
  }

  if (!hasAccess) {
    return (
      <Container maxW="7xl" py={8}>
        <VStack spacing={6}>
          <Alert status="warning" bg="orange.900" borderRadius="md">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold">Access Denied</Text>
              <Text>You need an active booking to access the development console.</Text>
            </Box>
          </Alert>
          <Button colorScheme="blue" onClick={onBack}>
            Go Back to Booking
          </Button>
        </VStack>
      </Container>
    );
  }

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
                <Text fontSize="xl" fontWeight="bold" color="white">
                  Development Console - Robot Control Interface
                </Text>
                <HStack spacing={4}>
                  <RobotSelector robot={robot} onSelect={onSelect} availableRobots={availableRobots} />
                  <Badge colorScheme="blue" fontSize="xs">
                    Eclipse Theia IDE + Robot Video Feed
                  </Badge>
                </HStack>
              </VStack>
              <Button 
                colorScheme="green" 
                onClick={handleGetRealResult}
                isLoading={videoLoading}
                loadingText="Loading Video..."
                disabled={videoLoading}
              >
                Get Real Result
              </Button>
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
                  <Text fontSize="lg" color="white" fontWeight="bold">
                    {showVideo ? `${robotNames[robot].name} Simulation Result` : "Robot Video Feed"}
                  </Text>
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
