import { useState, useEffect } from 'react';
import { Text, Badge, HStack, VStack } from '@chakra-ui/react';

const CountdownTimer = ({ targetDate, targetTime, onExpired }) => {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0
  });
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const calculateTimeLeft = () => {
      // Create target datetime
      const target = new Date(`${targetDate}T${targetTime}`);
      const now = new Date();
      const difference = target.getTime() - now.getTime();

      if (difference <= 0) {
        if (!isExpired) {
          setIsExpired(true);
          if (onExpired) onExpired();
        }
        return { days: 0, hours: 0, minutes: 0, seconds: 0 };
      }

      return {
        days: Math.floor(difference / (1000 * 60 * 60 * 24)),
        hours: Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((difference % (1000 * 60)) / 1000)
      };
    };

    // Update immediately
    setTimeLeft(calculateTimeLeft());

    // Set up interval to update every second
    const timer = setInterval(() => {
      setTimeLeft(calculateTimeLeft());
    }, 1000);

    return () => clearInterval(timer);
  }, [targetDate, targetTime, isExpired, onExpired]);

  if (isExpired) {
    return (
      <Badge colorScheme="red" fontSize="sm">
        Session Started
      </Badge>
    );
  }

  const formatTimeUnit = (value, unit) => {
    if (value === 0) return null;
    return `${value}${unit}`;
  };

  const timeComponents = [
    formatTimeUnit(timeLeft.days, 'd'),
    formatTimeUnit(timeLeft.hours, 'h'),
    formatTimeUnit(timeLeft.minutes, 'm'),
    formatTimeUnit(timeLeft.seconds, 's')
  ].filter(Boolean);

  if (timeComponents.length === 0) {
    return (
      <Badge colorScheme="red" fontSize="sm">
        Starting Now
      </Badge>
    );
  }

  // Show different styles based on time remaining
  const totalMinutes = timeLeft.days * 24 * 60 + timeLeft.hours * 60 + timeLeft.minutes;
  let colorScheme = 'green';
  if (totalMinutes < 30) colorScheme = 'red';
  else if (totalMinutes < 120) colorScheme = 'orange';

  return (
    <VStack spacing={1} align="start">
      <Text fontSize="xs" color="gray.400">Starts in:</Text>
      <Badge colorScheme={colorScheme} fontSize="sm">
        {timeComponents.join(' ')}
      </Badge>
    </VStack>
  );
};

export default CountdownTimer;