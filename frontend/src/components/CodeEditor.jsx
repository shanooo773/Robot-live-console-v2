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
import RTSPVideoPlayer from "./RTSPVideoPlayer";
import RobotSelector from "./RobotSelector";
import { checkAccess, getVideo } from "../api";

const robotNames = {
  turtlebot: { name: "TurtleBot3", emoji: "🤖" },
  arm: { name: "Robot Arm", emoji: "🦾" },
  hand: { name: "Robot Hand", emoji: "🤲" },
};

const CodeEditor = ({ user, slot, authToken, onBack, onLogout }) => {
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [selectedRobotData, setSelectedRobotData] = useState(null); // Store full robot object
  const [hasAccess, setHasAccess] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [videoLoading, setVideoLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    // Check if user has access to Monaco Editor
    const checkUserAccess = async () => {
      try {
        // Check for demo user access
        const isDemoUser = localStorage.getItem('isDemoUser');
        const isDemoAdmin = localStorage.getItem('isDemoAdmin');
        const isDummy = localStorage.getItem('isDummy');
        const isDemoMode = localStorage.getItem('isDemoMode');
        
        if (isDemoUser || isDemoAdmin || isDummy || isDemoMode || user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode) {
          // Demo users get immediate access
          setHasAccess(true);
          setLoading(false);
          return;
        }
        
        // Regular access check for non-demo users
        if (authToken) {
          const accessData = await checkAccess(authToken);
          setHasAccess(accessData.has_access);
          if (!accessData.has_access) {
            toast({
              title: "Access Denied",
              description: "You need to complete a booking before accessing the development console.",
              status: "warning",
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
  }, [authToken, user, toast]);

  const onSelect = (robotId, robotData) => {
    // Handle both new robot selection (with ID and data) and backward compatibility
    if (robotData) {
      // New format: robot object with id, name, type
      setRobot(robotId);  // Store robot ID
      setSelectedRobotData(robotData);  // Store full robot data
    } else {
      // Backward compatibility: robotId is actually robotType
      setRobot(robotId);
      setSelectedRobotData({ type: robotId, name: robotNames[robotId]?.name || robotId });
    }
    setShowVideo(false); // Reset video when robot changes
    setVideoUrl(null);
  };

  const handleGetRealResult = async () => {
    setVideoLoading(true);
    try {
      if (authToken) {
        // Get robot type for video API (backward compatibility)
        const robotType = selectedRobotData ? selectedRobotData.type : robot;
        // Regular video loading with authentication
        const videoBlob = await getVideo(robotType, authToken);
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
      } else if (user?.isDemoMode) {
        // Demo mode - show success message but no video
        toast({
          title: "Demo Mode",
          description: `In demo mode, ${robotNames[robot].name} simulation would display here. Full video access requires account registration.`,
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
              <Text>You need to complete a booking before accessing the development console.</Text>
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
                        <Text fontSize="lg">{robotNames[slot.robotType].emoji}</Text>
                        <Text color="gray.300">
                          {robotNames[slot.robotType].name}
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
                  <RobotSelector robot={robot} onSelect={onSelect} />
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
                        style={{ background: "#000" }}
                      >
                        <source src={videoUrl} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    ) : (
                      <RTSPVideoPlayer 
                        user={user}
                        authToken={authToken}
                        robot={selectedRobotData || robot}  // Pass robot data or fallback to robot type
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
