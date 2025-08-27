import { useState, useEffect } from "react";
import { 
  Box, 
  Text, 
  VStack, 
  HStack, 
  Badge, 
  Progress, 
  Grid, 
  GridItem,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText
} from "@chakra-ui/react";

const LiveResults = ({ robot }) => {
  const [liveData, setLiveData] = useState({
    position: { x: 0, y: 0, z: 0 },
    velocity: { x: 0, y: 0, z: 0 },
    joint_angles: { joint1: 0, joint2: 0, joint3: 0 },
    battery: 85,
    temperature: 42,
    status: "READY",
    lastUpdate: new Date()
  });

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveData(prev => ({
        position: {
          x: prev.position.x + (Math.random() - 0.5) * 0.1,
          y: prev.position.y + (Math.random() - 0.5) * 0.1,
          z: prev.position.z + (Math.random() - 0.5) * 0.05
        },
        velocity: {
          x: (Math.random() - 0.5) * 0.5,
          y: (Math.random() - 0.5) * 0.5,
          z: (Math.random() - 0.5) * 0.2
        },
        joint_angles: {
          joint1: prev.joint_angles.joint1 + (Math.random() - 0.5) * 5,
          joint2: prev.joint_angles.joint2 + (Math.random() - 0.5) * 5,
          joint3: prev.joint_angles.joint3 + (Math.random() - 0.5) * 5
        },
        battery: Math.max(20, prev.battery - 0.01),
        temperature: 40 + Math.random() * 10,
        status: Math.random() > 0.1 ? "ACTIVE" : "READY",
        lastUpdate: new Date()
      }));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const robotEmojis = {
    turtlebot: "🤖",
    arm: "🦾", 
    hand: "🤲"
  };

  return (
    <Box w="100%" h="100%" bg="#1a1a1a" border="1px solid #333" borderRadius="md" p={4}>
      <VStack spacing={4} align="stretch" h="100%">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <HStack>
            <Text fontSize="lg" fontWeight="bold" color="white">
              {robotEmojis[robot]} Live Data
            </Text>
            <Badge colorScheme={liveData.status === "ACTIVE" ? "green" : "orange"} size="sm">
              {liveData.status}
            </Badge>
          </HStack>
          <Text fontSize="xs" color="gray.400">
            {liveData.lastUpdate.toLocaleTimeString()}
          </Text>
        </HStack>

        {/* System Status */}
        <Grid templateColumns="repeat(2, 1fr)" gap={3}>
          <GridItem>
            <Card bg="#2a2a2a" border="1px solid #333">
              <CardBody p={3}>
                <Stat>
                  <StatLabel color="gray.300" fontSize="xs">Battery</StatLabel>
                  <StatNumber color="white" fontSize="md">{liveData.battery.toFixed(1)}%</StatNumber>
                  <Progress 
                    value={liveData.battery} 
                    size="sm" 
                    colorScheme={liveData.battery > 50 ? "green" : liveData.battery > 20 ? "yellow" : "red"}
                    mt={2}
                  />
                </Stat>
              </CardBody>
            </Card>
          </GridItem>
          <GridItem>
            <Card bg="#2a2a2a" border="1px solid #333">
              <CardBody p={3}>
                <Stat>
                  <StatLabel color="gray.300" fontSize="xs">Temperature</StatLabel>
                  <StatNumber color="white" fontSize="md">{liveData.temperature.toFixed(1)}°C</StatNumber>
                  <StatHelpText color="gray.400" fontSize="xs" mt={1}>Normal range</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </GridItem>
        </Grid>

        {/* Position Data */}
        <Card bg="#2a2a2a" border="1px solid #333">
          <CardBody p={3}>
            <Text color="white" fontSize="sm" fontWeight="bold" mb={2}>Position (m)</Text>
            <Grid templateColumns="repeat(3, 1fr)" gap={2}>
              <Box textAlign="center">
                <Text color="red.300" fontSize="xs">X</Text>
                <Text color="white" fontSize="sm">{liveData.position.x.toFixed(3)}</Text>
              </Box>
              <Box textAlign="center">
                <Text color="green.300" fontSize="xs">Y</Text>
                <Text color="white" fontSize="sm">{liveData.position.y.toFixed(3)}</Text>
              </Box>
              <Box textAlign="center">
                <Text color="blue.300" fontSize="xs">Z</Text>
                <Text color="white" fontSize="sm">{liveData.position.z.toFixed(3)}</Text>
              </Box>
            </Grid>
          </CardBody>
        </Card>

        {/* Velocity Data */}
        <Card bg="#2a2a2a" border="1px solid #333">
          <CardBody p={3}>
            <Text color="white" fontSize="sm" fontWeight="bold" mb={2}>Velocity (m/s)</Text>
            <Grid templateColumns="repeat(3, 1fr)" gap={2}>
              <Box textAlign="center">
                <Text color="red.300" fontSize="xs">X</Text>
                <Text color="white" fontSize="sm">{liveData.velocity.x.toFixed(3)}</Text>
              </Box>
              <Box textAlign="center">
                <Text color="green.300" fontSize="xs">Y</Text>
                <Text color="white" fontSize="sm">{liveData.velocity.y.toFixed(3)}</Text>
              </Box>
              <Box textAlign="center">
                <Text color="blue.300" fontSize="xs">Z</Text>
                <Text color="white" fontSize="sm">{liveData.velocity.z.toFixed(3)}</Text>
              </Box>
            </Grid>
          </CardBody>
        </Card>

        {/* Joint Angles (for arm/hand robots) */}
        {(robot === "arm" || robot === "hand") && (
          <Card bg="#2a2a2a" border="1px solid #333">
            <CardBody p={3}>
              <Text color="white" fontSize="sm" fontWeight="bold" mb={2}>Joint Angles (°)</Text>
              <Grid templateColumns="repeat(3, 1fr)" gap={2}>
                <Box textAlign="center">
                  <Text color="cyan.300" fontSize="xs">J1</Text>
                  <Text color="white" fontSize="sm">{liveData.joint_angles.joint1.toFixed(1)}</Text>
                </Box>
                <Box textAlign="center">
                  <Text color="cyan.300" fontSize="xs">J2</Text>
                  <Text color="white" fontSize="sm">{liveData.joint_angles.joint2.toFixed(1)}</Text>
                </Box>
                <Box textAlign="center">
                  <Text color="cyan.300" fontSize="xs">J3</Text>
                  <Text color="white" fontSize="sm">{liveData.joint_angles.joint3.toFixed(1)}</Text>
                </Box>
              </Grid>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
};

export default LiveResults;