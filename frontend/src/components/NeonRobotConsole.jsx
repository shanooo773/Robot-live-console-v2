import { useRef, useState, useEffect, useCallback, useMemo } from "react";
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
  Progress,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
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
  ChevronLeftIcon,
  ViewOffIcon,
} from "@chakra-ui/icons";
import TheiaIDE from "./TheiaIDE";
import WebRTCVideoPlayer from "./WebRTCVideoPlayer";
import RobotSelector from "./RobotSelector";
import FileSelector from "./FileSelector";
import {
  checkAccess,
  getVideo,
  getMyActiveBookings,
  getAvailableRobots,
  getContainerLogs,
  getLearningLessons,
  getLearningLesson,
  getLearningProgress,
  upsertLearningProgress,
} from "../api";

const renderInlineMarkdown = (text) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <Text as="span" key={index} fontWeight="700">{part.slice(2, -2)}</Text>;
    }
    return <Text as="span" key={index}>{part}</Text>;
  });
};

const MarkdownLessonContent = ({ content }) => {
  const lines = content.split("\n");
  const nodes = [];
  let inCodeBlock = false;
  let codeLines = [];

  const flushCodeBlock = (keyPrefix) => {
    if (!codeLines.length) {
      return null;
    }
    const block = (
      <Box
        key={`${keyPrefix}-code`}
        bg="rgba(15, 23, 42, 0.8)"
        border="1px solid rgba(255,255,255,0.1)"
        borderRadius="8px"
        p={3}
        overflowX="auto"
      >
        <Text color="gray.200" fontFamily="mono" fontSize="xs" whiteSpace="pre-wrap">
          {codeLines.join("\n")}
        </Text>
      </Box>
    );
    codeLines = [];
    return block;
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    const key = `line-${index}`;

    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        const blockNode = flushCodeBlock(key);
        if (blockNode) nodes.push(blockNode);
      }
      inCodeBlock = !inCodeBlock;
      return;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      return;
    }

    if (!trimmed) {
      nodes.push(<Box key={key} h={2} />);
      return;
    }

    if (trimmed.startsWith("### ")) {
      nodes.push(
        <Text key={key} color="blue.200" fontWeight="700" fontSize="md">
          {trimmed.replace(/^###\s*/, "")}
        </Text>
      );
      return;
    }

    if (trimmed.startsWith("## ")) {
      nodes.push(
        <Text key={key} color="blue.100" fontWeight="700" fontSize="lg">
          {trimmed.replace(/^##\s*/, "")}
        </Text>
      );
      return;
    }

    if (trimmed.startsWith("# ")) {
      nodes.push(
        <Text key={key} color="white" fontWeight="800" fontSize="xl">
          {trimmed.replace(/^#\s*/, "")}
        </Text>
      );
      return;
    }

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      nodes.push(
        <HStack key={key} align="start" spacing={2}>
          <Text color="blue.300">•</Text>
          <Text color="gray.200" fontSize="sm">{renderInlineMarkdown(trimmed.slice(2))}</Text>
        </HStack>
      );
      return;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      nodes.push(
        <Text key={key} color="gray.200" fontSize="sm">
          {renderInlineMarkdown(trimmed)}
        </Text>
      );
      return;
    }

    nodes.push(
      <Text key={key} color="gray.200" fontSize="sm" lineHeight="1.7">
        {renderInlineMarkdown(line)}
      </Text>
    );
  });

  if (inCodeBlock) {
    const blockNode = flushCodeBlock("tail");
    if (blockNode) nodes.push(blockNode);
  }

  return <VStack align="stretch" spacing={1}>{nodes}</VStack>;
};

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

  // Logs state
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logsError, setLogsError] = useState(null);
  const [logsType, setLogsType] = useState("preview");
  const [autoRefresh, setAutoRefresh] = useState(false);
  const logsTypeRef = useRef("preview");
  const logsAutoRefreshRef = useRef(null);
  const logsEndRef = useRef(null);

  // Learning panel state
  const [isLearningPanelOpen, setIsLearningPanelOpen] = useState(true);
  const [lessons, setLessons] = useState([]);
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [selectedLessonContent, setSelectedLessonContent] = useState("");
  const [learningLoading, setLearningLoading] = useState(true);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [learningError, setLearningError] = useState("");
  const [completedLessonIds, setCompletedLessonIds] = useState(new Set());
  const [progressSaving, setProgressSaving] = useState(false);

  const toast = useToast();
  const containerRef = useRef();
  const completedCount = useMemo(
    () => lessons.filter((lesson) => completedLessonIds.has(lesson.id)).length,
    [lessons, completedLessonIds]
  );

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

  const loadLearningPanelData = useCallback(async () => {
    if (!authToken) return;
    setLearningLoading(true);
    setLearningError("");
    try {
      const [lessonResponse, progressResponse] = await Promise.all([
        getLearningLessons(),
        getLearningProgress("ros2-foundation"),
      ]);
      const availableLessons = lessonResponse?.lessons || [];
      setLessons(availableLessons);

      const completed = new Set(progressResponse?.completed_lessons || []);
      setCompletedLessonIds(completed);

      if (availableLessons.length > 0) {
        const firstIncomplete = availableLessons.find((lesson) => !completed.has(lesson.id));
        setSelectedLessonId((currentSelected) => (
          currentSelected && availableLessons.some((lesson) => lesson.id === currentSelected)
            ? currentSelected
            : (firstIncomplete?.id || availableLessons[0].id)
        ));
      }
    } catch (error) {
      console.error("Failed to load learning lessons/progress:", error);
      setLearningError(error?.response?.data?.detail || "Unable to load lessons right now.");
    } finally {
      setLearningLoading(false);
    }
  }, [authToken]);

  const loadLessonContent = useCallback(async (lessonId) => {
    if (!lessonId) return;
    setLessonLoading(true);
    setLearningError("");
    try {
      const lesson = await getLearningLesson(lessonId);
      setSelectedLessonContent(lesson?.content || "");
    } catch (error) {
      console.error("Failed to load lesson content:", error);
      setLearningError(error?.response?.data?.detail || "Unable to load lesson content.");
      setSelectedLessonContent("");
    } finally {
      setLessonLoading(false);
    }
  }, []);

  const toggleLessonCompletion = async () => {
    if (!selectedLessonId) return;
    const currentlyCompleted = completedLessonIds.has(selectedLessonId);
    setProgressSaving(true);
    try {
      const progress = await upsertLearningProgress({
        course_id: "ros2-foundation",
        lesson_id: selectedLessonId,
        completed: !currentlyCompleted,
      });
      setCompletedLessonIds(new Set(progress?.completed_lessons || []));
      toast({
        title: currentlyCompleted ? "Lesson marked incomplete" : "Lesson marked complete",
        status: "success",
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: "Progress update failed",
        description: error?.response?.data?.detail || "Could not save lesson progress.",
        status: "error",
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setProgressSaving(false);
    }
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

  useEffect(() => {
    loadLearningPanelData();
  }, [loadLearningPanelData]);

  useEffect(() => {
    if (selectedLessonId) {
      loadLessonContent(selectedLessonId);
    }
  }, [selectedLessonId, loadLessonContent]);

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

  // ── Container logs ────────────────────────────────────────────────
  const fetchLogs = useCallback(async (typeOverride) => {
    const type = typeOverride || logsTypeRef.current;
    setLogsLoading(true);
    setLogsError(null);
    try {
      const data = await getContainerLogs(authToken, type);
      const raw = data.logs;
      const lines = Array.isArray(raw)
        ? raw
        : typeof raw === "string"
          ? raw.split("\n").filter(Boolean)
          : [];
      setLogs(lines);
    } catch (e) {
      setLogsError(e?.response?.data?.detail || e.message || "Failed to fetch logs");
      setLogs([]);
    } finally {
      setLogsLoading(false);
    }
  }, [authToken]);

  const switchLogsType = (type) => {
    setLogsType(type);
    logsTypeRef.current = type;
    fetchLogs(type);
  };

  // Fetch on modal open; clear on close
  useEffect(() => {
    if (!isLogsOpen) {
      clearInterval(logsAutoRefreshRef.current);
      logsAutoRefreshRef.current = null;
      setAutoRefresh(false);
      setLogs([]);
      return;
    }
    const defaultType = hasActiveBooking ? "booking" : "preview";
    switchLogsType(defaultType);
  }, [isLogsOpen, hasActiveBooking]);

  // Scroll to bottom when new logs arrive
  useEffect(() => {
    if (isLogsOpen && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, isLogsOpen]);

  // Auto-refresh every 5 s when enabled
  useEffect(() => {
    if (!autoRefresh || !isLogsOpen) {
      clearInterval(logsAutoRefreshRef.current);
      logsAutoRefreshRef.current = null;
      return;
    }
    logsAutoRefreshRef.current = setInterval(() => fetchLogs(), 5000);
    return () => clearInterval(logsAutoRefreshRef.current);
  }, [autoRefresh, isLogsOpen, fetchLogs]);

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
          
          const isPreview = !slot?.bookingId || slot?.isPreview;
          await fetch('/theia/start', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(
              isPreview
                ? { mode: "preview" }
                : { mode: "booking", booking_id: slot.bookingId, robot_id: slot.robotId, robot_type: slot.robotType }
            ),
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
      <Box h="100vh" w="100vw" bg="#0F172A" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={6}>
          <Spinner size="xl" color="blue.400" />
          <Text color="blue.300" fontSize="lg" fontWeight="600" fontFamily="'Inter', sans-serif">
            Initializing Development Environment...
          </Text>
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
        bg="#1E293B"
        borderBottom="1px solid rgba(255,255,255,0.1)"
        display="flex"
        alignItems="center"
        px={6}
        boxShadow="0 4px 20px rgba(0,0,0,0.25)"
      >
        <HStack spacing={4} flex="1">
          {/* Left side - User info */}
          <HStack spacing={3}>
            <Avatar size="sm" name={user.name} bg="blue.500" />
            <VStack align="start" spacing={0}>
              <Text color="white" fontSize="sm" fontWeight="600" fontFamily="'Inter', sans-serif">
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
            <Tooltip label={isLearningPanelOpen ? "Collapse Learning Panel" : "Expand Learning Panel"} placement="bottom">
              <IconButton
                icon={isLearningPanelOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
                size="sm"
                variant="ghost"
                color="gray.300"
                onClick={() => setIsLearningPanelOpen((open) => !open)}
                _hover={{ bg: "rgba(255,255,255,0.1)", color: "white" }}
              />
            </Tooltip>

            <Tooltip label="Expand IDE" placement="bottom">
              <IconButton
                icon={<ChevronRightIcon />}
                size="sm"
                variant="ghost"
                color="gray.300"
                onClick={expandIDE}
                isActive={panelLayout === "ide-expanded"}
                _active={{ bg: "rgba(37,99,235,0.25)", color: "blue.300" }}
                _hover={{ bg: "rgba(255,255,255,0.1)", color: "white" }}
              />
            </Tooltip>

            <Tooltip label="Expand Video" placement="bottom">
              <IconButton
                icon={<ViewIcon />}
                size="sm"
                variant="ghost"
                color="gray.300"
                onClick={expandVideo}
                isActive={panelLayout === "video-expanded"}
                _active={{ bg: "rgba(37,99,235,0.25)", color: "blue.300" }}
                _hover={{ bg: "rgba(255,255,255,0.1)", color: "white" }}
              />
            </Tooltip>

            <Tooltip label="Reset Split View" placement="bottom">
              <IconButton
                icon={<ViewOffIcon />}
                size="sm"
                variant="ghost"
                color="gray.300"
                onClick={resetSplit}
                isActive={panelLayout === "split"}
                _active={{ bg: "rgba(37,99,235,0.25)", color: "blue.300" }}
                _hover={{ bg: "rgba(255,255,255,0.1)", color: "white" }}
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
        mt="60px"
        h="calc(100vh - 60px)"
        display="flex"
        position="relative"
      >
        {/* Learning Panel */}
        <Box
          w={isLearningPanelOpen ? "360px" : "56px"}
          h="100%"
          borderRight="1px solid rgba(255,255,255,0.08)"
          bg="#111827"
          transition="width 0.2s ease"
          overflow="hidden"
        >
          {isLearningPanelOpen ? (
            <VStack h="100%" align="stretch" spacing={0}>
              <Box p={4} borderBottom="1px solid rgba(255,255,255,0.08)">
                <Text color="white" fontWeight="700" fontSize="lg">ROS2 Foundation</Text>
                <Text color="gray.400" fontSize="xs" mt={1}>
                  Progress: {learningLoading ? "Loading..." : `${completedCount}/${lessons.length}`}
                </Text>
                <Progress
                  mt={2}
                  value={lessons.length ? (completedCount / lessons.length) * 100 : 0}
                  size="sm"
                  colorScheme="green"
                  borderRadius="full"
                />
              </Box>

              <Box p={3} borderBottom="1px solid rgba(255,255,255,0.08)" maxH="220px" overflowY="auto">
                {learningLoading ? (
                  <HStack color="gray.300">
                    <Spinner size="sm" />
                    <Text fontSize="sm">Loading lessons...</Text>
                  </HStack>
                ) : (
                  <VStack spacing={2} align="stretch">
                    {lessons.map((lesson) => {
                      const isSelected = lesson.id === selectedLessonId;
                      const isCompleted = completedLessonIds.has(lesson.id);
                      return (
                        <Button
                          key={lesson.id}
                          justifyContent="space-between"
                          variant={isSelected ? "solid" : "ghost"}
                          colorScheme={isSelected ? "blue" : "gray"}
                          color={isSelected ? "white" : "gray.200"}
                          size="sm"
                          onClick={() => setSelectedLessonId(lesson.id)}
                        >
                          <Text fontSize="xs" noOfLines={1} textAlign="left">
                            {lesson.title}
                          </Text>
                          <Text fontSize="xs">{isCompleted ? "✅" : "⬜"}</Text>
                        </Button>
                      );
                    })}
                  </VStack>
                )}
              </Box>

              <Box flex="1" overflowY="auto" p={4}>
                {lessonLoading ? (
                  <HStack color="gray.300" mt={2}>
                    <Spinner size="sm" />
                    <Text fontSize="sm">Loading lesson content...</Text>
                  </HStack>
                ) : learningError ? (
                  <Alert status="error" borderRadius="md" fontSize="sm">
                    <AlertIcon />
                    {learningError}
                  </Alert>
                ) : selectedLessonContent ? (
                  <MarkdownLessonContent content={selectedLessonContent} />
                ) : (
                  <Text color="gray.400" fontSize="sm">
                    Select a lesson to get started.
                  </Text>
                )}
              </Box>

              <Box p={4} borderTop="1px solid rgba(255,255,255,0.08)">
                <Button
                  w="full"
                  colorScheme={selectedLessonId && completedLessonIds.has(selectedLessonId) ? "yellow" : "green"}
                  onClick={toggleLessonCompletion}
                  isLoading={progressSaving}
                  isDisabled={!selectedLessonId}
                >
                  {selectedLessonId && completedLessonIds.has(selectedLessonId)
                    ? "Mark Lesson Incomplete"
                    : "Mark Lesson Complete"}
                </Button>
              </Box>
            </VStack>
          ) : (
            <VStack h="100%" justify="center">
              <Tooltip label="Open Learning Panel" placement="right">
                <IconButton
                  aria-label="Open learning panel"
                  icon={<ChevronRightIcon />}
                  variant="ghost"
                  color="gray.300"
                  onClick={() => setIsLearningPanelOpen(true)}
                  _hover={{ bg: "rgba(255,255,255,0.08)", color: "white" }}
                />
              </Tooltip>
            </VStack>
          )}
        </Box>

        <Box
          ref={containerRef}
          h="100%"
          flex="1"
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
              slot={slot}
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
            bg="rgba(255,255,255,0.12)"
            cursor="col-resize"
            zIndex="10"
            _hover={{
              bg: "rgba(37,99,235,0.5)",
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
              bg="rgba(255,255,255,0.1)"
              borderRadius="4px"
              display="flex"
              alignItems="center"
              justifyContent="center"
              fontSize="xs"
              color="gray.400"
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
                    bg="gray.900"
                  >
                    <Text fontSize="4xl">📹</Text>
                    <VStack spacing={3} textAlign="center">
                      <Badge colorScheme="orange" fontSize="md" p={2}>
                        Preview Mode
                      </Badge>
                      <Text color="blue.300" fontSize="lg" fontWeight="bold">
                        Live Robot Feed
                      </Text>
                      <Text color="gray.400" maxW="300px">
                        👉 To access the real-time robot feed, please book the service.
                      </Text>
                    </VStack>
                    <Button
                      colorScheme="orange"
                      onClick={onBack}
                      size="md"
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
      </Box>

      {/* Container Logs Modal */}
      <Modal isOpen={isLogsOpen} onClose={onLogsClose} size="4xl">
        <ModalOverlay backdropFilter="blur(4px)" bg="rgba(0,0,0,0.6)" />
        <ModalContent bg="#1E293B" border="1px solid rgba(255,255,255,0.1)" boxShadow="0 20px 60px rgba(0,0,0,0.5)">
          <ModalHeader pb={3} borderBottom="1px solid rgba(255,255,255,0.08)">
            <HStack justify="space-between" align="center" pr={8}>
              <HStack spacing={3}>
                <Text color="white" fontFamily="'Inter', sans-serif" fontWeight="700" fontSize="md">
                  Container Logs
                </Text>
                <Badge colorScheme={autoRefresh ? "green" : "gray"} fontSize="xs">
                  {autoRefresh ? "● Live" : "Paused"}
                </Badge>
              </HStack>
              {/* Tab buttons */}
              <HStack spacing={1}>
                <Button
                  size="xs"
                  variant={logsType === "preview" ? "solid" : "ghost"}
                  colorScheme={logsType === "preview" ? "blue" : "gray"}
                  onClick={() => switchLogsType("preview")}
                  color={logsType === "preview" ? "white" : "gray.400"}
                >
                  Preview IDE
                </Button>
                {hasActiveBooking && (
                  <Button
                    size="xs"
                    variant={logsType === "booking" ? "solid" : "ghost"}
                    colorScheme={logsType === "booking" ? "green" : "gray"}
                    onClick={() => switchLogsType("booking")}
                    color={logsType === "booking" ? "white" : "gray.400"}
                  >
                    Booking IDE
                  </Button>
                )}
              </HStack>
            </HStack>
          </ModalHeader>
          <ModalCloseButton color="gray.400" />

          <ModalBody p={0}>
            {/* Terminal box */}
            <Box
              bg="#0F172A"
              fontFamily="'Courier New', Courier, monospace"
              fontSize="12px"
              h="55vh"
              overflowY="auto"
              p={4}
              position="relative"
            >
              {logsLoading && logs.length === 0 ? (
                <HStack justify="center" mt={8}>
                  <Spinner size="sm" color="blue.400" />
                  <Text color="gray.400">Fetching logs...</Text>
                </HStack>
              ) : logsError ? (
                <Text color="#FF6B6B">Error: {logsError}</Text>
              ) : logs.length === 0 ? (
                <Text color="gray.500">No log output yet. Container may still be starting.</Text>
              ) : (
                <>
                  {logs.map((line, i) => {
                    const lower = line.toLowerCase();
                    let color = "#CBD5E0";
                    if (lower.includes("error") || lower.includes("fatal") || lower.includes("exception"))
                      color = "#FF6B6B";
                    else if (lower.includes("warn"))
                      color = "#FFD93D";
                    else if (lower.includes("info") || lower.includes("✅") || lower.includes("started") || lower.includes("ready"))
                      color = "#6BCB77";
                    else if (lower.includes("debug"))
                      color = "#74B9FF";
                    return (
                      <Text key={i} color={color} whiteSpace="pre-wrap" wordBreak="break-all" lineHeight="1.6">
                        {line}
                      </Text>
                    );
                  })}
                  <Box ref={logsEndRef} />
                </>
              )}
            </Box>
          </ModalBody>

          <ModalFooter borderTop="1px solid rgba(255,255,255,0.08)" py={3} gap={2}>
            <Text color="gray.500" fontSize="xs" flex="1">
              {logs.length} line{logs.length !== 1 ? "s" : ""} · {user.name} · {logsType} container
            </Text>
            <Button
              size="sm"
              variant="ghost"
              color="gray.400"
              _hover={{ color: "white" }}
              onClick={() => setAutoRefresh(r => !r)}
            >
              {autoRefresh ? "⏸ Pause" : "▶ Auto-refresh"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              color="gray.400"
              _hover={{ color: "white" }}
              isLoading={logsLoading}
              onClick={() => fetchLogs()}
            >
              ↻ Refresh
            </Button>
            <Button
              size="sm"
              variant="ghost"
              color="gray.400"
              _hover={{ color: "white" }}
              onClick={() => navigator.clipboard.writeText(logs.join("\n"))}
              isDisabled={logs.length === 0}
            >
              ⎘ Copy All
            </Button>
            <Button size="sm" variant="ghost" color="gray.400" _hover={{ color: "white" }} onClick={onLogsClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default NeonRobotConsole;
