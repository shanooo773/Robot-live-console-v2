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
import { createBooking, getUserBookings, getBookingSchedule, getActiveAnnouncements } from "../api";
import ServiceStatus from "./ServiceStatus";

// Dummy data for available time slots
const generateTimeSlots = () => {
  const slots = [];
  const today = new Date();
  
  for (let day = 0; day < 7; day++) {
    const date = new Date(today);
    date.setDate(today.getDate() + day);
    
    // Generate slots from 9 AM to 9 PM
    for (let hour = 9; hour <= 21; hour++) {
      const startTime = new Date(date);
      startTime.setHours(hour, 0, 0, 0);
      
      const endTime = new Date(startTime);
      endTime.setHours(hour + 1, 0, 0, 0);
      
      // Randomly mark some slots as taken to simulate real usage
      const isTaken = Math.random() < 0.3;
      
      slots.push({
        id: `slot_${day}_${hour}`,
        date: date.toISOString().split('T')[0],
        startTime: startTime.toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit',
          hour12: true 
        }),
        endTime: endTime.toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit',
          hour12: true 
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
    // Generate dummy time slots on component mount
    const slots = generateTimeSlots();
    setTimeSlots(slots);
    
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);
    
    // Load user bookings, booked slots, and announcements
    loadBookings();
    loadAnnouncements();
  }, [authToken]);

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

  const filteredSlots = timeSlots.filter(slot => {
    let matches = true;
    if (selectedDate && slot.date !== selectedDate) matches = false;
    if (selectedRobot && slot.robotType !== selectedRobot) matches = false;
    
    // Check if slot is already booked
    const isBooked = bookedSlots.some(booked => 
      booked.date === slot.date &&
      booked.start_time === slot.startTime &&
      booked.end_time === slot.endTime &&
      booked.robot_type === slot.robotType
    );
    
    slot.available = !isBooked;
    if (isBooked) {
      const booking = bookedSlots.find(booked => 
        booked.date === slot.date &&
        booked.start_time === slot.startTime &&
        booked.end_time === slot.endTime &&
        booked.robot_type === slot.robotType
      );
      slot.bookedBy = booking.user_name;
    }
    
    return matches;
  });

  const availableSlots = filteredSlots.filter(slot => slot.available);
  const unavailableSlots = filteredSlots.filter(slot => !slot.available);

  const handleBookSlot = async (slot) => {
    setIsLoading(true);
    
    try {
      if (authToken) {
        // Regular authenticated booking
        const bookingData = {
          robot_type: slot.robotType,
          date: slot.date,
          start_time: slot.startTime,
          end_time: slot.endTime
        };
        
        const booking = await createBooking(bookingData, authToken);
        
        // Update local state
        await loadBookings();
        
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
          start_time: slot.startTime,
          end_time: slot.endTime,
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
        description: `Your coding console is reserved for ${slot.date} at ${slot.startTime}`,
        status: "success",
        duration: 5000,
        isClosable: true,
      });
      
    } catch (error) {
      console.error('Booking error:', error);
      toast({
        title: "Booking failed",
        description: error.response?.data?.detail || "Failed to book session. Please try again.",
        status: "error",
        duration: 5000,
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
                    startTime: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }),
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