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
import { checkAccess, startTheiaIDE, getTheiaStatus } from "../api";

const robotNames = {
  turtlebot: { name: "TurtleBot3", emoji: "🤖" },
  arm: { name: "Robot Arm", emoji: "🦾" },
  hand: { name: "Robot Hand", emoji: "🤲" },
};

const VPS_URL = import.meta.env.VITE_VPS_URL || "http://172.104.207.139";

const CodeEditor = ({ user, slot, authToken, onBack, onLogout }) => {
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [hasAccess, setHasAccess] = useState(false);
  const [theiaUrl, setTheiaUrl] = useState(null);
  const [theiaLoading, setTheiaLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  useEffect(() => {
    // Check if user has access and start Theia IDE
    const checkUserAccessAndStartTheia = async () => {
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
          toast({
            title: "Demo Mode",
            description: "In demo mode, Theia IDE would be available here. Full access requires account registration.",
            status: "info",
            duration: 5000,
            isClosable: true,
          });
          return;
        }
        
        // Regular access check for non-demo users
        if (authToken) {
          const accessData = await checkAccess(authToken);
          setHasAccess(accessData.has_access);
          
          if (accessData.has_access) {
            // Start Theia IDE
            setTheiaLoading(true);
            try {
              const theiaData = await startTheiaIDE(authToken);
              if (theiaData.success && !theiaData.demo_mode) {
                setTheiaUrl(theiaData.theia_url);
                toast({
                  title: "Theia IDE Ready",
                  description: "Your development environment is starting up...",
                  status: "success",
                  duration: 3000,
                  isClosable: true,
                });
              }
            } catch (error) {
              console.error("Failed to start Theia:", error);
              toast({
                title: "Theia Startup Failed",
                description: "Unable to start development environment. Please try again.",
                status: "error",
                duration: 5000,
                isClosable: true,
              });
            } finally {
              setTheiaLoading(false);
            }
          } else {
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

    checkUserAccessAndStartTheia();
  }, [authToken, user, toast]);

  const onSelect = (robotType) => {
    setRobot(robotType);
  };

  const handleRefreshTheia = async () => {
    if (!authToken) return;
    
    setTheiaLoading(true);
    try {
      const theiaData = await startTheiaIDE(authToken);
      if (theiaData.success && !theiaData.demo_mode) {
        setTheiaUrl(theiaData.theia_url);
        toast({
          title: "Theia IDE Refreshed",
          description: "Development environment reloaded successfully.",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Failed to refresh Theia:", error);
      toast({
        title: "Refresh Failed",
        description: "Unable to refresh development environment.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setTheiaLoading(false);
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

        {/* Main Development and Camera Panel */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Text fontSize="xl" fontWeight="bold" color="white">
                Development Console - Theia IDE + Robot Camera Feed
              </Text>
              <Button 
                colorScheme="blue" 
                onClick={handleRefreshTheia}
                isLoading={theiaLoading}
                loadingText="Loading IDE..."
                disabled={theiaLoading || !hasAccess}
              >
                Refresh IDE
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            <HStack spacing={6} align="start">
              {/* Left Panel - Theia IDE */}
              <Box w="50%">
                <VStack spacing={4} align="start">
                  <HStack spacing={4}>
                    <Text fontSize="lg" color="white" fontWeight="bold">
                      Eclipse Theia IDE
                    </Text>
                    {theiaUrl && (
                      <Badge colorScheme="green" fontSize="xs">
                        RUNNING
                      </Badge>
                    )}
                  </HStack>
                  <Box w="full" h="75vh" border="1px solid" borderColor="gray.600" borderRadius="md" overflow="hidden">
                    {theiaLoading ? (
                      <VStack justify="center" h="100%" bg="gray.900">
                        <Spinner size="xl" color="blue.500" />
                        <Text color="white">Starting Theia IDE...</Text>
                      </VStack>
                    ) : theiaUrl ? (
                      <iframe
                        src={theiaUrl}
                        width="100%"
                        height="100%"
                        style={{ border: "none", background: "#1e1e1e" }}
                        title="Theia IDE"
                        onError={() => {
                          toast({
                            title: "IDE Connection Error",
                            description: "Unable to connect to Theia IDE. Please refresh.",
                            status: "error",
                            duration: 5000,
                            isClosable: true,
                          });
                        }}
                      />
                    ) : (
                      <VStack justify="center" h="100%" bg="gray.900" p={6}>
                        <Text color="white" fontSize="lg" textAlign="center">
                          {user?.isDemoMode ? 
                            "🖥️ Theia IDE Preview (Demo Mode)" : 
                            "🖥️ Theia IDE Loading..."
                          }
                        </Text>
                        <Text color="gray.400" fontSize="sm" textAlign="center">
                          {user?.isDemoMode ? 
                            "Full IDE access available with account registration" :
                            "Your personal development environment will appear here"
                          }
                        </Text>
                      </VStack>
                    )}
                  </Box>
                </VStack>
              </Box>
              
              {/* Right Panel - Robot Camera Feed Placeholder */}
              <Box w="50%">
                <VStack spacing={4} align="start" h="100%">
                  <HStack spacing={4}>
                    <Text fontSize="lg" color="white" fontWeight="bold">
                      Live Robot Camera Feed
                    </Text>
                    <Badge colorScheme="orange" fontSize="xs">
                      COMING SOON
                    </Badge>
                  </HStack>
                  <Box w="full" h="75vh" border="1px solid" borderColor="gray.600" borderRadius="md" overflow="hidden">
                    <VStack justify="center" h="100%" bg="gray.900" p={6} spacing={6}>
                      <Text fontSize="6xl" color="gray.600">
                        🎥
                      </Text>
                      <VStack spacing={2}>
                        <Text color="white" fontSize="lg" textAlign="center" fontWeight="bold">
                          Robot Camera Stream
                        </Text>
                        <Text color="gray.400" fontSize="sm" textAlign="center" maxW="300px">
                          Live camera feed from your selected robot will appear here once the hardware integration is complete.
                        </Text>
                        <Text color="gray.500" fontSize="xs" textAlign="center">
                          Current Selection: {robotNames[robot].emoji} {robotNames[robot].name}
                        </Text>
                      </VStack>
                      <Badge colorScheme="blue" fontSize="xs" px={3} py={1}>
                        Hardware Integration in Progress
                      </Badge>
                    </VStack>
                  </Box>
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
