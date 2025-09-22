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
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { createBooking, getUserBookings, getBookingSchedule, getActiveAnnouncements, getAvailableSlots } from "../api";
import ServiceStatus from "./ServiceStatus";

// Generate realistic time slots based on business rules
const generateAvailableTimeSlots = async (authToken, selectedDate, selectedRobot) => {
  if (!authToken || !selectedDate || !selectedRobot) {
    return [];
  }
  
  try {
    const response = await getAvailableSlots(selectedDate, selectedRobot, authToken);
    return response.available_slots.map((slot, index) => ({
      id: `slot_${selectedDate}_${slot.start_time}_${selectedRobot}`,
      date: slot.date,
      startTime: slot.start_time,
      endTime: slot.end_time,
      robotType: slot.robot_type,
      available: true,
      bookedBy: null,
      duration: slot.duration_hours
    }));
  } catch (error) {
    console.error('Error fetching available slots:', error);
    return [];
  }
};

// Fallback dummy data for demo mode or when API is unavailable
const generateFallbackTimeSlots = () => {
  const slots = [];
  const today = new Date();
  
  for (let day = 0; day < 7; day++) {
    const date = new Date(today);
    date.setDate(today.getDate() + day);
    
    // Generate slots from 9 AM to 6 PM (working hours)
    for (let hour = 9; hour < 18; hour++) {
      const startTime = new Date(date);
      startTime.setHours(hour, 0, 0, 0);
      
      const endTime = new Date(startTime);
      endTime.setHours(hour + 1, 0, 0, 0);
      
      // Skip past time slots for today
      if (date.toDateString() === today.toDateString() && startTime <= new Date()) {
        continue;
      }
      
      // Randomly mark some slots as taken to simulate real usage
      const isTaken = Math.random() < 0.2; // Reduced probability for better demo experience
      
      slots.push({
        id: `slot_${day}_${hour}`,
        date: date.toISOString().split('T')[0],
        startTime: startTime.toLocaleTimeString('en-GB', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        }),
        endTime: endTime.toLocaleTimeString('en-GB', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        }),
        available: !isTaken,
        robotType: ["turtlebot", "arm", "hand"][Math.floor(Math.random() * 3)],
        bookedBy: isTaken ? "Another User" : null,
      });
    }
  }
  
  return slots;
};

const robotNames = {
  turtlebot: { name: "TurtleBot3 Navigation", emoji: "🤖" },
  arm: { name: "Robot Arm Manipulation", emoji: "🦾" },
  hand: { name: "Dexterous Hand Control", emoji: "🤲" },
};

