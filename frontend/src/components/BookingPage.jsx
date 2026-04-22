import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Container,
  Card,
  CardBody,
  CardHeader,
  SimpleGrid,
  Badge,
  Avatar,
  Divider,
  useToast,
  Select,
  Input,
  FormControl,
  FormLabel,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Alert,
  AlertIcon,
  AlertDescription,
  IconButton,
  Fade,
} from "@chakra-ui/react";
import "../styles/booking.css";
import { useState, useEffect, useMemo } from "react";
import { createBooking, getUserBookings, getBookingSchedule, getActiveAnnouncements, getAvailableSlots, getAvailableRobots } from "../api";
import ServiceStatus from "./ServiceStatus";
import CountdownTimer from "./CountdownTimer";
import TimeSlotGrid from "./TimeSlotGrid";
import { ChevronUpIcon } from "@chakra-ui/icons";

// Generate realistic time slots based on business rules - NO DUMMY DATA
const generateAvailableTimeSlots = async (authToken, selectedDate, selectedRobotId, robotLookup) => {
  if (!authToken || !selectedDate || !selectedRobotId) {
    return [];
  }

  try {
    const response = await getAvailableSlots(
      selectedDate,
      selectedRobotId,
      authToken,
      robotLookup?.[selectedRobotId]?.type
    );
    const slots = response.available_slots || [];
    return Array.isArray(slots) ? slots.map((slot, index) => ({
      id: `slot_${selectedDate}_${slot.start_time}_${selectedRobotId}`,
      date: slot.date,
      startTime: slot.start_time,
      endTime: slot.end_time,
      robotId: slot.robot_id || selectedRobotId,
      robotType: slot.robot_type,
      available: true,
      bookedBy: null,
      duration: slot.duration_hours
    })) : [];
  } catch (error) {
    console.error('Error fetching available slots:', error);
    throw error; // Throw error instead of returning empty array for better error handling
  }
};

