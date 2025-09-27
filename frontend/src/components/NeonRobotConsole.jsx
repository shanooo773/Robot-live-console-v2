import { useState, useEffect } from "react";
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
} from "@chakra-ui/react";
import { 
  InfoIcon,
  ChevronRightIcon,
} from "@chakra-ui/icons";
import TheiaIDE from "./TheiaIDE";
import WebRTCVideoPlayer from "./WebRTCVideoPlayer";
import RobotSelector from "./RobotSelector";
import { getMyActiveBookings, getAvailableRobots, executeRobotCode } from "../api";
import PropTypes from 'prop-types';

const NeonRobotConsole = ({ user, slot, authToken, onBack, onLogout }) => {
  // Simplified state - remove complex layout state
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [codeRunning, setCodeRunning] = useState(false);
  const [activeBookings, setActiveBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotNames, setRobotNames] = useState({});
  const [webrtcAccessDenied, setWebrtcAccessDenied] = useState(false);
  const [logs, setLogs] = useState([]);
  
  // Modal state for logs
  const { isOpen: isLogsOpen, onOpen: onLogsOpen, onClose: onLogsClose } = useDisclosure();
  
  const toast = useToast();

  // Utility functions
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const onSelect = (robotType) => {
    setRobot(robotType);
    addLog(`Switched to robot: ${robotNames[robotType]?.name || robotType}`);
  };

  // Main action handlers
  const handleRunCode = async () => {
    setCodeRunning(true);
    addLog("Initializing code execution...");
    
    try {
      // Auto-start Theia container if not running
      addLog("Ensuring Theia container is running...");
      
      // Get code from Theia IDE (this would need integration with TheiaIDE component)
      // For now, we'll show a placeholder
      const result = await executeRobotCode(
        "# Your code from Theia IDE will be executed here\nprint('Hello from robot!')", 
        robot
      );
      
      addLog(`Code execution completed: ${result.message || 'Success'}`, 'success');
      toast({
        title: "Code Executed",
        description: `Successfully pushed code to ${robotNames[robot]?.name || robot}`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error("Code execution failed:", error);
      addLog(`Code execution failed: ${error.message}`, 'error');
      toast({
        title: "Code Execution Failed",
        description: error.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setCodeRunning(false);
    }
  };

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
        // Demo users get full access (IDE + WebRTC)
        if (user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode || 
            localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin') || 
            localStorage.getItem('isDummy') || localStorage.getItem('isDemoMode')) {
            
          setHasAccess(true);
          setAvailableRobots(['turtlebot', 'robot_arm', 'robot_hand']);
          addLog("Demo user session initialized - full access granted");
        } else if (authToken) {
          // Regular users: Always get IDE access (24/7), WebRTC controlled by booking
          setHasAccess(true); // Always grant IDE access
          
          try {
            const bookings = await getMyActiveBookings(authToken);
            setActiveBookings(bookings);
            
            const robotTypes = [...new Set(bookings.map(booking => booking.robot_type))];
            setAvailableRobots(robotTypes.length > 0 ? robotTypes : ['turtlebot']); // Default robot for IDE access
            
            if (robotTypes.length > 0 && !robotTypes.includes(robot)) {
              setRobot(robotTypes[0]);
            }
            
            addLog(`IDE access granted. Active bookings: ${robotTypes.length > 0 ? robotTypes.join(', ') : 'None'}`);
          } catch (error) {
            console.error("Failed to fetch active bookings:", error);
            // Still grant IDE access even if booking fetch fails
            setAvailableRobots(['turtlebot']); // Default for IDE access
            addLog("IDE access granted (booking check failed, but IDE available 24/7)");
          }
        } else {
          setHasAccess(false);
          addLog("Authentication required for access");
        }
      } catch (error) {
        console.error("Access check failed:", error);
        addLog(`Access check failed: ${error.message}`);
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
              <Text fontWeight="bold" color="white">Authentication Required</Text>
              <Text color="gray.300">Please log in to access the Eclipse Theia IDE console.</Text>
            </Box>
          </Alert>
          <Button variant="neonPrimary" onClick={onBack}>
            Go Back to Login
          </Button>
        </VStack>
      </Box>
    );
  }



  return (
    <Box h="100vh" w="100vw" overflow="hidden" position="relative" bg="gray.900">
      {/* Simplified Top Bar */}
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        zIndex="1000"
        h="60px"
        bg="rgba(26, 32, 44, 0.9)"
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
              <Text color="white" fontSize="sm" fontWeight="600">
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
            </HStack>
          </HStack>
          
          <Box flex="1" />
          
          {/* Center - Main Actions (Only 2 buttons as per requirements) */}
          <HStack spacing={4}>
                <Button
                  colorScheme="green"
                  size="md"
                  onClick={handleRunCode}
                  isLoading={codeRunning}
                  loadingText="Running Code..."
                  leftIcon={<ChevronRightIcon />}
                >
                  Run Code
                </Button>
                
                <Button
                  colorScheme="blue"
                  variant="outline"
                  size="md"
                  onClick={onLogsOpen}
                  leftIcon={<InfoIcon />}
                >
                  View Logs
                </Button>
          </HStack>
          
          <Box flex="1" />
          
          {/* Right side - Navigation */}
          <HStack spacing={3}>
            <RobotSelector robot={robot} onSelect={onSelect} availableRobots={availableRobots} />
            
            <Button size="sm" variant="ghost" onClick={onBack}>
              Back
            </Button>
            
            <Button size="sm" variant="ghost" onClick={onLogout}>
              Logout
            </Button>
          </HStack>
        </HStack>
      </Box>

      {/* Main Content Area - Simplified Layout */}
      <Box
        mt="60px"
        h="calc(100vh - 60px)"
        display="flex"
        position="relative"
      >
        {/* Left Panel - Eclipse Theia IDE (50% width) */}
        <Box
          w="50%"
          h="100%"
          borderRight="1px solid rgba(0,255,200,0.3)"
          position="relative"
          overflow="hidden"
        >
          <TheiaIDE 
            user={user} 
            authToken={authToken}
            onError={(error) => {
              addLog(`IDE Error: ${error.message}`, 'error');
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

        {/* Right Panel - WebRTC Video Feed (50% width) */}
        <Box
          w="50%"
          h="100%"
          position="relative"
          overflow="hidden"
          bg="rgba(0,0,0,0.5)"
        >
          <VStack h="100%" spacing={4} p={4}>
            <Text color="white" fontSize="lg" fontWeight="bold">
              Robot Video Feed
            </Text>
            
            <Box 
              flex="1" 
              w="100%" 
              border="1px solid rgba(0,255,200,0.3)"
              borderRadius="8px" 
              overflow="hidden"
              bg="rgba(0,0,0,0.8)"
              position="relative"
            >
              {webrtcAccessDenied ? (
                <VStack spacing={4} justify="center" h="100%" p={6} textAlign="center">
                  <Text color="orange.300" fontSize="lg" fontWeight="bold">
                    🔒 Robot Feed Access Restricted
                  </Text>
                  <Text color="gray.300" fontSize="md">
                    To access the robot feed, please book a session.
                  </Text>
                  <Button 
                    colorScheme="blue" 
                    variant="outline" 
                    onClick={onBack}
                    size="sm"
                  >
                    Book a Session
                  </Button>
                </VStack>
              ) : (
                <WebRTCVideoPlayer 
                  user={user}
                  authToken={authToken}
                  robotType={robot}
                  onError={(error) => {
                    addLog(`WebRTC Error: ${error.message}`, 'error');
                    // Check if it's an access control error
                    if (error.message.includes('booking') || error.message.includes('session')) {
                      setWebrtcAccessDenied(true);
                      addLog("WebRTC access denied - booking required for robot feed");
                    } else {
                      toast({
                        title: "Video Stream Error",
                        description: error.message,
                        status: "error",
                        duration: 5000,
                        isClosable: true,
                      });
                    }
                  }}
                />
              )}
            </Box>
          </VStack>
        </Box>
      </Box>

      {/* Enhanced Logs Modal */}
      <Modal isOpen={isLogsOpen} onClose={onLogsClose} size="xl">
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent bg="rgba(26, 32, 44, 0.95)" backdropFilter="blur(12px)" border="1px solid rgba(0,255,200,0.3)">
          <ModalHeader color="white" fontFamily="'Orbitron', sans-serif">
            System Logs & Status
          </ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody pb={6} color="gray.300">
            <VStack spacing={4} align="start">
              <Box w="100%">
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Current Session Status:</Text>
                <Text>Robot: {robotNames[robot]?.name || robot}</Text>
                <Text>IDE: Eclipse Theia Ready (24/7 Access)</Text>
                <Text>WebRTC: {webrtcAccessDenied ? "Access Restricted (Booking Required)" : "Available"}</Text>
                <Text>Active Bookings: {activeBookings.length > 0 ? activeBookings.map(b => b.robot_type).join(', ') : 'None'}</Text>
              </Box>
              
              <Box w="100%">
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Activity Log:</Text>
                <Box 
                  maxH="300px" 
                  overflowY="auto" 
                  bg="rgba(0,0,0,0.3)" 
                  p={3} 
                  borderRadius="md"
                  border="1px solid rgba(0,255,200,0.2)"
                >
                  {logs.length === 0 ? (
                    <Text color="gray.500" fontSize="sm">No activity yet...</Text>
                  ) : (
                    logs.map((log, index) => (
                      <HStack key={index} spacing={2} mb={1}>
                        <Text color="gray.500" fontSize="xs" minW="20">{log.timestamp}</Text>
                        <Text 
                          fontSize="sm" 
                          color={
                            log.type === 'error' ? 'red.300' : 
                            log.type === 'success' ? 'green.300' : 
                            'gray.300'
                          }
                        >
                          {log.message}
                        </Text>
                      </HStack>
                    ))
                  )}
                </Box>
              </Box>
              
              <Box w="100%">
                <Text fontWeight="bold" color="neon.cyan" mb={2}>Instructions:</Text>
                <VStack spacing={2} align="start" fontSize="sm">
                  <Text>• Use the Eclipse Theia IDE (left panel) to write and edit robot code - available 24/7</Text>
                  <Text>• Click &quot;Run Code&quot; to push your code to the selected robot endpoint</Text>
                  <Text>• Robot video feed (right panel) requires an active booking session</Text>
                  <Text>• Demo users get full access during demo sessions</Text>
                  <Text>• All activities are logged and can be viewed in this modal</Text>
                </VStack>
              </Box>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

NeonRobotConsole.propTypes = {
  user: PropTypes.shape({
    name: PropTypes.string,
    isDemoUser: PropTypes.bool,
    isDemoAdmin: PropTypes.bool,
    isDemoMode: PropTypes.bool,
  }).isRequired,
  slot: PropTypes.shape({
    robotType: PropTypes.string,
  }),
  authToken: PropTypes.string,
  onBack: PropTypes.func.isRequired,
  onLogout: PropTypes.func.isRequired,
};

export default NeonRobotConsole;