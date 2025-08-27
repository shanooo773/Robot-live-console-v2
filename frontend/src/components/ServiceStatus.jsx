import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Tooltip,
  IconButton,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Collapse,
  useDisclosure,
  Button,
} from '@chakra-ui/react';
import { FiRefreshCw, FiInfo, FiChevronDown, FiChevronUp } from 'react-icons/fi';
import { getSystemHealth, getServiceStatus, getAvailableFeatures } from '../api';

const ServiceStatusComponent = ({ showDetails = false, onStatusChange }) => {
  const [health, setHealth] = useState(null);
  const [services, setServices] = useState(null);
  const [features, setFeatures] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isOpen, onToggle } = useDisclosure();
  
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [healthData, servicesData, featuresData] = await Promise.all([
        getSystemHealth(),
        getServiceStatus(),
        getAvailableFeatures()
      ]);
      
      setHealth(healthData);
      setServices(servicesData);
      setFeatures(featuresData);
      
      // Notify parent component of status changes
      if (onStatusChange) {
        onStatusChange({
          health: healthData,
          services: servicesData,
          features: featuresData
        });
      }
    } catch (err) {
      setError('Failed to fetch service status');
      console.error('Service status error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational': return 'green';
      case 'limited': return 'yellow';
      case 'degraded': return 'orange';
      case 'unavailable': return 'red';
      default: return 'gray';
    }
  };

  const getServiceIcon = (service) => {
    if (service.available) {
      return <Badge colorScheme="green" size="sm">Online</Badge>;
    } else {
      return <Badge colorScheme="red" size="sm">Offline</Badge>;
    }
  };

  const getStatusMessage = () => {
    if (!health) return null;
    
    switch (health.status) {
      case 'operational':
        return {
          type: 'success',
          title: 'All Systems Operational',
          description: 'All services including robot simulation are available.'
        };
      case 'limited':
        return {
          type: 'warning',
          title: 'Limited Functionality',
          description: 'Core services (login, booking) are available. Robot simulation may be limited.'
        };
      case 'degraded':
        return {
          type: 'error',
          title: 'Degraded Performance',
          description: 'Some services are experiencing issues. Core functionality may be affected.'
        };
      default:
        return {
          type: 'info',
          title: 'System Status Unknown',
          description: 'Unable to determine system status.'
        };
    }
  };

  if (loading && !health) {
    return (
      <Box p={2}>
        <Text fontSize="sm" color="gray.500">Loading system status...</Text>
      </Box>
    );
  }

  if (error && !health) {
    return (
      <Alert status="warning" size="sm">
        <AlertIcon />
        <Text fontSize="sm">Cannot connect to backend services</Text>
      </Alert>
    );
  }

  const statusMessage = getStatusMessage();

  return (
    <Box>
      {/* Compact Status Bar */}
      <HStack 
        p={2} 
        bg={bgColor} 
        borderRadius="md" 
        borderWidth={1} 
        borderColor={borderColor}
        spacing={3}
      >
        <HStack spacing={2}>
          <Badge 
            colorScheme={getStatusColor(health?.status)} 
            variant="solid"
            fontSize="xs"
          >
            {health?.status?.toUpperCase() || 'UNKNOWN'}
          </Badge>
          
          {health?.core_services && (
            <Badge colorScheme="blue" variant="outline" fontSize="xs">
              Core Services Online
            </Badge>
          )}
          
          {services?.services?.docker && !services.services.docker.available && (
            <Badge colorScheme="orange" variant="outline" fontSize="xs">
              Simulation Limited
            </Badge>
          )}
        </HStack>

        <HStack spacing={1} ml="auto">
          <Tooltip label="Refresh status">
            <IconButton
              icon={<FiRefreshCw />}
              size="xs"
              variant="ghost"
              onClick={fetchStatus}
              isLoading={loading}
            />
          </Tooltip>
          
          {showDetails && (
            <IconButton
              icon={isOpen ? <FiChevronUp /> : <FiChevronDown />}
              size="xs"
              variant="ghost"
              onClick={onToggle}
            />
          )}
        </HStack>
      </HStack>

      {/* Detailed Status (Collapsible) */}
      {showDetails && (
        <Collapse in={isOpen}>
          <Box mt={3} p={4} bg={bgColor} borderRadius="md" borderWidth={1} borderColor={borderColor}>
            <VStack spacing={4} align="stretch">
              {/* Status Alert */}
              {statusMessage && (
                <Alert status={statusMessage.type} size="sm">
                  <AlertIcon />
                  <Box>
                    <AlertTitle fontSize="sm">{statusMessage.title}</AlertTitle>
                    <AlertDescription fontSize="xs">
                      {statusMessage.description}
                    </AlertDescription>
                  </Box>
                </Alert>
              )}

              {/* Services Status */}
              <Box>
                <Text fontSize="sm" fontWeight="semibold" mb={2}>Service Status</Text>
                <VStack spacing={2} align="stretch">
                  {services?.services && Object.entries(services.services).map(([name, service]) => (
                    <HStack key={name} justify="space-between">
                      <HStack>
                        <Text fontSize="sm" textTransform="capitalize">{name}</Text>
                        {service.error && (
                          <Tooltip label={service.error}>
                            <Box><FiInfo size={12} color="orange" /></Box>
                          </Tooltip>
                        )}
                      </HStack>
                      {getServiceIcon(service)}
                    </HStack>
                  ))}
                </VStack>
              </Box>

              {/* Feature Availability */}
              <Box>
                <Text fontSize="sm" fontWeight="semibold" mb={2}>Available Features</Text>
                <VStack spacing={1} align="stretch">
                  {features?.always_available?.length > 0 && (
                    <HStack>
                      <Badge colorScheme="green" size="sm">{features.always_available.length}</Badge>
                      <Text fontSize="xs">Always available features</Text>
                    </HStack>
                  )}
                  {features?.conditionally_available?.length > 0 && (
                    <HStack>
                      <Badge colorScheme="yellow" size="sm">{features.conditionally_available.length}</Badge>
                      <Text fontSize="xs">Limited features</Text>
                    </HStack>
                  )}
                  {features?.unavailable?.length > 0 && (
                    <HStack>
                      <Badge colorScheme="red" size="sm">{features.unavailable.length}</Badge>
                      <Text fontSize="xs">Unavailable features</Text>
                    </HStack>
                  )}
                </VStack>
              </Box>
            </VStack>
          </Box>
        </Collapse>
      )}
    </Box>
  );
};

export default ServiceStatusComponent;