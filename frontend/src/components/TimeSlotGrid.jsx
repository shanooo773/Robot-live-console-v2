import {
  Box,
  SimpleGrid,
  Button,
  Text,
  VStack,
  HStack,
  Badge,
  Tooltip,
  useColorModeValue
} from '@chakra-ui/react';
import { useState, useMemo } from 'react';

const TimeSlotGrid = ({ 
  selectedDate, 
  selectedRobot, 
  availableSlots, 
  bookedSlots, 
  onSlotSelect, 
  isLoading,
  availableRobots 
}) => {
  const [hoveredSlot, setHoveredSlot] = useState(null);

  // Generate all possible time slots (9 AM to 6 PM, 1-hour slots)
  const allPossibleSlots = useMemo(() => {
    const slots = [];
    for (let hour = 9; hour < 18; hour++) {
      const startTime = `${hour.toString().padStart(2, '0')}:00`;
      const endTime = `${(hour + 1).toString().padStart(2, '0')}:00`;
      slots.push({
        id: `${selectedDate}-${startTime}-${selectedRobot}`,
        startTime,
        endTime,
        hour
      });
    }
    return slots;
  }, [selectedDate, selectedRobot]);

  // Determine slot status
  const getSlotStatus = (slot) => {
    if (!selectedDate || !selectedRobot) {
      return { status: 'disabled', reason: 'Select robot and date first' };
    }

    // Check if slot is available
    const isAvailable = availableSlots.some(available => 
      available.startTime === slot.startTime && 
      available.endTime === slot.endTime &&
      available.date === selectedDate &&
      available.robotType === selectedRobot
    );

    if (isAvailable) {
      return { status: 'available', reason: 'Available for booking' };
    }

    // Check if slot is booked
    const booking = bookedSlots.find(booked => 
      booked.start_time === slot.startTime && 
      booked.end_time === slot.endTime &&
      booked.date === selectedDate &&
      booked.robot_type === selectedRobot
    );

    if (booking) {
      return { 
        status: 'booked', 
        reason: `Booked by ${booking.user_name || 'Another user'}`,
        booking 
      };
    }

    // Check if slot is in the past
    const now = new Date();
    const slotDateTime = new Date(`${selectedDate}T${slot.startTime}`);
    if (slotDateTime < now) {
      return { status: 'past', reason: 'Time slot has passed' };
    }

    return { status: 'unavailable', reason: 'Not available for booking' };
  };

  const getSlotColors = (status) => {
    switch (status) {
      case 'available':
        return {
          bg: 'green.700',
          borderColor: 'green.500',
          color: 'green.100',
          _hover: { bg: 'green.600', borderColor: 'green.400' }
        };
      case 'booked':
        return {
          bg: 'red.900',
          borderColor: 'red.700',
          color: 'red.200',
          cursor: 'not-allowed',
          opacity: 0.8
        };
      case 'past':
        return {
          bg: 'gray.800',
          borderColor: 'gray.600',
          color: 'gray.500',
          cursor: 'not-allowed',
          opacity: 0.6
        };
      case 'disabled':
      case 'unavailable':
      default:
        return {
          bg: 'gray.800',
          borderColor: 'gray.600',
          color: 'gray.500',
          cursor: 'not-allowed',
          opacity: 0.7
        };
    }
  };

  const formatTime12Hour = (time24) => {
    const [hours, minutes] = time24.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${hour12}:${minutes} ${ampm}`;
  };

  if (!selectedDate || !selectedRobot) {
    return (
      <Box 
        p={8} 
        textAlign="center" 
        bg="gray.800" 
        borderRadius="md" 
        border="2px dashed" 
        borderColor="gray.600"
      >
        <Text color="gray.400" fontSize="lg">
          Select a robot and date to view available time slots
        </Text>
      </Box>
    );
  }

  return (
    <VStack spacing={4} align="stretch">
      <HStack justify="space-between" align="center">
        <VStack align="start" spacing={1}>
          <Text fontSize="lg" fontWeight="bold" color="white">
            Time Slots for {new Date(selectedDate).toLocaleDateString('en-US', { 
              weekday: 'long', 
              month: 'long', 
              day: 'numeric',
              year: 'numeric'
            })}
          </Text>
          <HStack>
            <Text fontSize="xl">{availableRobots[selectedRobot]?.emoji || "🤖"}</Text>
            <Text color="gray.300">
              {availableRobots[selectedRobot]?.name || selectedRobot}
            </Text>
          </HStack>
        </VStack>
        
        <HStack spacing={4}>
          <HStack spacing={2}>
            <Box w={3} h={3} bg="green.500" borderRadius="sm" />
            <Text fontSize="sm" color="gray.300">Available</Text>
          </HStack>
          <HStack spacing={2}>
            <Box w={3} h={3} bg="red.500" borderRadius="sm" />
            <Text fontSize="sm" color="gray.300">Booked</Text>
          </HStack>
          <HStack spacing={2}>
            <Box w={3} h={3} bg="gray.500" borderRadius="sm" />
            <Text fontSize="sm" color="gray.300">Unavailable</Text>
          </HStack>
        </HStack>
      </HStack>

      <SimpleGrid columns={{ base: 2, md: 3, lg: 4, xl: 5 }} spacing={3}>
        {allPossibleSlots.map((slot) => {
          const slotInfo = getSlotStatus(slot);
          const colors = getSlotColors(slotInfo.status);
          const isClickable = slotInfo.status === 'available';

          return (
            <Tooltip
              key={slot.id}
              label={slotInfo.reason}
              placement="top"
              hasArrow
            >
              <Button
                variant="outline"
                size="lg"
                h="auto"
                py={4}
                px={3}
                border="2px solid"
                borderRadius="lg"
                transition="all 0.2s"
                isDisabled={!isClickable || isLoading}
                isLoading={isLoading && hoveredSlot === slot.id}
                loadingText="Booking..."
                onClick={() => {
                  if (isClickable) {
                    const availableSlot = availableSlots.find(available => 
                      available.startTime === slot.startTime && 
                      available.endTime === slot.endTime &&
                      available.date === selectedDate &&
                      available.robotType === selectedRobot
                    );
                    if (availableSlot) {
                      setHoveredSlot(slot.id);
                      onSlotSelect(availableSlot);
                    }
                  }
                }}
                onMouseEnter={() => setHoveredSlot(slot.id)}
                onMouseLeave={() => setHoveredSlot(null)}
                {...colors}
              >
                <VStack spacing={2}>
                  <Text fontWeight="bold" fontSize="md">
                    {formatTime12Hour(slot.startTime)}
                  </Text>
                  <Text fontSize="xs" opacity={0.8}>
                    to {formatTime12Hour(slot.endTime)}
                  </Text>
                  {slotInfo.status === 'available' && (
                    <Badge colorScheme="green" size="sm" fontSize="xs">
                      Available
                    </Badge>
                  )}
                  {slotInfo.status === 'booked' && (
                    <Badge colorScheme="red" size="sm" fontSize="xs">
                      Booked
                    </Badge>
                  )}
                  {slotInfo.status === 'past' && (
                    <Badge colorScheme="gray" size="sm" fontSize="xs">
                      Past
                    </Badge>
                  )}
                </VStack>
              </Button>
            </Tooltip>
          );
        })}
      </SimpleGrid>
    </VStack>
  );
};

export default TimeSlotGrid;