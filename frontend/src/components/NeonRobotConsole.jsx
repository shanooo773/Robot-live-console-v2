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
  ChevronRightIcon,
  ChevronLeftIcon,
} from "@chakra-ui/icons";
import TheiaIDE from "./TheiaIDE";
import WebRTCVideoPlayer from "./WebRTCVideoPlayer";
import FileSelector from "./FileSelector";
import {
  getVideo,
  getMyActiveBookings,
  getAvailableRobots,
  getContainerLogs,
  getLearningLessons,
  getLearningLesson,
  getLearningProgress,
  upsertLearningProgress,
} from "../api";

const parseInlineBoldMarkdown = (text) => {
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
    if (!codeLines.length) return null;
    const block = (
      <Box
        key={`${keyPrefix}-code`}
        bg="#0a0a0a"
        border="1px solid #2a2a2a"
        borderRadius="6px"
        p={3}
        overflowX="auto"
        my={1}
      >
        <Text color="#a0a0a0" fontFamily="'Courier New', monospace" fontSize="xs" whiteSpace="pre-wrap">
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
        <Text key={key} color="#93c5fd" fontWeight="700" fontSize="sm" mt={2}>
          {trimmed.replace(/^###\s*/, "")}
        </Text>
      );
      return;
    }

    if (trimmed.startsWith("## ")) {
      nodes.push(
        <Text key={key} color="#bfdbfe" fontWeight="700" fontSize="md" mt={3}>
          {trimmed.replace(/^##\s*/, "")}
        </Text>
      );
      return;
    }

    if (trimmed.startsWith("# ")) {
      nodes.push(
        <Text key={key} color="#e0e0e0" fontWeight="800" fontSize="lg" mt={3}>
          {trimmed.replace(/^#\s*/, "")}
        </Text>
      );
      return;
    }

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      nodes.push(
        <HStack key={key} align="start" spacing={2}>
          <Text color="#3b82f6" mt="3px" flexShrink={0}>•</Text>
          <Text color="#c0c0c0" fontSize="sm" lineHeight="1.7">{parseInlineBoldMarkdown(trimmed.slice(2))}</Text>
        </HStack>
      );
      return;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      nodes.push(
        <Text key={key} color="#c0c0c0" fontSize="sm" lineHeight="1.7">
          {parseInlineBoldMarkdown(trimmed)}
        </Text>
      );
      return;
    }

    nodes.push(
      <Text key={key} color="#c0c0c0" fontSize="sm" lineHeight="1.7">
        {parseInlineBoldMarkdown(line)}
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
  const [panelLayout, setPanelLayout] = useState("ide-expanded"); // "split", "ide-expanded", "video-expanded"
  const [dividerPosition, setDividerPosition] = useState(50);
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
  const [userMode, setUserMode] = useState("preview");
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
  const [leftPanelTab, setLeftPanelTab] = useState("lesson");
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

  const loadRobotNames = async () => {
    try {
      const robotData = await getAvailableRobots();
      const robotDetails = robotData.details || {};
      const formattedRobots = {};
      Object.keys(robotDetails).forEach(robotType => {
        const r = robotDetails[robotType];
        let emoji = "🤖";
        if (robotType.includes("arm")) emoji = "🦾";
        else if (robotType.includes("hand")) emoji = "🤲";
        formattedRobots[robotType] = {
          name: r.display_name || robotType,
          emoji,
          description: r.description || `${robotType} robot`,
        };
      });
      setRobotNames(formattedRobots);
    } catch (error) {
      setRobotNames({
        turtlebot: { name: "TurtleBot3", emoji: "🤖", description: "Mobile navigation robot" },
        robot_arm: { name: "Robot Arm", emoji: "🦾", description: "6-DOF manipulation arm" },
        robot_hand: { name: "Robot Hand", emoji: "🤲", description: "Dexterous robotic hand" },
      });
    }
  };

  const checkTheiaStatusAndMode = async () => {
    try {
      const response = await fetch('/theia/status', {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        const status = await response.json();
        setTheiaStatus(status);
        setUserMode(status.user_mode || "preview");
        setHasActiveBooking(status.has_active_booking || false);
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
        await checkTheiaStatusAndMode();
        if (user?.isDemoUser || user?.isDemoAdmin || user?.isDemoMode ||
            localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin') ||
            localStorage.getItem('isDummy') || localStorage.getItem('isDemoMode')) {
          setHasAccess(true);
          setAvailableRobots(['turtlebot', 'robot_arm', 'robot_hand']);
        } else if (authToken) {
          setHasAccess(true);
          try {
            const bookings = await getMyActiveBookings(authToken);
            setActiveBookings(bookings);
            const robotTypes = [...new Set(bookings.map(b => b.robot_type))];
            setAvailableRobots(robotTypes.length > 0 ? robotTypes : ['turtlebot']);
            if (robotTypes.length > 0 && !robotTypes.includes(robot)) setRobot(robotTypes[0]);
            if (userMode === "preview") {
              toast({ title: "Preview Mode Active", description: "IDE ready for code editing. Book a session for robot execution and live video.", status: "info", duration: 4000, isClosable: true });
            } else {
              toast({ title: "Booking Mode Active", description: "Full robot access enabled.", status: "success", duration: 3000, isClosable: true });
            }
          } catch {
            setAvailableRobots(['turtlebot']);
            toast({ title: "IDE Ready", description: "Development environment loaded.", status: "info", duration: 3000, isClosable: true });
          }
        } else {
          setHasAccess(false);
        }
      } catch (error) {
        console.error("Access check failed:", error);
        toast({ title: "IDE Access Error", description: "Unable to fully initialize. Please refresh.", status: "error", duration: 5000, isClosable: true });
      } finally {
        setLoading(false);
      }
    };
    checkUserAccessAndMode();
  }, [authToken, user, toast, robot]);

  useEffect(() => { loadLearningPanelData(); }, [loadLearningPanelData]);
  useEffect(() => { if (selectedLessonId) loadLessonContent(selectedLessonId); }, [selectedLessonId, loadLessonContent]);
  useEffect(() => { if (theiaStatus?.status === "running" && authToken) loadWorkspaceFiles(); }, [theiaStatus?.status, authToken]);

  const expandIDE = () => setPanelLayout("ide-expanded");
  const expandVideo = () => setPanelLayout("video-expanded");
  const resetSplit = () => { setPanelLayout("split"); setDividerPosition(50); };

  const handleMouseDown = (e) => { setIsDragging(true); document.body.style.userSelect = 'none'; };
  const handleMouseMove = (e) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
    setDividerPosition(Math.min(Math.max(newPosition, 20), 80));
  };
  const handleMouseUp = () => { setIsDragging(false); document.body.style.userSelect = ''; };

  const fetchLogs = useCallback(async (typeOverride) => {
    const type = typeOverride || logsTypeRef.current;
    setLogsLoading(true);
    setLogsError(null);
    try {
      const data = await getContainerLogs(authToken, type);
      const raw = data.logs;
      const lines = Array.isArray(raw) ? raw : typeof raw === "string" ? raw.split("\n").filter(Boolean) : [];
      setLogs(lines);
    } catch (e) {
      setLogsError(e?.response?.data?.detail || e.message || "Failed to fetch logs");
      setLogs([]);
    } finally {
      setLogsLoading(false);
    }
  }, [authToken]);

  const switchLogsType = (type) => { setLogsType(type); logsTypeRef.current = type; fetchLogs(type); };

  useEffect(() => {
    if (!isLogsOpen) {
      clearInterval(logsAutoRefreshRef.current);
      logsAutoRefreshRef.current = null;
      setAutoRefresh(false);
      setLogs([]);
      return;
    }
    switchLogsType(hasActiveBooking ? "booking" : "preview");
  }, [isLogsOpen, hasActiveBooking]);

  useEffect(() => {
    if (isLogsOpen && logsEndRef.current) logsEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [logs, isLogsOpen]);

  useEffect(() => {
    if (!autoRefresh || !isLogsOpen) { clearInterval(logsAutoRefreshRef.current); logsAutoRefreshRef.current = null; return; }
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

  const loadWorkspaceFiles = async () => {
    setFilesLoading(true);
    try {
      const response = await fetch('/theia/workspace/files', {
        headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        const data = await response.json();
        setWorkspaceFiles(data.files || []);
        if (!selectedFile && data.files && data.files.length > 0) setSelectedFile(data.files[0]);
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
        toast({ title: "Video Loaded", description: `${robotNames[robot]?.name} simulation video is now playing.`, status: "success", duration: 3000, isClosable: true });
      } else if (user?.isDemoMode || user?.isDemoUser || user?.isDemoAdmin ||
                 localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin') ||
                 localStorage.getItem('isDummy') || localStorage.getItem('isDemoMode')) {
        toast({ title: "Demo Mode", description: `In demo mode, simulation video would display here.`, status: "info", duration: 5000, isClosable: true });
      }
    } catch (error) {
      toast({ title: "Video Load Failed", description: error.response?.data?.detail || "Unable to load simulation video.", status: "error", duration: 5000, isClosable: true });
    } finally {
      setVideoLoading(false);
    }
  };

  const handleRunCode = async () => {
    if (!selectedFile) {
      toast({ title: "No File Selected", description: "Please select a .py or .cpp file to run.", status: "warning", duration: 3000, isClosable: true });
      return;
    }
    if (userMode === "preview" && !hasActiveBooking) {
      toast({ title: "Booking Required", description: "Code execution on robot requires booking.", status: "warning", duration: 5000, isClosable: true });
      return;
    }
    setCodeLoading(true);
    try {
      const theiaResponse = await fetch('/theia/status', {
        headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
      });
      if (theiaResponse.ok) {
        const theiaStatusData = await theiaResponse.json();
        setTheiaStatus(theiaStatusData);
        setUserMode(theiaStatusData.user_mode || "preview");
        setHasActiveBooking(theiaStatusData.has_active_booking || false);
        if (theiaStatusData.status !== "running") {
          toast({ title: "Starting IDE", description: "Auto-starting development environment...", status: "info", duration: 3000, isClosable: true });
          const isPreview = !slot?.bookingId || slot?.isPreview;
          await fetch('/theia/start', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(isPreview ? { mode: "preview" } : { mode: "booking", booking_id: slot.bookingId, robot_id: slot.robotId, robot_type: slot.robotType }),
          });
        }
      }
      const encodedPath = selectedFile.path.split('/').map(encodeURIComponent).join('/');
      const fileResponse = await fetch(`/theia/workspace/file/${encodedPath}`, {
        headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' }
      });
      if (!fileResponse.ok) throw new Error('Failed to read file from workspace');
      const fileData = await fileResponse.json();
      const response = await fetch('/robot/execute', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ robot_type: robot, code: fileData.content, language: selectedFile.language, filename: selectedFile.name })
      });
      if (response.ok) {
        toast({ title: "Code Executed", description: `${selectedFile.name} sent to ${robotNames[robot]?.name || robot}.`, status: "success", duration: 3000, isClosable: true });
      } else {
        throw new Error('Failed to execute code');
      }
    } catch (error) {
      const errorMessage = error.message || "Unable to execute code";
      toast({
        title: errorMessage.includes("booking") ? "Booking Required" : "Code Execution Failed",
        description: errorMessage,
        status: errorMessage.includes("booking") ? "warning" : "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setCodeLoading(false);
    }
  };

  // Lesson navigation
  const currentLessonIndex = lessons.findIndex((l) => l.id === selectedLessonId);
  const currentLesson = lessons[currentLessonIndex] || null;
  const goToPrevLesson = () => { if (currentLessonIndex > 0) setSelectedLessonId(lessons[currentLessonIndex - 1].id); };
  const goToNextLesson = () => { if (currentLessonIndex < lessons.length - 1) setSelectedLessonId(lessons[currentLessonIndex + 1].id); };
  const handleSelectLesson = (id) => { setSelectedLessonId(id); setLeftPanelTab("lesson"); };

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

  if (loading) {
    return (
      <Box h="100vh" w="100vw" display="flex" alignItems="center" justifyContent="center" bg="#0f0f0f">
        <VStack spacing={4}>
          <Spinner size="xl" color="#3b82f6" thickness="3px" />
          <Text color="#888" fontSize="sm" fontFamily="'Inter', sans-serif">
            Initializing Development Environment...
          </Text>
        </VStack>
      </Box>
    );
  }

  const isDemoUser = user?.isDemoUser || user?.isDemoAdmin ||
    localStorage.getItem("isDemoUser") || localStorage.getItem("isDemoAdmin");

  return (
    <Box
      h="100vh"
      w="100vw"
      overflow="hidden"
      display="flex"
      flexDirection="column"
      bg="#0f0f0f"
      fontFamily="'Inter', sans-serif"
    >
      {/* ── Top Navbar (48px) ── */}
      <Box
        h="48px"
        bg="#1a1a1a"
        borderBottom="1px solid #2a2a2a"
        display="flex"
        alignItems="center"
        px={4}
        flexShrink={0}
        zIndex={100}
      >
        {/* Left: Logo + lesson nav */}
        <HStack spacing={0} flex="1" h="100%" overflow="hidden">
          <HStack spacing={2} pr={4} mr={2} borderRight="1px solid #2a2a2a" h="100%" align="center" flexShrink={0}>
            <Text fontSize="md" lineHeight="1">🤖</Text>
            <Text color="#e0e0e0" fontWeight="700" fontSize="sm" letterSpacing="-0.01em">AnyBot</Text>
          </HStack>

          {!isLearningPanelOpen && (
            <Tooltip label="Show Learning Panel" placement="bottom">
              <IconButton
                icon={<ChevronRightIcon />}
                size="xs"
                variant="ghost"
                color="#666"
                mr={2}
                onClick={() => setIsLearningPanelOpen(true)}
                _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
              />
            </Tooltip>
          )}

          <HStack spacing={1} px={2} overflow="hidden">
            <Tooltip label="Previous lesson" placement="bottom">
              <IconButton
                icon={<ChevronLeftIcon />}
                size="xs"
                variant="ghost"
                color="#555"
                onClick={goToPrevLesson}
                isDisabled={currentLessonIndex <= 0 || learningLoading}
                _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
                _disabled={{ opacity: 0.25, cursor: "not-allowed" }}
              />
            </Tooltip>
            <Text
              color="#c0c0c0"
              fontSize="sm"
              fontWeight="500"
              maxW="280px"
              noOfLines={1}
              px={1}
              flexShrink={1}
              minW={0}
            >
              {currentLesson ? currentLesson.title : "ROS2 Foundation"}
            </Text>
            <Tooltip label="Next lesson" placement="bottom">
              <IconButton
                icon={<ChevronRightIcon />}
                size="xs"
                variant="ghost"
                color="#555"
                onClick={goToNextLesson}
                isDisabled={currentLessonIndex >= lessons.length - 1 || learningLoading}
                _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
                _disabled={{ opacity: 0.25, cursor: "not-allowed" }}
              />
            </Tooltip>
            {!learningLoading && lessons.length > 0 && (
              <Text color="#444" fontSize="xs" flexShrink={0}>
                {currentLessonIndex + 1}/{lessons.length}
              </Text>
            )}
          </HStack>
        </HStack>

        {/* Right: Actions */}
        <HStack spacing={2} flexShrink={0}>
          <FileSelector
            selectedFile={selectedFile}
            files={workspaceFiles}
            onSelect={setSelectedFile}
            isLoading={filesLoading}
            onRefresh={loadWorkspaceFiles}
          />

          {userMode === "preview" ? (
            <>
              <Tooltip label="Code execution requires an active booking" placement="bottom" bg="#222" color="#aaa">
                <Button
                  size="sm"
                  bg="#222"
                  color="#555"
                  border="1px solid #2a2a2a"
                  _hover={{ bg: "#222" }}
                  cursor="not-allowed"
                  fontSize="xs"
                  fontWeight="600"
                  px={4}
                  h="32px"
                >
                  ▶ Run
                </Button>
              </Tooltip>
              <Button
                size="sm"
                bg="rgba(180,83,9,0.2)"
                color="#f59e0b"
                border="1px solid rgba(180,83,9,0.4)"
                _hover={{ bg: "rgba(180,83,9,0.3)" }}
                onClick={onBack}
                fontSize="xs"
                fontWeight="600"
                px={4}
                h="32px"
              >
                📅 Book Session
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              bg="rgba(22,101,52,0.3)"
              color="#4ade80"
              border="1px solid rgba(22,101,52,0.5)"
              _hover={{ bg: "rgba(22,101,52,0.45)" }}
              onClick={handleRunCode}
              isLoading={codeLoading}
              loadingText="Running..."
              fontSize="xs"
              fontWeight="700"
              px={5}
              h="32px"
            >
              ▶ Run
            </Button>
          )}

          <Box w="1px" h="20px" bg="#2a2a2a" flexShrink={0} />

          <Button
            size="sm"
            variant="ghost"
            color="#666"
            _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
            onClick={onLogsOpen}
            fontSize="xs"
            h="32px"
          >
            Logs
          </Button>

          <Button
            size="sm"
            variant="ghost"
            color="#666"
            _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
            onClick={onBack}
            fontSize="xs"
            h="32px"
          >
            Back
          </Button>

          <Box w="1px" h="20px" bg="#2a2a2a" flexShrink={0} />

          <Tooltip label={`${user.name} — click to logout`} placement="bottom">
            <Avatar
              size="xs"
              name={user.name}
              bg="#2563eb"
              cursor="pointer"
              onClick={onLogout}
            />
          </Tooltip>
          {isDemoUser && (
            <Badge colorScheme="orange" variant="subtle" fontSize="xs">DEMO</Badge>
          )}
        </HStack>
      </Box>

      {/* ── Body ── */}
      <Box flex="1" display="flex" overflow="hidden">

        {/* ── Left Learning Panel ── */}
        <Box
          w={isLearningPanelOpen ? "380px" : "48px"}
          minW={isLearningPanelOpen ? "380px" : "48px"}
          flexShrink={0}
          display="flex"
          flexDirection="column"
          bg="#141414"
          borderRight="1px solid #2a2a2a"
          overflow="hidden"
          transition="width 0.2s ease, min-width 0.2s ease"
        >
          {isLearningPanelOpen ? (
            <>
              {/* Panel header */}
              <Box flexShrink={0} borderBottom="1px solid #2a2a2a">
                <Box px={4} pt={4} pb={0}>
                  <HStack justify="space-between" mb={3} align="flex-start">
                    <VStack align="start" spacing={0}>
                      <Text color="#e0e0e0" fontWeight="700" fontSize="sm" lineHeight="1.3">
                        ROS2 Foundation
                      </Text>
                      <Text color="#555" fontSize="xs" mt={1}>
                        {learningLoading ? "Loading..." : `${completedCount} of ${lessons.length} completed`}
                      </Text>
                    </VStack>
                    <Tooltip label="Collapse panel" placement="right">
                      <IconButton
                        icon={<ChevronLeftIcon />}
                        size="xs"
                        variant="ghost"
                        color="#555"
                        onClick={() => setIsLearningPanelOpen(false)}
                        _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
                        flexShrink={0}
                      />
                    </Tooltip>
                  </HStack>
                  <Progress
                    value={lessons.length ? (completedCount / lessons.length) * 100 : 0}
                    size="xs"
                    colorScheme="green"
                    bg="#222"
                    borderRadius="full"
                    mb={3}
                  />
                </Box>

                {/* Tab bar */}
                <HStack spacing={0} px={4}>
                  {[
                    { key: "lesson", label: "Content" },
                    { key: "lessons", label: "Lessons" },
                  ].map(({ key, label }) => (
                    <Box
                      key={key}
                      px={3}
                      py="10px"
                      cursor="pointer"
                      onClick={() => setLeftPanelTab(key)}
                      borderBottom={leftPanelTab === key ? "2px solid #3b82f6" : "2px solid transparent"}
                      color={leftPanelTab === key ? "#e0e0e0" : "#555"}
                      fontSize="xs"
                      fontWeight={leftPanelTab === key ? "600" : "400"}
                      _hover={{ color: "#c0c0c0" }}
                      transition="all 0.15s"
                      userSelect="none"
                    >
                      {label}
                    </Box>
                  ))}
                </HStack>
              </Box>

              {/* Scrollable body */}
              <Box
                flex="1"
                overflowY="auto"
                sx={{
                  "&::-webkit-scrollbar": { width: "4px" },
                  "&::-webkit-scrollbar-thumb": { background: "#2a2a2a", borderRadius: "2px" },
                  "&::-webkit-scrollbar-track": { background: "transparent" },
                }}
              >
                {leftPanelTab === "lessons" ? (
                  <Box p={3}>
                    {learningLoading ? (
                      <HStack spacing={2} p={2} color="#666">
                        <Spinner size="xs" />
                        <Text fontSize="xs">Loading lessons...</Text>
                      </HStack>
                    ) : (
                      <VStack spacing="2px" align="stretch">
                        {lessons.map((lesson, idx) => {
                          const isSelected = lesson.id === selectedLessonId;
                          const isCompleted = completedLessonIds.has(lesson.id);
                          return (
                            <Box
                              key={lesson.id}
                              px={3}
                              py="10px"
                              cursor="pointer"
                              borderRadius="6px"
                              bg={isSelected ? "rgba(59,130,246,0.1)" : "transparent"}
                              borderLeft={isSelected ? "2px solid #3b82f6" : "2px solid transparent"}
                              _hover={{ bg: isSelected ? "rgba(59,130,246,0.12)" : "rgba(255,255,255,0.03)" }}
                              onClick={() => handleSelectLesson(lesson.id)}
                              transition="all 0.1s"
                            >
                              <HStack spacing={3} align="flex-start">
                                <Text color="#444" fontSize="xs" w="18px" textAlign="right" flexShrink={0} mt="2px" fontVariantNumeric="tabular-nums">
                                  {idx + 1}
                                </Text>
                                <Text
                                  color={isSelected ? "#e0e0e0" : "#999"}
                                  fontSize="sm"
                                  flex="1"
                                  lineHeight="1.4"
                                  noOfLines={2}
                                >
                                  {lesson.title}
                                </Text>
                                {isCompleted && (
                                  <Box
                                    w="16px"
                                    h="16px"
                                    borderRadius="full"
                                    bg="rgba(34,197,94,0.15)"
                                    border="1px solid rgba(34,197,94,0.3)"
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="center"
                                    flexShrink={0}
                                  >
                                    <Text fontSize="8px" color="#4ade80" fontWeight="700">✓</Text>
                                  </Box>
                                )}
                              </HStack>
                            </Box>
                          );
                        })}
                      </VStack>
                    )}
                  </Box>
                ) : (
                  <Box p={4}>
                    {lessonLoading ? (
                      <HStack spacing={2} color="#666">
                        <Spinner size="xs" />
                        <Text fontSize="xs">Loading content...</Text>
                      </HStack>
                    ) : learningError ? (
                      <Alert
                        status="error"
                        borderRadius="6px"
                        bg="rgba(220,38,38,0.08)"
                        border="1px solid rgba(220,38,38,0.2)"
                        py={2}
                        px={3}
                      >
                        <AlertIcon color="#f87171" boxSize="14px" />
                        <Text color="#f87171" fontSize="xs">{learningError}</Text>
                      </Alert>
                    ) : selectedLessonContent ? (
                      <>
                        {currentLesson && (
                          <Text color="#e0e0e0" fontWeight="700" fontSize="md" mb={4} lineHeight="1.4">
                            {currentLesson.title}
                          </Text>
                        )}
                        <MarkdownLessonContent content={selectedLessonContent} />
                      </>
                    ) : (
                      <Text color="#555" fontSize="sm" lineHeight="1.6">
                        Select a lesson from the{" "}
                        <Text
                          as="span"
                          color="#3b82f6"
                          cursor="pointer"
                          _hover={{ textDecoration: "underline" }}
                          onClick={() => setLeftPanelTab("lessons")}
                        >
                          Lessons
                        </Text>{" "}
                        tab to get started.
                      </Text>
                    )}
                  </Box>
                )}
              </Box>

              {/* Footer: Complete button */}
              <Box p={3} borderTop="1px solid #2a2a2a" flexShrink={0}>
                <Button
                  w="full"
                  size="sm"
                  variant="ghost"
                  border="1px solid"
                  borderColor={
                    selectedLessonId && completedLessonIds.has(selectedLessonId)
                      ? "rgba(133,77,14,0.5)"
                      : "rgba(22,101,52,0.5)"
                  }
                  color={
                    selectedLessonId && completedLessonIds.has(selectedLessonId)
                      ? "#f59e0b"
                      : "#4ade80"
                  }
                  _hover={{
                    bg:
                      selectedLessonId && completedLessonIds.has(selectedLessonId)
                        ? "rgba(133,77,14,0.12)"
                        : "rgba(22,101,52,0.15)",
                  }}
                  onClick={toggleLessonCompletion}
                  isLoading={progressSaving}
                  isDisabled={!selectedLessonId}
                  fontSize="xs"
                  fontWeight="600"
                  h="34px"
                >
                  {selectedLessonId && completedLessonIds.has(selectedLessonId)
                    ? "Mark as Incomplete"
                    : "Mark as Complete ✓"}
                </Button>
              </Box>
            </>
          ) : (
            /* Collapsed */
            <VStack h="100%" align="center" pt={3} spacing={4}>
              <Tooltip label="Expand Learning Panel" placement="right">
                <IconButton
                  icon={<ChevronRightIcon />}
                  size="sm"
                  variant="ghost"
                  color="#555"
                  onClick={() => setIsLearningPanelOpen(true)}
                  _hover={{ color: "#e0e0e0", bg: "rgba(255,255,255,0.06)" }}
                />
              </Tooltip>
              {!learningLoading && lessons.length > 0 && (
                <Tooltip label={`${completedCount}/${lessons.length} lessons completed`} placement="right">
                  <Box w="4px" h="60px" bg="#222" borderRadius="4px" overflow="hidden" position="relative">
                    <Box
                      position="absolute"
                      bottom="0"
                      w="100%"
                      bg="#22c55e"
                      borderRadius="4px"
                      h={`${(completedCount / lessons.length) * 100}%`}
                      transition="height 0.3s ease"
                    />
                  </Box>
                </Tooltip>
              )}
            </VStack>
          )}
        </Box>

        {/* ── Right: IDE + Video ── */}
        <Box flex="1" display="flex" flexDirection="column" overflow="hidden" minW={0}>

          {/* Right panel tab header (40px) */}
          <Box
            h="40px"
            bg="#1a1a1a"
            borderBottom="1px solid #2a2a2a"
            display="flex"
            alignItems="stretch"
            flexShrink={0}
          >
            <HStack spacing={0} flex="1" px={2}>
              {[
                { key: "ide-expanded", label: "</> IDE" },
                { key: "video-expanded", label: "📹 Video" },
                { key: "split", label: "⇔ Split" },
              ].map(({ key, label }) => (
                <Box
                  key={key}
                  px={4}
                  h="100%"
                  display="flex"
                  alignItems="center"
                  cursor="pointer"
                  borderBottom={panelLayout === key ? "2px solid #3b82f6" : "2px solid transparent"}
                  color={panelLayout === key ? "#e0e0e0" : "#555"}
                  fontSize="xs"
                  fontWeight={panelLayout === key ? "600" : "400"}
                  _hover={{ color: "#c0c0c0" }}
                  transition="all 0.15s"
                  userSelect="none"
                  onClick={() => {
                    if (key === "ide-expanded") expandIDE();
                    else if (key === "video-expanded") expandVideo();
                    else resetSplit();
                  }}
                >
                  {label}
                </Box>
              ))}
            </HStack>
            <HStack spacing={2} px={3} flexShrink={0}>
              <Badge
                colorScheme={hasActiveBooking ? "green" : "orange"}
                variant="subtle"
                fontSize="xs"
              >
                {hasActiveBooking ? "Booking" : "Preview"}
              </Badge>
            </HStack>
          </Box>

          {/* Right panel content */}
          <Box
            flex="1"
            display="flex"
            overflow="hidden"
            ref={containerRef}
          >
            {/* IDE panel */}
            <Box
              w={getLeftPanelWidth()}
              h="100%"
              display={panelLayout === "video-expanded" ? "none" : "flex"}
              flexDirection="column"
              overflow="hidden"
              flexShrink={0}
            >
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

            {/* Drag divider (split mode only) */}
            {panelLayout === "split" && (
              <Box
                w="4px"
                bg="#242424"
                cursor="col-resize"
                flexShrink={0}
                position="relative"
                _hover={{ bg: "#3b82f6" }}
                transition="background 0.15s"
                onMouseDown={handleMouseDown}
              >
                <Box
                  position="absolute"
                  top="50%"
                  left="50%"
                  transform="translate(-50%, -50%)"
                  w="14px"
                  h="28px"
                  bg="rgba(255,255,255,0.06)"
                  borderRadius="3px"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  color="#444"
                  fontSize="9px"
                  letterSpacing="-1px"
                >
                  ⋮
                </Box>
              </Box>
            )}

            {/* Video panel */}
            <Box
              w={getRightPanelWidth()}
              h="100%"
              display={panelLayout === "ide-expanded" ? "none" : "flex"}
              flexDirection="column"
              overflow="hidden"
              bg="#0f0f0f"
              p={3}
              flexShrink={0}
            >
              <Box
                flex="1"
                borderRadius="8px"
                overflow="hidden"
                bg="#141414"
                border="1px solid #2a2a2a"
                display="flex"
                flexDirection="column"
                minH={0}
              >
                {showVideo && videoUrl ? (
                  <Box flex="1" overflow="hidden" minH={0}>
                    <video
                      width="100%"
                      height="100%"
                      controls
                      autoPlay
                      playsInline
                      muted
                      style={{ background: "#000", objectFit: "contain", height: "100%" }}
                    >
                      <source src={videoUrl} type="video/mp4" />
                    </video>
                  </Box>
                ) : userMode === "preview" ? (
                  <VStack justify="center" align="center" flex="1" spacing={5} p={8} bg="#0d0d0d">
                    <Box
                      w="52px"
                      h="52px"
                      borderRadius="10px"
                      bg="#1a1a1a"
                      border="1px solid #2a2a2a"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                      fontSize="xl"
                    >
                      📹
                    </Box>
                    <VStack spacing={2} textAlign="center">
                      <Text color="#e0e0e0" fontWeight="600" fontSize="sm">Live Robot Feed</Text>
                      <Text color="#555" fontSize="xs" maxW="200px" lineHeight="1.7">
                        Real-time robot video requires an active booking session.
                      </Text>
                    </VStack>
                    <Button
                      size="sm"
                      bg="rgba(180,83,9,0.2)"
                      color="#f59e0b"
                      border="1px solid rgba(180,83,9,0.3)"
                      _hover={{ bg: "rgba(180,83,9,0.3)" }}
                      onClick={onBack}
                      fontSize="xs"
                      fontWeight="600"
                    >
                      📅 Book a Session
                    </Button>
                  </VStack>
                ) : (
                  <Box flex="1" overflow="hidden" minH={0}>
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
                  </Box>
                )}
              </Box>

              {(hasAccess || showVideo) && (
                <HStack pt={2} spacing={2} justify="flex-end" flexShrink={0}>
                  {hasAccess && (
                    <Button
                      size="xs"
                      variant="ghost"
                      border="1px solid #2a2a2a"
                      color="#666"
                      _hover={{ color: "#e0e0e0", borderColor: "#444" }}
                      onClick={handleGetRealResult}
                      isLoading={videoLoading}
                      loadingText="Loading..."
                      fontSize="xs"
                    >
                      Get Result Video
                    </Button>
                  )}
                  {showVideo && (
                    <Button
                      size="xs"
                      variant="ghost"
                      border="1px solid #2a2a2a"
                      color="#666"
                      _hover={{ color: "#e0e0e0", borderColor: "#444" }}
                      onClick={() => {
                        setShowVideo(false);
                        if (videoUrl) { URL.revokeObjectURL(videoUrl); setVideoUrl(null); }
                      }}
                      fontSize="xs"
                    >
                      Back to Live Feed
                    </Button>
                  )}
                </HStack>
              )}
            </Box>
          </Box>
        </Box>
      </Box>

      {/* ── Container Logs Modal ── */}
      <Modal isOpen={isLogsOpen} onClose={onLogsClose} size="4xl">
        <ModalOverlay backdropFilter="blur(4px)" bg="rgba(0,0,0,0.75)" />
        <ModalContent bg="#1a1a1a" border="1px solid #2a2a2a" boxShadow="0 24px 64px rgba(0,0,0,0.6)">
          <ModalHeader pb={3} borderBottom="1px solid #2a2a2a">
            <HStack justify="space-between" align="center" pr={8}>
              <HStack spacing={3}>
                <Text color="#e0e0e0" fontWeight="700" fontSize="sm">Container Logs</Text>
                <Badge colorScheme={autoRefresh ? "green" : "gray"} variant="subtle" fontSize="xs">
                  {autoRefresh ? "● Live" : "Paused"}
                </Badge>
              </HStack>
              <HStack spacing={1}>
                <Button
                  size="xs"
                  variant={logsType === "preview" ? "solid" : "ghost"}
                  colorScheme={logsType === "preview" ? "blue" : "gray"}
                  onClick={() => switchLogsType("preview")}
                  color={logsType === "preview" ? "white" : "#666"}
                >
                  Preview IDE
                </Button>
                {hasActiveBooking && (
                  <Button
                    size="xs"
                    variant={logsType === "booking" ? "solid" : "ghost"}
                    colorScheme={logsType === "booking" ? "green" : "gray"}
                    onClick={() => switchLogsType("booking")}
                    color={logsType === "booking" ? "white" : "#666"}
                  >
                    Booking IDE
                  </Button>
                )}
              </HStack>
            </HStack>
          </ModalHeader>
          <ModalCloseButton color="#666" />

          <ModalBody p={0}>
            <Box
              bg="#0a0a0a"
              fontFamily="'Courier New', Courier, monospace"
              fontSize="12px"
              h="55vh"
              overflowY="auto"
              p={4}
              sx={{
                "&::-webkit-scrollbar": { width: "4px" },
                "&::-webkit-scrollbar-thumb": { background: "#2a2a2a", borderRadius: "2px" },
              }}
            >
              {logsLoading && logs.length === 0 ? (
                <HStack justify="center" mt={8}>
                  <Spinner size="sm" color="#3b82f6" />
                  <Text color="#666">Fetching logs...</Text>
                </HStack>
              ) : logsError ? (
                <Text color="#f87171">Error: {logsError}</Text>
              ) : logs.length === 0 ? (
                <Text color="#444">No log output yet. Container may still be starting.</Text>
              ) : (
                <>
                  {logs.map((line, i) => {
                    const lower = line.toLowerCase();
                    let color = "#888";
                    if (lower.includes("error") || lower.includes("fatal") || lower.includes("exception")) color = "#f87171";
                    else if (lower.includes("warn")) color = "#fbbf24";
                    else if (lower.includes("info") || lower.includes("✅") || lower.includes("started") || lower.includes("ready")) color = "#4ade80";
                    else if (lower.includes("debug")) color = "#60a5fa";
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

          <ModalFooter borderTop="1px solid #2a2a2a" py={3} gap={2}>
            <Text color="#444" fontSize="xs" flex="1">
              {logs.length} line{logs.length !== 1 ? "s" : ""} · {user.name} · {logsType}
            </Text>
            <Button size="sm" variant="ghost" color="#666" _hover={{ color: "#e0e0e0" }} onClick={() => setAutoRefresh((r) => !r)} fontSize="xs">
              {autoRefresh ? "⏸ Pause" : "▶ Auto-refresh"}
            </Button>
            <Button size="sm" variant="ghost" color="#666" _hover={{ color: "#e0e0e0" }} isLoading={logsLoading} onClick={() => fetchLogs()} fontSize="xs">
              ↻ Refresh
            </Button>
            <Button size="sm" variant="ghost" color="#666" _hover={{ color: "#e0e0e0" }} onClick={() => navigator.clipboard.writeText(logs.join("\n"))} isDisabled={logs.length === 0} fontSize="xs">
              ⎘ Copy All
            </Button>
            <Button size="sm" variant="ghost" color="#666" _hover={{ color: "#e0e0e0" }} onClick={onLogsClose} fontSize="xs">
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default NeonRobotConsole;