const BookingPage = ({ user, authToken, onBooking, onLogout, onAdminAccess }) => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [bookedSlots, setBookedSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedRobotId, setSelectedRobotId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [userBookings, setUserBookings] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [availableRobots, setAvailableRobots] = useState({});
  const [slotError, setSlotError] = useState(null);
  const [isAutoFetching, setIsAutoFetching] = useState(false);
  // Track which booking countdowns have expired to enable "View Booking" button
  const [expiredCountdowns, setExpiredCountdowns] = useState(new Set());
  const [showScrollTop, setShowScrollTop] = useState(false);
  const toast = useToast();

  // Handle scroll to top button visibility
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      setShowScrollTop(scrollTop > 300);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Scroll to top function
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // Handle countdown expiration for a specific booking
  const handleCountdownExpired = (bookingId) => {
    setExpiredCountdowns(prev => new Set([...prev, bookingId]));
    // Reload bookings when countdown expires to update status
    loadBookings();
  };

  // Check if user is a demo user (for unrestricted console access)
  const isDemoUser = () => {
    return user?.isDemoUser || user?.isDemoAdmin ||
      localStorage.getItem('isDemoUser') ||
      localStorage.getItem('isDemoAdmin') ||
      localStorage.getItem('isDemoMode') ||
      (user?.email && (user.email.includes('demo') || user.email.includes('test') || user.email.includes('example')));
  };

  // Booking classification - separate upcoming and past bookings
  const classifiedBookings = useMemo(() => {
    const now = new Date();
    const upcoming = [];
    const past = [];

    // Ensure userBookings is an array
    const bookings = Array.isArray(userBookings) ? userBookings : [];

    bookings.forEach(booking => {
      const bookingDateTime = new Date(`${booking.date}T${booking.start_time}`);
      const bookingEndTime = new Date(`${booking.date}T${booking.end_time}`);

      // Consider booking as past if end time has passed
      if (bookingEndTime < now) {
        past.push({
          ...booking,
          status: 'past',
          timeStatus: 'completed'
        });
      } else if (bookingDateTime <= now && bookingEndTime > now) {
        // Booking is currently active
        upcoming.push({
          ...booking,
          status: 'active',
          timeStatus: 'in-progress'
        });
      } else {
        // Booking is in the future
        upcoming.push({
          ...booking,
          status: 'upcoming',
          timeStatus: 'scheduled'
        });
      }
    });

    // Sort upcoming by start time (earliest first)
    upcoming.sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`));

    // Sort past by start time (most recent first)
    past.sort((a, b) => new Date(`${b.date}T${b.start_time}`) - new Date(`${a.date}T${a.start_time}`));

    return { upcoming, past };
  }, [userBookings]);

  useEffect(() => {
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);

    // Load user bookings, booked slots, announcements, and available robots
    loadBookings();
    loadAnnouncements();
    loadRobots();

    // Set up interval to update booking classifications every minute
    const interval = setInterval(() => {
      // This will trigger the useMemo recalculation
      setUserBookings(prev => [...prev]);
    }, 60000);

    return () => clearInterval(interval);
  }, [authToken]);

  const loadRobots = async () => {
    try {
      // Only load real robots from API - no fallback to dummy data
      const robotData = await getAvailableRobots();
      const registry = Array.isArray(robotData.registry) ? robotData.registry : [];

      // Convert to format keyed by robot_id with metadata
      const formattedRobots = {};
      registry.forEach(robot => {
        const robotType = robot.type || "";
        let emoji = "🤖"; // default emoji
        if (robotType.includes("arm")) emoji = "🦾";
        else if (robotType.includes("hand")) emoji = "🤲";
        else if (robotType.includes("turtle")) emoji = "🤖";

        formattedRobots[String(robot.id)] = {
          id: robot.id,
          name: robot.name || robotType,
          type: robotType,
          image: robot.container_image,
          emoji
        };
      });

      setAvailableRobots(formattedRobots);
      if (!selectedRobotId && registry.length === 1) {
        setSelectedRobotId(String(registry[0].id));
      }
    } catch (error) {
      console.error('Error loading robots:', error);
      // Show empty robots if API fails - no fallback to dummy data
      setAvailableRobots({});
      toast({
        title: "Unable to load robots",
        description: "Please check your connection and try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  // Auto-fetch available slots when date or robot selection changes
  useEffect(() => {
    loadAvailableSlots();
  }, [selectedDate, selectedRobotId, authToken]);

  const loadAvailableSlots = async () => {
    // Clear previous error
    setSlotError(null);

    // Only load slots if we have auth token and both date and robot selected
    if (!authToken || !selectedDate || !selectedRobotId) {
      setTimeSlots([]);
      return;
    }

    setIsAutoFetching(true);
    try {
      // Load real available slots from API only
      const slots = await generateAvailableTimeSlots(authToken, selectedDate, selectedRobotId, availableRobots);
      setTimeSlots(slots);

      if (slots.length === 0) {
        setSlotError("No time slots available for the selected robot and date.");
      }
    } catch (error) {
      console.error('Error loading available slots:', error);
      const backendDetail = error?.response?.data?.detail;
      setSlotError(backendDetail || error.message || 'Failed to load time slots. Please try again.');
      setTimeSlots([]);

      toast({
        title: "Error loading time slots",
        description: backendDetail || "Unable to fetch available booking slots. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsAutoFetching(false);
    }
  };

  const loadBookings = async () => {
    try {
      if (authToken) {
        // Only load real authenticated bookings - no demo data
        const bookings = await getUserBookings(authToken);
        setUserBookings(bookings);

        // Get booking schedule for the next 7 days
        const today = new Date();
        const endDate = new Date(today);
        endDate.setDate(today.getDate() + 7);

        const schedule = await getBookingSchedule(
          today.toISOString().split('T')[0],
          endDate.toISOString().split('T')[0]
        );
        setBookedSlots(schedule.bookings || []);
      } else {
        // No auth token - clear data, no fallback to dummy data
        setUserBookings([]);
        setBookedSlots([]);
      }
    } catch (error) {
      console.error('Error loading bookings:', error);
      toast({
        title: "Error loading bookings",
        description: "Unable to load your bookings. Please refresh the page.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const loadAnnouncements = async () => {
    try {
      const response = await getActiveAnnouncements();
      setAnnouncements(response.announcements || []);
    } catch (error) {
      console.error('Error loading announcements:', error);
    }
  };



  // Helper function to ensure 24-hour format consistency
  const ensureTwentyFourHourFormat = (timeStr) => {
    try {
      // If already in 24-hour format (no AM/PM), return as-is
      if (!/AM|PM/i.test(timeStr)) {
        return timeStr;
      }

      // Convert 12-hour format to 24-hour format (for backward compatibility)
      const date = new Date(`1970-01-01 ${timeStr}`);
      return date.toLocaleTimeString('en-GB', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Time format error:', error);
      return timeStr; // Return original if conversion fails
    }
  };

  const handleBookSlot = async (slot) => {
    // Enforce authentication requirement - no demo mode
    if (!authToken) {
      toast({
        title: "Authentication Required",
        description: "You must be logged in to make a booking. Please sign in first.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);

    try {
      // Regular authenticated booking with enhanced validation
      const bookingData = {
        robot_id: slot.robotId,
        robot_type: slot.robotType,
        date: slot.date,
        start_time: ensureTwentyFourHourFormat(slot.startTime),
        end_time: ensureTwentyFourHourFormat(slot.endTime)
      };

      const booking = await createBooking(bookingData, authToken);

      // Update local state by reloading available slots and bookings
      await loadBookings();
      await loadAvailableSlots();

      onBooking({
        ...slot,
        bookingId: booking.id,
        available: false,
        bookedBy: user.name,
        bookingTime: booking.created_at,
      });

      toast({
        title: "Development session booked!",
        description: `Your coding console is reserved for ${slot.date} from ${slot.startTime} to ${slot.endTime}`,
        status: "success",
        duration: 5000,
        isClosable: true,
      });

    } catch (error) {
      console.error('Booking error:', error);

      // Enhanced error message handling
      let errorMessage = "Failed to book session. Please try again.";

      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      // Specific error handling for common cases
      if (errorMessage.includes("conflicts with existing booking")) {
        errorMessage = "This time slot is no longer available. Please select a different time.";
      } else if (errorMessage.includes("working hours")) {
        errorMessage = "Bookings are only allowed during working hours (9:00 AM - 6:00 PM).";
      } else if (errorMessage.includes("duration")) {
        errorMessage = "Session duration must be between 1-2 hours during working hours.";
      }

      toast({
        title: "Booking failed",
        description: errorMessage,
        status: "error",
        duration: 7000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getDateOptions = () => {
    const today = new Date();
    const options = [];

    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];
      const label = i === 0 ? 'Today' :
        i === 1 ? 'Tomorrow' :
          date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
      options.push({ value: dateStr, label });
    }

    return options;
  };

  // Ensure arrays before mapping - prevents "X.map is not a function" errors
  const safeAnnouncements = Array.isArray(announcements) ? announcements : [];
  const safeUpcoming = Array.isArray(classifiedBookings?.upcoming) ? classifiedBookings.upcoming : [];
  const safePast = Array.isArray(classifiedBookings?.past) ? classifiedBookings.past : [];
  const safeAvailableRobotsKeys = (availableRobots && typeof availableRobots === "object") ? Object.keys(availableRobots) : [];

  return (
    <Box
      className="booking-page"
      w="full"
      minH="100vh"
      pb={20}
      css={{
        WebkitOverflowScrolling: 'touch', // Smooth scrolling on iOS
      }}
    >
      <Container maxW="7xl" py={8} px={{ base: 4, md: 8 }}>
        <VStack spacing={8} w="full">
          {/* Header */}
          <HStack w="full" justify="space-between">

            <VStack align="start" spacing={1}>

              <Text fontSize="3xl" fontWeight="bold" color="black">
                Book Development Console Session
              </Text>

              <div className="user-info">

                <div className="user-left">
                  <div className="avatar">
                    {user.name.charAt(0).toUpperCase()}
                  </div>

                  <div className="user-text">
                    Welcome, <span>{user.name}</span>
                  </div>
                </div>



                {user.role === 'admin' && (
                  <Badge colorScheme="purple" ml={2}>Admin</Badge>
                )}
                {(user?.isDemoUser || user?.isDemoAdmin || localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin')) && (
                  <Badge colorScheme="orange" ml={2}>DEMO MODE</Badge>
                )}
              </div>


            </VStack>

            <HStack spacing={3}>
              {onAdminAccess && user.role === 'admin' && (
                <Button colorScheme="purple" onClick={onAdminAccess}>
                  Admin Dashboard
                </Button>
              )}

              <Button
                className="btn-primary1 logout-btn"
                onClick={onLogout}
              >
                Logout
              </Button>

            </HStack>
          </HStack>

          {/* Service Status */}
          <Box w="full">
            <ServiceStatus showDetails={false} />
          </Box>

          {/* Demo User Direct Access */}
          {isDemoUser() && (
            <Card w="full" bg="orange.900" border="1px solid" borderColor="orange.500">
              <CardBody>
                <VStack align="start" spacing={4}>
                  <HStack>
                    <Text fontSize="lg" fontWeight="bold" color="orange.100">
                      🎯 Demo Mode - Unrestricted Access
                    </Text>
                    <Badge colorScheme="orange" size="sm">DEMO</Badge>
                  </HStack>
                  <Text color="orange.200" fontSize="sm">
                    As a demo user, you have unrestricted access to the robot console. You can access the console immediately without waiting for countdown timers or booking restrictions.
                  </Text>
                  <Button
                    colorScheme="orange"
                    size="md"
                    onClick={() => onBooking({
                      id: `demo_direct_access`,
                      robotType: 'turtlebot', // Use a valid robot type that exists in the system
                      date: new Date().toISOString().split('T')[0],
                      startTime: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
                      endTime: new Date(Date.now() + 2 * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
                      bookingId: 'demo_direct',
                      available: true,
                      bookedBy: user.name
                    })}
                  >
                    🚀 Enter Console Now (Demo Access)
                  </Button>
                </VStack>
              </CardBody>
            </Card>
          )}

          {/* Booking Guidelines */}
          <div className="booking-guidelines">

            <div className="guidelines-title">
              📋 Booking Guidelines
            </div>

            <div className="guidelines-stats">

              <div className="guide-box">
                <div className="guide-icon">⏰</div>
                <div className="guide-value">Working Hours</div>
                <div className="guide-label">9 AM - 6 PM</div>

              </div>

              <div className="guide-box">
                <div className="guide-icon">⌛</div>
                <div className="guide-value">Session Duration</div>
                <div className="guide-label">1 - 2 Hours</div>

              </div>

              <div className="guide-box">
                <div className="guide-icon">🤖</div>
                <div className="guide-value">Authentication</div>
                <div className="guide-label">Login Required</div>

              </div>

              <div className="guide-box">
                <div className="guide-icon">⚡</div>
                <div className="guide-value">Availability</div>
                <div className="guide-label">Real-time</div>
              </div>

            </div>

          </div>

          {/* Active Announcements */}
          {safeAnnouncements.length > 0 && (
            <VStack spacing={4} w="full">
              {safeAnnouncements.map((announcement) => (
                <Card
                  key={announcement.id}
                  w="full"
                  bg={
                    announcement.priority === 'high' ? 'red.900' :
                      announcement.priority === 'normal' ? 'blue.900' : 'gray.800'
                  }
                  border="1px solid"
                  borderColor={
                    announcement.priority === 'high' ? 'red.500' :
                      announcement.priority === 'normal' ? 'blue.500' : 'gray.600'
                  }
                >
                  <CardBody>
                    <VStack align="start" spacing={2}>
                      <HStack justify="space-between" w="full">
                        <Text fontSize="lg" fontWeight="bold" color="white">
                          📢 {announcement.title}
                        </Text>
                        <Badge
                          colorScheme={
                            announcement.priority === 'high' ? 'red' :
                              announcement.priority === 'normal' ? 'blue' : 'gray'
                          }
                          size="sm"
                        >
                          {announcement.priority}
                        </Badge>
                      </HStack>
                      <Text color="gray.300" whiteSpace="pre-wrap">
                        {announcement.content}
                      </Text>
                      <Text color="gray.500" fontSize="sm">
                        {new Date(announcement.created_at).toLocaleDateString()}
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          )}

          {/* Robot and Date Selection */}
          <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
            <CardHeader>
              <Text fontSize="lg" fontWeight="bold" color="white">
                Select Robot and Date
              </Text>
            </CardHeader>
            <CardBody>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl>
                  <FormLabel color="gray.300">Date</FormLabel>
                  <Select
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    bg="gray.700"
                    border="1px solid"
                    borderColor="gray.600"
                    color="white"
                    placeholder="Select a date"
                  >
                    {getDateOptions().map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel color="gray.300">Robot Environment</FormLabel>
                  <Select
                    value={selectedRobotId}
                    onChange={(e) => setSelectedRobotId(e.target.value)}
                    bg="gray.700"
                    border="1px solid"
                    borderColor="gray.600"
                    color="white"
                    placeholder="Select a robot"
                  >
                    {safeAvailableRobotsKeys.map(robotKey => (
                      <option key={robotKey} value={robotKey}>
                        {availableRobots[robotKey].emoji} {availableRobots[robotKey].name} ({availableRobots[robotKey].type})
                      </option>
                    ))}
                  </Select>
                </FormControl>
              </SimpleGrid>
              {isAutoFetching && (
                <Text mt={3} color="blue.300" fontSize="sm">
                  🔄 Auto-fetching available time slots...
                </Text>
              )}
            </CardBody>
          </Card>

          {/* Error Display */}
          {slotError && (
            <Alert status="error" bg="red.900" border="1px solid" borderColor="red.700">
              <AlertIcon />
              <AlertDescription color="red.200">
                {slotError}
              </AlertDescription>
            </Alert>
          )}

          {/* Time Slot Grid */}
          {!slotError && (
            <TimeSlotGrid
              selectedDate={selectedDate}
              selectedRobot={selectedRobotId}
              availableSlots={timeSlots}
              bookedSlots={bookedSlots}
              onSlotSelect={handleBookSlot}
              isLoading={isLoading}
              availableRobots={availableRobots}
            />
          )}


          {/* Code Preview Access - Always Available */}
          {authToken && !isDemoUser() && (
            <div className="code-preview-section">
              <div className="code-preview-card">

                <div className="code-preview-content">

                  <div className="code-preview-text">
                    <div className="code-preview-title">
                      💻 Development Environment
                      <span className="preview-badge">Always Available</span>
                    </div>

                    <div className="code-preview-desc">
                      Access your personal IDE to write, edit, and save robot code anytime.
                    </div>

                    <div className="code-preview-sub">
                      Preview Mode: Full code editing Book a session for robot execution and live video feed
                    </div>
                  </div>

                  <button
                    className="btn-primary1 code-preview-btn"
                    onClick={() => onBooking({
                      id: `code_preview_${Date.now()}`,
                      robotType: 'turtlebot',
                      date: new Date().toISOString().split('T')[0],
                      startTime: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
                      endTime: new Date(Date.now() + 1 * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
                      bookingId: 'code_preview',
                      available: true,
                      bookedBy: user.name,
                      isPreview: true
                    })}
                  >
                    📝 Code Preview
                  </button>

                </div>

              </div>
            </div>
          )}

          {/* User's Bookings with Classification */}
          {authToken && (classifiedBookings.upcoming.length > 0 || classifiedBookings.past.length > 0) && (
            <VStack w="full" spacing={6} mt={8}>
              <Divider borderColor="gray.600" />

              <Tabs variant="enclosed" colorScheme="blue" w="full">
                <TabList>
                  <Tab>
                    Upcoming Sessions ({classifiedBookings.upcoming.length})
                  </Tab>
                  <Tab>
                    Past Sessions ({classifiedBookings.past.length})
                  </Tab>
                </TabList>

                <TabPanels>
                  {/* Upcoming Bookings */}
                  <TabPanel px={0} py={6}>
                    {classifiedBookings.upcoming.length === 0 ? (
                      <Card bg="gray.800" border="1px solid" borderColor="gray.600">
                        <CardBody textAlign="center" py={8}>
                          <Text color="gray.400">No upcoming sessions</Text>
                        </CardBody>
                      </Card>
                    ) : (
                      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} w="full">
                        {safeUpcoming.map((booking) => (
                          <Card
                            key={booking.id}
                            bg={booking.timeStatus === 'in-progress' ? 'orange.900' : 'green.900'}
                            border="1px solid"
                            borderColor={booking.timeStatus === 'in-progress' ? 'orange.600' : 'green.600'}
                          >
                            <CardBody>
                              <VStack spacing={3} align="start">
                                <HStack justify="space-between" w="full">
                                  <Badge
                                    colorScheme={booking.timeStatus === 'in-progress' ? 'orange' : 'green'}
                                  >
                                    {booking.timeStatus === 'in-progress' ? 'In Progress' : 'Scheduled'}
                                  </Badge>
                                  <HStack>
                                    <Text fontSize="xl">{availableRobots[String(booking.robot_id)]?.emoji || "🤖"}</Text>
                                    <Text fontSize="sm" color="green.100">
                                      {availableRobots[String(booking.robot_id)]?.name || booking.robot_name || booking.robot_type}
                                    </Text>
                                  </HStack>
                                </HStack>

                                <VStack align="start" spacing={1}>
                                  <Text color="green.100" fontWeight="bold">
                                    {new Date(booking.date).toLocaleDateString('en-US', {
                                      weekday: 'long',
                                      month: 'long',
                                      day: 'numeric'
                                    })}
                                  </Text>
                                  <Text color="green.200" fontSize="lg">
                                    {booking.start_time} - {booking.end_time}
                                  </Text>
                                </VStack>

                                {booking.timeStatus === 'scheduled' && (
                                  <CountdownTimer
                                    targetDate={booking.date}
                                    targetTime={booking.start_time}
                                    onExpired={() => {
                                      handleCountdownExpired(booking.id);
                                    }}
                                  />
                                )}

                                <Button
                                  colorScheme={booking.timeStatus === 'in-progress' ? 'orange' : 'green'}
                                  size="sm"
                                  w="full"
                                  isDisabled={
                                    // Demo users have unrestricted access
                                    isDemoUser() ? false :
                                      // Regular users need countdown to expire for scheduled bookings
                                      (booking.timeStatus === 'scheduled' && !expiredCountdowns.has(booking.id))
                                  }
                                  onClick={() => onBooking({
                                    id: `booking_${booking.id}`,
                                    robotType: booking.robot_type,
                                    robotId: booking.robot_id,
                                    date: booking.date,
                                    startTime: booking.start_time,
                                    endTime: booking.end_time,
                                    bookingId: booking.id,
                                    available: false,
                                    bookedBy: user.name
                                  })}
                                >
                                  {booking.timeStatus === 'in-progress' ? 'Enter Console' :
                                    (booking.timeStatus === 'scheduled' && !expiredCountdowns.has(booking.id) && !isDemoUser() ? 'View Booking (Countdown Active)' :
                                      booking.timeStatus === 'scheduled' && isDemoUser() ? 'Enter Console (Demo Access)' : 'Enter Console')}
                                </Button>
                              </VStack>
                            </CardBody>
                          </Card>
                        ))}
                      </SimpleGrid>
                    )}
                  </TabPanel>

                  {/* Past Bookings */}
                  <TabPanel px={0} py={6}>
                    {classifiedBookings.past.length === 0 ? (
                      <Card bg="gray.800" border="1px solid" borderColor="gray.600">
                        <CardBody textAlign="center" py={8}>
                          <Text color="gray.400">No past sessions</Text>
                        </CardBody>
                      </Card>
                    ) : (
                      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} w="full">
                        {safePast.map((booking) => (
                          <Card
                            key={booking.id}
                            bg="gray.800"
                            border="1px solid"
                            borderColor="gray.600"
                            opacity={0.8}
                          >
                            <CardBody>
                              <VStack spacing={3} align="start">
                                <HStack justify="space-between" w="full">
                                  <Badge colorScheme="gray">Completed</Badge>
                                  <HStack>
                                    <Text fontSize="xl">{availableRobots[String(booking.robot_id)]?.emoji || "🤖"}</Text>
                                    <Text fontSize="sm" color="gray.400">
                                      {availableRobots[String(booking.robot_id)]?.name || booking.robot_name || booking.robot_type}
                                    </Text>
                                  </HStack>
                                </HStack>

                                <VStack align="start" spacing={1}>
                                  <Text color="gray.300" fontWeight="bold">
                                    {new Date(booking.date).toLocaleDateString('en-US', {
                                      weekday: 'long',
                                      month: 'long',
                                      day: 'numeric'
                                    })}
                                  </Text>
                                  <Text color="gray.400" fontSize="lg">
                                    {booking.start_time} - {booking.end_time}
                                  </Text>
                                </VStack>

                                <Text fontSize="sm" color="gray.500">
                                  Session completed
                                </Text>
                              </VStack>
                            </CardBody>
                          </Card>
                        ))}
                      </SimpleGrid>
                    )}
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </VStack>
          )}
        </VStack>
      </Container>

      {/* Scroll to Top Button */}
      <Fade in={showScrollTop}>
        <IconButton
          icon={<ChevronUpIcon />}
          aria-label="Scroll to top"
          position="fixed"
          bottom={{ base: "20px", md: "30px" }}
          right={{ base: "20px", md: "30px" }}
          size={{ base: "md", md: "lg" }}
          colorScheme="blue"
          borderRadius="full"
          boxShadow="lg"
          zIndex={1000}
          onClick={scrollToTop}
          _hover={{
            transform: 'translateY(-2px)',
            boxShadow: 'xl'
          }}
          transition="all 0.2s"
          display={{ base: showScrollTop ? "flex" : "none", md: "flex" }}
        />
      </Fade>
    </Box>
  );
};

export default BookingPage;