const BookingPage = ({ user, authToken, onBooking, onLogout, onAdminAccess }) => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [bookedSlots, setBookedSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedRobot, setSelectedRobot] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [userBookings, setUserBookings] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const toast = useToast();

  useEffect(() => {
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);
    
    // Load user bookings, booked slots, and announcements
    loadBookings();
    loadAnnouncements();
  }, [authToken]);

  // Load available slots when date or robot selection changes
  useEffect(() => {
    loadAvailableSlots();
  }, [selectedDate, selectedRobot, authToken]);

  const loadAvailableSlots = async () => {
    try {
      if (authToken && selectedDate && selectedRobot) {
        // Load real available slots from API
        const slots = await generateAvailableTimeSlots(authToken, selectedDate, selectedRobot);
        setTimeSlots(slots);
      } else if (user?.isDemoMode) {
        // Demo mode - use fallback data
        const slots = generateFallbackTimeSlots();
        setTimeSlots(slots);
      } else {
        // No auth or incomplete selection - show empty or fallback slots
        const slots = generateFallbackTimeSlots();
        setTimeSlots(slots);
      }
    } catch (error) {
      console.error('Error loading available slots:', error);
      // Fallback to dummy data on error
      const fallbackSlots = generateFallbackTimeSlots();
      setTimeSlots(fallbackSlots);
    }
  };

  const loadBookings = async () => {
    try {
      if (authToken) {
        // Regular authenticated mode
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
      } else if (user?.isDemoMode) {
        // Demo mode - create dummy data
        const dummyBookings = [
          {
            id: 1,
            robot_type: "turtlebot",
            date: new Date().toISOString().split('T')[0],
            start_time: "10:00",
            end_time: "11:00",
            status: "completed"
          }
        ];
        setUserBookings(dummyBookings);
        setBookedSlots([]);
      }
    } catch (error) {
      console.error('Error loading bookings:', error);
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
  const filteredSlots = timeSlots.filter((slot) => {
    let matches = true;
    if (selectedDate && slot.date !== selectedDate) matches = false;
    if (selectedRobot && slot.robotType !== selectedRobot) matches = false;

    const slotStart24 = ensureTwentyFourHourFormat(slot.startTime);
    const slotEnd24 = ensureTwentyFourHourFormat(slot.endTime);

    const isBooked = bookedSlots.some((booked) => {
      const bookedStart24 = ensureTwentyFourHourFormat(booked.start_time);
      const bookedEnd24 = ensureTwentyFourHourFormat(booked.end_time);

      return (
        booked.date === slot.date &&
        bookedStart24 === slotStart24 &&
        bookedEnd24 === slotEnd24 &&
        booked.robot_type === slot.robotType
      );
    });

    slot.available = !isBooked;
    if (isBooked) {
      const booking = bookedSlots.find((booked) => {
        const bookedStart24 = ensureTwentyFourHourFormat(booked.start_time);
        const bookedEnd24 = ensureTwentyFourHourFormat(booked.end_time);
        return (
          booked.date === slot.date &&
          bookedStart24 === slotStart24 &&
          bookedEnd24 === slotEnd24 &&
          booked.robot_type === slot.robotType
        );
      });
      slot.bookedBy = booking?.user_name || "Another User";
    }

    return matches;
  });

  const availableSlots = filteredSlots.filter((slot) => slot.available);
  const unavailableSlots = filteredSlots.filter((slot) => !slot.available);

  const handleBookSlot = async (slot) => {
    // Enforce authentication requirement
    if (!authToken && !user?.isDemoMode) {
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
      if (authToken) {
        // Regular authenticated booking with enhanced validation
        const bookingData = {
          robot_type: slot.robotType,
          date: slot.date,
          start_time: ensureTwentyFourHourFormat(slot.startTime),
          end_time: ensureTwentyFourHourFormat(slot.endTime)
        };
        
        // Client-side validation
        const startHour = parseInt(slot.startTime.split(':')[0]);
        const endHour = parseInt(slot.endTime.split(':')[0]);
        
        if (startHour < 9 || startHour >= 18) {
          throw new Error("Bookings are only allowed during working hours (9:00 AM - 6:00 PM)");
        }
        
        if (endHour > 18) {
          throw new Error("Booking sessions cannot extend beyond 6:00 PM");
        }
        
        const duration = endHour - startHour;
        if (duration > 2) {
          throw new Error("Maximum booking duration is 2 hours");
        }
        
        if (duration < 1) {
          throw new Error("Minimum booking duration is 1 hour");
        }
        
        const booking = await createBooking(bookingData, authToken);
        
        // Update local state by reloading available slots
        await loadBookings();
        await loadAvailableSlots();
        
        onBooking({
          ...slot,
          bookingId: booking.id,
          available: false,
          bookedBy: user.name,
          bookingTime: booking.created_at,
        });
      } else if (user?.isDemoMode) {
        // Demo mode - create dummy booking
        const demoBooking = {
          id: Math.random().toString(36).substr(2, 9),
          robot_type: slot.robotType,
          date: slot.date,
          start_time: ensureTwentyFourHourFormat(slot.startTime),
          end_time: ensureTwentyFourHourFormat(slot.endTime),
          status: "completed",
          created_at: new Date().toISOString()
        };
        
        onBooking({
          ...slot,
          bookingId: demoBooking.id,
          available: false,
          bookedBy: user.name,
          bookingTime: demoBooking.created_at,
        });
      }
      
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

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8}>
        {/* Header */}
        <HStack w="full" justify="space-between">
          <VStack align="start" spacing={1}>
            <Text fontSize="3xl" fontWeight="bold" color="white">
              Book Development Console Session
            </Text>
            <HStack>
              <Avatar size="sm" name={user.name} />
              <Text color="gray.300">Welcome, {user.name}</Text>
              {user.role === 'admin' && (
                <Badge colorScheme="purple" ml={2}>Admin</Badge>
              )}
              {(user?.isDemoUser || user?.isDemoAdmin || localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin')) && (
                <Badge colorScheme="orange" ml={2}>DEMO MODE</Badge>
              )}
            </HStack>
          </VStack>
          <HStack spacing={3}>
            {onAdminAccess && user.role === 'admin' && (
              <Button colorScheme="purple" onClick={onAdminAccess}>
                Admin Dashboard
              </Button>
            )}
            <Button variant="ghost" onClick={onLogout} color="gray.400">
              Logout
            </Button>
          </HStack>
        </HStack>

        {/* Service Status */}
        <Box w="full">
          <ServiceStatus showDetails={false} />
        </Box>

        {/* Booking Rules Information */}
        <Card w="full" bg="blue.900" border="1px solid" borderColor="blue.500">
          <CardBody>
            <VStack align="start" spacing={3}>
              <Text fontSize="lg" fontWeight="bold" color="blue.100">
                📋 Booking Guidelines
              </Text>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} w="full">
                <VStack align="start" spacing={2}>
                  <Text color="blue.200" fontWeight="semibold">Working Hours</Text>
                  <Text color="blue.300" fontSize="sm">9:00 AM - 6:00 PM</Text>
                  <Text color="blue.200" fontWeight="semibold">Session Duration</Text>
                  <Text color="blue.300" fontSize="sm">30 minutes - 2 hours maximum</Text>
                </VStack>
                <VStack align="start" spacing={2}>
                  <Text color="blue.200" fontWeight="semibold">Authentication</Text>
                  <Text color="blue.300" fontSize="sm">Login required for booking</Text>
                  <Text color="blue.200" fontWeight="semibold">Availability</Text>
                  <Text color="blue.300" fontSize="sm">Real-time slot availability</Text>
                </VStack>
              </SimpleGrid>
            </VStack>
          </CardBody>
        </Card>

        {/* Active Announcements */}
        {announcements.length > 0 && (
          <VStack spacing={4} w="full">
            {announcements.map((announcement) => (
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

        {/* Demo User Direct Access */}
        {(user?.isDemoUser || user?.isDemoAdmin || localStorage.getItem('isDemoUser') || localStorage.getItem('isDemoAdmin')) && (
          <Card w="full" bg="orange.900" border="2px solid" borderColor="orange.500">
            <CardHeader>
              <HStack justify="space-between" align="center">
                <VStack align="start" spacing={1}>
                  <Text fontSize="lg" fontWeight="bold" color="orange.100">
                    🎯 Demo Mode - Unrestricted Access
                  </Text>
                  <Text color="orange.200" fontSize="sm">
                    Skip bookings and access the development console directly
                  </Text>
                </VStack>
                <Button
                  colorScheme="orange"
                  size="lg"
                  onClick={() => onBooking({
                    id: 'demo_direct_access',
                    robotType: 'turtlebot',
                    date: new Date().toISOString().split('T')[0],
                    startTime: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }),
                    endTime: 'Unlimited',
                    bookingId: 'demo',
                    available: true,
                    bookedBy: user.name,
                    isDemoAccess: true
                  })}
                >
                  Enter Development Console
                </Button>
              </HStack>
            </CardHeader>
          </Card>
        )}

        {/* Filters */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <Text fontSize="lg" fontWeight="bold" color="white">
              Choose Development Environment
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
                >
                  <option value="">All dates</option>
                  {getDateOptions().map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel color="gray.300">Development Environment</FormLabel>
                <Select
                  value={selectedRobot}
                  onChange={(e) => setSelectedRobot(e.target.value)}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                >
                  <option value="">All environments</option>
                  <option value="turtlebot">🤖 TurtleBot3 Navigation</option>
                  <option value="arm">🦾 Robot Arm Manipulation</option>
                  <option value="hand">🤲 Dexterous Hand Control</option>
                </Select>
              </FormControl>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Available Slots */}
        <VStack w="full" spacing={6}>
          <HStack w="full" justify="space-between">
            <Text fontSize="xl" fontWeight="bold" color="white">
              Available Development Sessions ({availableSlots.length})
            </Text>
            <Badge colorScheme="green" px={3} py={1}>
              {availableSlots.length} console slots free
            </Badge>
          </HStack>

          {availableSlots.length === 0 ? (
            <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
              <CardBody textAlign="center" py={12}>
                <Text fontSize="xl" color="gray.400" mb={2}>
                  No development sessions available
                </Text>
                <Text color="gray.500">
                  Try adjusting your filters or check back later
                </Text>
              </CardBody>
            </Card>
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} w="full">
              {availableSlots.map((slot) => (
                <Card
                  key={slot.id}
                  bg="gray.800"
                  border="1px solid"
                  borderColor="gray.600"
                  _hover={{ borderColor: "green.400", transform: "translateY(-2px)" }}
                  transition="all 0.2s"
                >
                  <CardBody>
                    <VStack spacing={3} align="start">
                      <HStack justify="space-between" w="full">
                        <Badge colorScheme="green">Available</Badge>
                        <HStack>
                          <Text fontSize="xl">{robotNames[slot.robotType].emoji}</Text>
                          <Text fontSize="sm" color="gray.300">
                            {robotNames[slot.robotType].name}
                          </Text>
                        </HStack>
                      </HStack>
                      
                      <VStack align="start" spacing={1}>
                        <Text color="white" fontWeight="bold">
                          {new Date(slot.date).toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            month: 'long', 
                            day: 'numeric' 
                          })}
                        </Text>
                        <Text color="gray.300" fontSize="lg">
                          {slot.startTime} - {slot.endTime}
                        </Text>
                      </VStack>

                      <Button
                        colorScheme="green"
                        w="full"
                        onClick={() => handleBookSlot(slot)}
                        isLoading={isLoading}
                        loadingText="Booking..."
                      >
                        Access Development Console
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          )}
        </VStack>

        {/* User's Current Bookings */}
        {userBookings.length > 0 && (
          <VStack w="full" spacing={6}>
            <Divider borderColor="gray.600" />
            
            <HStack w="full" justify="space-between">
              <Text fontSize="xl" fontWeight="bold" color="white">
                Your Booked Sessions
              </Text>
              <Badge colorScheme="green" px={3} py={1}>
                {userBookings.length} active booking{userBookings.length !== 1 ? 's' : ''}
              </Badge>
            </HStack>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} w="full">
              {userBookings.map((booking) => (
                <Card
                  key={booking.id}
                  bg="green.900"
                  border="1px solid"
                  borderColor="green.600"
                >
                  <CardBody>
                    <VStack spacing={3} align="start">
                      <HStack justify="space-between" w="full">
                        <Badge colorScheme="green">Your Booking</Badge>
                        <HStack>
                          <Text fontSize="xl">{robotNames[booking.robot_type].emoji}</Text>
                          <Text fontSize="sm" color="green.100">
                            {robotNames[booking.robot_type].name}
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

                      <Button
                        colorScheme="green"
                        size="sm"
                        w="full"
                        onClick={() => onBooking({
                          id: `booking_${booking.id}`,
                          robotType: booking.robot_type,
                          date: booking.date,
                          startTime: booking.start_time,
                          endTime: booking.end_time,
                          bookingId: booking.id,
                          available: false,
                          bookedBy: user.name
                        })}
                      >
                        Enter Development Console
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </VStack>
        )}

        {/* Booked Slots (for reference) */}
        {unavailableSlots.length > 0 && (
          <VStack w="full" spacing={6}>
            <Divider borderColor="gray.600" />
            
            <HStack w="full" justify="space-between">
              <Text fontSize="xl" fontWeight="bold" color="white">
                Unavailable Sessions
              </Text>
              <Badge colorScheme="red" px={3} py={1}>
                {unavailableSlots.length} slots taken
              </Badge>
            </HStack>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4} w="full">
              {unavailableSlots.slice(0, 6).map((slot) => (
                <Card
                  key={slot.id}
                  bg="gray.900"
                  border="1px solid"
                  borderColor="gray.700"
                  opacity={0.7}
                >
                  <CardBody>
                    <VStack spacing={3} align="start">
                      <HStack justify="space-between" w="full">
                        <Badge colorScheme="red">Taken</Badge>
                        <HStack>
                          <Text fontSize="xl">{robotNames[slot.robotType].emoji}</Text>
                          <Text fontSize="sm" color="gray.400">
                            {robotNames[slot.robotType].name}
                          </Text>
                        </HStack>
                      </HStack>
                      
                      <VStack align="start" spacing={1}>
                        <Text color="gray.300">
                          {new Date(slot.date).toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            month: 'long', 
                            day: 'numeric' 
                          })}
                        </Text>
                        <Text color="gray.400">
                          {slot.startTime} - {slot.endTime}
                        </Text>
                      </VStack>

                      <Text fontSize="sm" color="gray.500">
                        Booked by {slot.bookedBy}
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </VStack>
        )}
      </VStack>
    </Container>
  );
};

export default BookingPage;
