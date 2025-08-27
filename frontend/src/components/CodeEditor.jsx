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
import { Editor } from "@monaco-editor/react";
import RobotSelector from "./RobotSelector";
import LanguageSelector from "./LanguageSelector";
import { ROBOT_CODE_SNIPPETS } from "../constants";
import { checkAccess, getVideo } from "../api";

const robotNames = {
  turtlebot: { name: "TurtleBot3", emoji: "🤖" },
  arm: { name: "Robot Arm", emoji: "🦾" },
  hand: { name: "Robot Hand", emoji: "🤲" },
};

const VPS_URL = import.meta.env.VITE_VPS_URL || "http://172.104.207.139";

const CodeEditor = ({ user, slot, authToken, onBack, onLogout }) => {
  const editorRef = useRef();
  const [robot, setRobot] = useState(slot?.robotType || "turtlebot");
  const [language, setLanguage] = useState("python");
  const [value, setValue] = useState(ROBOT_CODE_SNIPPETS["python"][slot?.robotType || "turtlebot"]);
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
        
        if (isDemoUser || isDemoAdmin || isDummy || user?.isDemoUser || user?.isDemoAdmin) {
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

  const onMount = (editor) => {
    editorRef.current = editor;
    editor.focus();
  };

  const onSelect = (robotType) => {
    setRobot(robotType);
    setValue(ROBOT_CODE_SNIPPETS[language][robotType]);
    setShowVideo(false); // Reset video when robot changes
    setVideoUrl(null);
  };

  const onLanguageSelect = (languageType) => {
    setLanguage(languageType);
    setValue(ROBOT_CODE_SNIPPETS[languageType][robot]);
  };

  const handleGetRealResult = async () => {
    setVideoLoading(true);
    try {
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

        {/* Main Editor and VPS Panel */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Text fontSize="xl" fontWeight="bold" color="white">
                Development Console - Robot Control Interface
              </Text>
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
              {/* Left Panel - Monaco Editor */}
              <Box w="50%">
                <VStack spacing={4} align="start">
                  <HStack spacing={4}>
                    <RobotSelector robot={robot} onSelect={onSelect} />
                    <LanguageSelector language={language} onSelect={onLanguageSelect} />
                  </HStack>
                  <Box w="full">
                    <Editor
                      options={{
                        minimap: {
                          enabled: false,
                        },
                        fontSize: 14,
                        lineNumbers: "on",
                        automaticLayout: true,
                        scrollBeyondLastLine: false,
                      }}
                      height="75vh"
                      theme="vs-dark"
                      language={language === "cpp" ? "cpp" : "python"}
                      defaultValue={ROBOT_CODE_SNIPPETS[language][robot]}
                      onMount={onMount}
                      value={value}
                      onChange={(value) => setValue(value)}
                    />
                  </Box>
                </VStack>
              </Box>
              
              {/* Right Panel - VPS iframe or Video */}
              <Box w="50%">
                <VStack spacing={4} align="start" h="100%">
                  <Text fontSize="lg" color="white" fontWeight="bold">
                    {showVideo ? `${robotNames[robot].name} Simulation Result` : "Live VPS Control"}
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
                      <iframe
                        src={VPS_URL}
                        width="100%"
                        height="100%"
                        style={{ border: "none", background: "#000" }}
                        title="VPS Control Interface"
                        onError={() => {
                          toast({
                            title: "VPS Connection Error",
                            description: "Unable to connect to VPS. Please check your connection.",
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
                      Back to VPS View
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
