import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Container,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Image,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Icon,
  Input,
  Textarea,
  FormControl,
  FormLabel,
  Flex,
  Avatar,
  Divider,
  Link,
} from "@chakra-ui/react";
import { 
  FaRobot, 
  FaBrain, 
  FaGraduationCap, 
  FaChartLine, 
  FaCogs, 
  FaLightbulb,
  FaShieldAlt,
  FaRocket,
  FaPhone,
  FaEnvelope,
  FaMapMarkerAlt,
  FaFacebook,
  FaTwitter,
  FaLinkedin,
  FaGithub,
  FaStar,
  FaArrowRight,
  FaPlay,
  FaQuoteLeft,
  FaUsers,
  FaAward,
  FaGlobe,
  FaHandshake
} from "react-icons/fa";
import { useState } from "react";
import { submitContactMessage } from "../api";
import { useToast } from "@chakra-ui/react";

const LandingPage = ({ onGetStarted }) => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    message: ""
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmitMessage = async () => {
    if (!formData.name || !formData.email || !formData.message) {
      toast({
        title: "Missing Information",
        description: "Please fill in all fields",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await submitContactMessage(formData);
      toast({
        title: "Message Sent!",
        description: "Thank you for contacting us. We'll get back to you soon.",
        status: "success",
        duration: 5000,
        isClosable: true,
      });
      setFormData({ name: "", email: "", message: "" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  return (
    <Box 
      minH="100vh"
      bg="white"
      color="gray.800"
      position="relative"
      overflow="hidden"
    >
      {/* Hero Section */}
<Box
  position="relative"
  minH="100vh"
  bgImage="url('/img/hero.jpg')"
  bgSize="cover"
  bgPosition="center"
  bgRepeat="no-repeat"
  overflow="hidden"
>
  {/* Semi-transparent overlay for better text visibility */}
  <Box
    position="absolute"
    top={0}
    left={0}
    w="100%"
    h="100%"
    bg="rgba(0, 0, 0, 0.8)" // black overlay with 50% opacity
    zIndex={0}
  />

  {/* Background Circuit Pattern */}
  <Box
    position="absolute"
    top="0"
    left="0"
    right="0"
    bottom="0"
    opacity="0.1"
    backgroundImage="url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><path d=\"M10 10h20v20h-20zM40 10h20v20h-20zM70 10h20v20h-20zM10 40h20v20h-20zM40 40h20v20h-20zM70 40h20v20h-20zM10 70h20v20h-20zM40 70h20v20h-20zM70 70h20v20h-20z\" fill=\"none\" stroke=\"%23ffffff\" stroke-width=\"1\"/></svg>')"
    backgroundSize="60px 60px"
    zIndex={1}
  />
        
        <Container maxW="7xl" position="relative" zIndex="1">
          <VStack
            minH="100vh"
            justify="center"
            align="center"
            spacing={12}
            py={20}
          >
            <HStack
              spacing={20}
              align="center"
              w="full"
              maxW="6xl"
              flexDir={{ base: "column", lg: "row" }}
            >
              {/* Left Side - Text Content */}
              <VStack
                align={{ base: "center", lg: "start" }}
                spacing={8}
                flex="1"
                textAlign={{ base: "center", lg: "left" }}
              >
                <VStack spacing={4} align={{ base: "center", lg: "start" }}>
                  <Text
                    fontSize={{ base: "4xl", md: "5xl", lg: "6xl" }}
                    fontWeight="900"
                    color="white"
                    lineHeight="1.1"
                    textShadow="0 4px 20px rgba(0, 0, 0, 0.3)"
                  >
                    Book Your{" "}
                    <Text as="span" color="cyan.300">
                      Robot Development
                    </Text>{" "}
                    Console Session
                  </Text>
                  
                  <Text
                    fontSize={{ base: "lg", md: "xl" }}
                    color="blue.100"
                    maxW="2xl"
                    lineHeight="1.6"
                  >
                    Reserve dedicated time slots to code, test, and simulate robotics projects. 
                    Access professional development environments with ROS, Gazebo, and real-time 
                    video feedback for TurtleBot, Robot Arms, and Manipulation systems.
                  </Text>
                </VStack>
                
                <HStack spacing={6} flexWrap="wrap" justify={{ base: "center", lg: "start" }}>
                  <Button
                    size="lg"
                    px={8}
                    py={6}
                    fontSize="lg"
                    fontWeight="bold"
                    bgGradient="linear(135deg, cyan.400, blue.500)"
                    color="white"
                    boxShadow="0 8px 32px rgba(0, 255, 255, 0.3)"
                    _hover={{
                      bgGradient: "linear(135deg, cyan.300, blue.400)",
                      boxShadow: "0 12px 48px rgba(0, 255, 255, 0.4)",
                      transform: "translateY(-2px)",
                    }}
                    leftIcon={<FaArrowRight />}
                    onClick={onGetStarted}
                  >
                    Book Development Session
                  </Button>
                  
                  <Button
                    size="lg"
                    px={8}
                    py={6}
                    fontSize="lg"
                    variant="outline"
                    borderColor="cyan.300"
                    color="white"
                    _hover={{
                      bg: "whiteAlpha.200",
                      borderColor: "cyan.200",
                      transform: "translateY(-2px)",
                    }}
                    leftIcon={<FaPhone />}
                    onClick={onGetStarted}
                  >
                    View Available Slots
                  </Button>
                </HStack>
              </VStack>
              
              {/* Right Side - 3D Robot Illustration */}
              <Box
  flex="1"
  display="flex"
  justifyContent="center"
  alignItems="center"
  position="relative"
>
  <Box
    position="relative"
    w="500px"
    h="500px"
    display="flex"
    alignItems="center"
    justifyContent="center"
  >
    {/* Glow Effect */}
    <Box
      position="absolute"
      w="300px"
      h="300px"
      bgGradient="radial(circle, cyan.400 0%, transparent 70%)"
      opacity="0.3"
      borderRadius="full"
      filter="blur(40px)"
      // Make sure pulse animation is defined in CSS
      className="pulse"
    />
    
    {/* Robot Icon */}
    <a href="/img/banner-right-image.png">
      <Image
        src="/img/banner-right-image.png"
        alt="Robot Icon"
        maxW="100%"    // make it fit inside parent
        maxH="100%"
        objectFit="contain"
      />
    </a>
  </Box>
</Box>

            </HStack>
          </VStack>
        </Container>
      </Box>

      {/* About Section */}
      <Container maxW="7xl" py={20}>
        <HStack
          spacing={20}
          align="center"
          w="full"
          flexDir={{ base: "column", lg: "row" }}
        >
          {/* Left Side - Image */}
         <Box
  flex="1"
  display="flex"
  justifyContent="center"
  alignItems="center"
  position="relative"
  minH="100vh" // ensures vertical centering
>
  <Box
    w="400px"
    h="400px"
    bgGradient="linear(135deg, blue.500, cyan.400)"
    borderRadius="30px"
    display="flex"
    justifyContent="center"
    alignItems="center"
    position="relative"
    boxShadow="0 20px 60px rgba(59, 130, 246, 0.3)"
  >
    <Icon
      as={FaHandshake}
      fontSize="600px"        // make the handshake icon much bigger
      color="white"
      filter="drop-shadow(0 10px 30px rgba(0, 0, 0, 0.4))"
    />
  </Box>
</Box>


          
          {/* Right Side - Text Content */}
          <VStack
            align="start"
            spacing={8}
            flex="1"
            textAlign={{ base: "center", lg: "left" }}
          >
            <VStack spacing={4} align={{ base: "center", lg: "start" }}>
              <Text
                fontSize={{ base: "3xl", md: "4xl", lg: "5xl" }}
                fontWeight="900"
                color="blue.900"
                lineHeight="1.2"
              >
                Dedicated Development{" "}
                <Text as="span" color="cyan.500">
                  Environments
                </Text>
              </Text>
              
              <Text
                fontSize="lg"
                color="gray.600"
                lineHeight="1.6"
                maxW="xl"
              >
                Access professional-grade robotics development environments through our 
                time-slot booking system. Code, test, and iterate on your robot projects 
                with dedicated computing resources and simulation capabilities.
              </Text>
            </VStack>
            
            {/* Stats/Features */}
            <SimpleGrid columns={{ base: 2, md: 2 }} spacing={6} w="full">
              <Card
                bg="white"
                border="2px solid"
                borderColor="blue.100"
                borderRadius="15px"
                boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
                _hover={{
                  borderColor: "cyan.300",
                  boxShadow: "0 15px 40px rgba(59, 130, 246, 0.2)",
                  transform: "translateY(-5px)",
                }}
                transition="all 0.3s ease"
              >
                <CardBody textAlign="center" py={6}>
                  <Icon as={FaUsers} fontSize="3xl" color="cyan.500" mb={3} />
                  <Stat>
                    <StatNumber fontSize="2xl" color="blue.900" fontWeight="bold">
                      24/7
                    </StatNumber>
                    <StatLabel color="gray.600" fontSize="sm">
                      Console Access
                    </StatLabel>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card
                bg="white"
                border="2px solid"
                borderColor="blue.100"
                borderRadius="15px"
                boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
                _hover={{
                  borderColor: "cyan.300",
                  boxShadow: "0 15px 40px rgba(59, 130, 246, 0.2)",
                  transform: "translateY(-5px)",
                }}
                transition="all 0.3s ease"
              >
                <CardBody textAlign="center" py={6}>
                  <Icon as={FaAward} fontSize="3xl" color="cyan.500" mb={3} />
                  <Stat>
                    <StatNumber fontSize="2xl" color="blue.900" fontWeight="bold">
                      3
                    </StatNumber>
                    <StatLabel color="gray.600" fontSize="sm">
                      Robot Types
                    </StatLabel>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card
                bg="white"
                border="2px solid"
                borderColor="blue.100"
                borderRadius="15px"
                boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
                _hover={{
                  borderColor: "cyan.300",
                  boxShadow: "0 15px 40px rgba(59, 130, 246, 0.2)",
                  transform: "translateY(-5px)",
                }}
                transition="all 0.3s ease"
              >
                <CardBody textAlign="center" py={6}>
                  <Icon as={FaGlobe} fontSize="3xl" color="cyan.500" mb={3} />
                  <Stat>
                    <StatNumber fontSize="2xl" color="blue.900" fontWeight="bold">
                      ROS+Gazebo
                    </StatNumber>
                    <StatLabel color="gray.600" fontSize="sm">
                      Simulation Ready
                    </StatLabel>
                  </Stat>
                </CardBody>
              </Card>
              
              <Card
                bg="white"
                border="2px solid"
                borderColor="blue.100"
                borderRadius="15px"
                boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
                _hover={{
                  borderColor: "cyan.300",
                  boxShadow: "0 15px 40px rgba(59, 130, 246, 0.2)",
                  transform: "translateY(-5px)",
                }}
                transition="all 0.3s ease"
              >
                <CardBody textAlign="center" py={6}>
                  <Icon as={FaShieldAlt} fontSize="3xl" color="cyan.500" mb={3} />
                  <Stat>
                    <StatNumber fontSize="2xl" color="blue.900" fontWeight="bold">
                      Real-time
                    </StatNumber>
                    <StatLabel color="gray.600" fontSize="sm">
                      Video Feedback
                    </StatLabel>
                  </Stat>
                </CardBody>
              </Card>
            </SimpleGrid>
          </VStack>
        </HStack>
      </Container>

      {/* Services Section */}
      <Box bg="gray.50" py={20}>
        <Container maxW="7xl">
          <VStack spacing={16} w="full">
            <VStack spacing={6} textAlign="center">
              <Text
                fontSize={{ base: "3xl", md: "4xl", lg: "5xl" }}
                fontWeight="900"
                color="blue.900"
                lineHeight="1.2"
                maxW="4xl"
              >
                Professional Development{" "}
                <Text as="span" color="cyan.500">
                  Console Features
                </Text>
              </Text>
              <Text
                fontSize="lg"
                color="gray.600"
                maxW="2xl"
                lineHeight="1.6"
              >
                Book time slots and access dedicated robotics development environments with all the tools you need
              </Text>
            </VStack>
            
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={8} w="full">
{/* Robotic Automation */}
<Card
  bg="white"
  border="2px solid"
  borderColor="blue.100"
  borderRadius="20px"
  boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
  _hover={{
    borderColor: "cyan.300",
    boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
    transform: "translateY(-10px)",
  }}
  transition="all 0.3s ease"
  overflow="hidden"
>
  <CardBody textAlign="center" py={10}>
    <Box
      w="120px"
      h="120px"
      bgGradient="linear(135deg, cyan.400, blue.500)"
      borderRadius="25px"
      display="flex"
      justifyContent="center"
      alignItems="center"
      mx="auto"
      mb={6}
    >
      <Icon as={FaCogs} fontSize="6xl" color="white" />
    </Box>

    <Text fontSize="xl" fontWeight="bold" color="blue.900" mb={4}>
      Code Editor Console
    </Text>

    <Text color="gray.600" lineHeight="1.6" mb={6}>
      Professional Monaco editor with Python syntax highlighting, autocomplete, and ROS library support for robotics development.
    </Text>

    <Button
      size="sm"
      variant="ghost"
      color="cyan.500"
      _hover={{ bg: "cyan.50" }}
      rightIcon={<FaArrowRight />}
    >
      Learn More
    </Button>
  </CardBody>
</Card>

{/* Machine Learning */}
<Card
  bg="white"
  border="2px solid"
  borderColor="blue.100"
  borderRadius="20px"
  boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
  _hover={{
    borderColor: "cyan.300",
    boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
    transform: "translateY(-10px)",
  }}
  transition="all 0.3s ease"
  overflow="hidden"
>
  <CardBody textAlign="center" py={10}>
    <Box
      w="120px"
      h="120px"
      bgGradient="linear(135deg, cyan.400, blue.500)"
      borderRadius="25px"
      display="flex"
      justifyContent="center"
      alignItems="center"
      mx="auto"
      mb={6}
    >
      <Icon as={FaBrain} fontSize="6xl" color="white" />
    </Box>

    <Text fontSize="xl" fontWeight="bold" color="blue.900" mb={4}>
      Gazebo Simulation
    </Text>

    <Text color="gray.600" lineHeight="1.6" mb={6}>
      Test your robot code in realistic 3D environments with physics simulation and real-time video feedback of your robot's behavior.
    </Text>

    <Button
      size="sm"
      variant="ghost"
      color="cyan.500"
      _hover={{ bg: "cyan.50" }}
      rightIcon={<FaArrowRight />}
    >
      Learn More
    </Button>
  </CardBody>
</Card>

{/* Education & Science */}
<Card
  bg="white"
  border="2px solid"
  borderColor="blue.100"
  borderRadius="20px"
  boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
  _hover={{
    borderColor: "cyan.300",
    boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
    transform: "translateY(-10px)",
  }}
  transition="all 0.3s ease"
  overflow="hidden"
>
  <CardBody textAlign="center" py={10}>
    <Box
      w="120px"
      h="120px"
      bgGradient="linear(135deg, cyan.400, blue.500)"
      borderRadius="25px"
      display="flex"
      justifyContent="center"
      alignItems="center"
      mx="auto"
      mb={6}
    >
      <Icon as={FaGraduationCap} fontSize="6xl" color="white" />
    </Box>

    <Text fontSize="xl" fontWeight="bold" color="blue.900" mb={4}>
      Time Slot Booking
    </Text>

    <Text color="gray.600" lineHeight="1.6" mb={6}>
      Reserve dedicated development sessions with guaranteed access to computing resources and simulation environments.
    </Text>

    <Button
      size="sm"
      variant="ghost"
      color="cyan.500"
      _hover={{ bg: "cyan.50" }}
      rightIcon={<FaArrowRight />}
    >
      Learn More
    </Button>
  </CardBody>
</Card>

{/* Predictive Analysis */}
<Card
  bg="white"
  border="2px solid"
  borderColor="blue.100"
  borderRadius="20px"
  boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
  _hover={{
    borderColor: "cyan.300",
    boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
    transform: "translateY(-10px)",
  }}
  transition="all 0.3s ease"
  overflow="hidden"
>
  <CardBody textAlign="center" py={10}>
    <Box
      w="120px"
      h="120px"
      bgGradient="linear(135deg, cyan.400, blue.500)"
      borderRadius="25px"
      display="flex"
      justifyContent="center"
      alignItems="center"
      mx="auto"
      mb={6}
    >
      <Icon as={FaChartLine} fontSize="6xl" color="white" />
    </Box>

    <Text fontSize="xl" fontWeight="bold" color="blue.900" mb={4}>
      Multi-Robot Support
    </Text>

    <Text color="gray.600" lineHeight="1.6" mb={6}>
      Work with TurtleBot navigation, robot arm manipulation, and dexterous hand control in separate booked development sessions.
    </Text>

    <Button
      size="sm"
      variant="ghost"
      color="cyan.500"
      _hover={{ bg: "cyan.50" }}
      rightIcon={<FaArrowRight />}
    >
      Learn More
    </Button>
  </CardBody>
</Card>

              
            </SimpleGrid>
          </VStack>
        </Container>
      </Box>

      {/* Business Growth Section */}
<Box
  position="relative"
  minH="50vh"
  bgImage="url('/img/hero.jpg')"
  bgSize="cover"
  bgPosition="center"
  bgRepeat="no-repeat"
  overflow="hidden"
>
  {/* Semi-transparent overlay for better text visibility */}
  <Box
    position="absolute"
    top={0}
    left={0}
    w="100%"
    h="100%"
    bg="rgba(0, 0, 0, 0.73)" // black overlay with 50% opacity
    zIndex={0}
  />

  {/* Background Circuit Pattern */}
  <Box
    position="absolute"
    top="0"
    left="0"
    right="0"
    bottom="0"
    opacity="0.1"
    backgroundImage="url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><path d=\"M10 10h20v20h-20zM40 10h20v20h-20zM70 10h20v20h-20zM10 40h20v20h-20zM40 40h20v20h-20zM70 40h20v20h-20zM10 70h20v20h-20zM40 70h20v20h-20zM70 70h20v20h-20z\" fill=\"none\" stroke=\"%23ffffff\" stroke-width=\"1\"/></svg>')"
    backgroundSize="60px 60px"
    zIndex={1}
  />
        
        <Container maxW="7xl" position="relative" zIndex="1">
          <HStack
            spacing={20}
            align="center"
            w="full"
            flexDir={{ base: "column", lg: "row" }}
          >
            {/* Left Side - Robot with Tablet */}
<Box
  flex="1"
  display="flex"
  justifyContent="center"
  alignItems="center"
  position="relative"
  minH="500px"
>
  <Box
    position="relative"
    w="400px"
    h="400px"
    display="flex"
    justifyContent="center"
    alignItems="center"
  >
    {/* Glow Effect */}
    <Box
      position="absolute"
      w="300px"
      h="300px"
      bgGradient="radial(circle, cyan.400 0%, transparent 70%)"
      opacity="0.2"
      borderRadius="full"
      filter="blur(50px)"
      animation="pulse 4s infinite"
    />

    {/* Robot with Tablet Illustration */}
    <VStack spacing={-8} align="center">
      <Icon
        as={FaRobot}
        fontSize="220px"
        color="cyan.300"
        filter="drop-shadow(0 10px 30px rgba(0, 255, 255, 0.3))"
      />
      <Box
        w="50px"              // bigger box
        h="50px"              // taller to fit icon
        bg="white"
        borderRadius="15px"
        display="flex"
        alignItems="center"
        justifyContent="center"
        boxShadow="0 10px 30px rgba(51, 0, 255, 0.3)"
        position="relative"
        top="-50px"            // slightly overlap with robot
      >
        
      </Box>
    </VStack>
  </Box>
</Box>



            
            {/* Right Side - Text Content */}
            <VStack
              align={{ base: "center", lg: "start" }}
              spacing={8}
              flex="1"
              textAlign={{ base: "center", lg: "left" }}
            >
              <VStack spacing={4} align={{ base: "center", lg: "start" }}>
                <Text
                  fontSize={{ base: "3xl", md: "4xl", lg: "5xl" }}
                  fontWeight="900"
                  color="white"
                  lineHeight="1.2"
                  maxW="3xl"
                >
                  Complete Development{" "}
                  <Text as="span" color="cyan.300">
                    Workflow in Your Browser
                  </Text>
                </Text>
                
                <Text
                  fontSize="lg"
                  color="blue.100"
                  lineHeight="1.6"
                  maxW="2xl"
                >
                  Book your time slot, access the code editor, write ROS Python code, and see your robot 
                  come to life in Gazebo simulation. Complete robotics development workflow with 
                  real-time feedback and video output of your simulation results.
                </Text>
              </VStack>
              
              <Button
                size="lg"
                px={8}
                py={6}
                fontSize="lg"
                fontWeight="bold"
                bgGradient="linear(135deg, cyan.400, blue.500)"
                color="white"
                boxShadow="0 8px 32px rgba(0, 255, 255, 0.3)"
                _hover={{
                  bgGradient: "linear(135deg, cyan.300, blue.400)",
                  boxShadow: "0 12px 48px rgba(0, 255, 255, 0.4)",
                  transform: "translateY(-2px)",
                }}
                leftIcon={<FaPlay />}
                onClick={onGetStarted}
              >
                Start Development Session
              </Button>
            </VStack>
          </HStack>
        </Container>
      </Box>

      {/* Case Studies Section */}
      <Container maxW="7xl" py={20}>
        <VStack spacing={16} w="full">
          <VStack spacing={6} textAlign="center">
            <Text
              fontSize={{ base: "3xl", md: "4xl", lg: "5xl" }}
              fontWeight="900"
              color="blue.900"
              lineHeight="1.2"
            >
              Development{" "}
              <Text as="span" color="cyan.500">
                Success Stories
              </Text>
            </Text>
            <Text
              fontSize="lg"
              color="gray.600"
              maxW="2xl"
              lineHeight="1.6"
            >
              See how developers are using our console booking system to build amazing robotics projects
            </Text>
          </VStack>
          
            {/* Case Study 1 */}
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={8}>
  {/* Case Study 1 */}
  <Card
    bg="white"
    borderRadius="20px"
    overflow="hidden"
    boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
    _hover={{
      boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
      transform: "translateY(-5px)",
    }}
    transition="all 0.3s ease"
    position="relative"
    cursor="pointer"
  >
    <Box
      h="200px"
      bgGradient="linear(135deg, blue.500, cyan.400)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      overflow="hidden"
    >
      <Icon as={FaCogs} fontSize="8xl" color="white" opacity="0.85" />
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="blackAlpha.300"
        display="flex"
        alignItems="center"
        justifyContent="center"
        opacity="0"
        _hover={{ opacity: "1" }}
        transition="opacity 0.3s ease"
      >
        <Text color="white" fontSize="lg" fontWeight="bold">
          View Case Study
        </Text>
      </Box>
    </Box>
    <CardBody p={6}>
      <Text fontSize="lg" fontWeight="bold" color="blue.900" mb={3}>
        TurtleBot Navigation Project
      </Text>
      <Text color="gray.600" lineHeight="1.6">
        Student developed autonomous navigation algorithm in weekly 2-hour booked sessions, iterating through code and Gazebo simulations.
      </Text>
    </CardBody>
  </Card>

  {/* Case Study 2 */}
  <Card
    bg="white"
    borderRadius="20px"
    overflow="hidden"
    boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
    _hover={{
      boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
      transform: "translateY(-5px)",
    }}
    transition="all 0.3s ease"
    position="relative"
    cursor="pointer"
  >
    <Box
      h="200px"
      bgGradient="linear(135deg, cyan.500, blue.400)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      overflow="hidden"
    >
      <Icon as={FaBrain} fontSize="8xl" color="white" opacity="0.85" />
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="blackAlpha.300"
        display="flex"
        alignItems="center"
        justifyContent="center"
        opacity="0"
        _hover={{ opacity: "1" }}
        transition="opacity 0.3s ease"
      >
        <Text color="white" fontSize="lg" fontWeight="bold">
          View Case Study
        </Text>
      </Box>
    </Box>
    <CardBody p={6}>
      <Text fontSize="lg" fontWeight="bold" color="blue.900" mb={3}>
        Robot Arm Pick & Place
      </Text>
      <Text color="gray.600" lineHeight="1.6">
        Research team prototyped manipulation tasks using booked development slots, testing complex grasping algorithms in simulation.
      </Text>
    </CardBody>
  </Card>

  {/* Case Study 3 */}
  <Card
    bg="white"
    borderRadius="20px"
    overflow="hidden"
    boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
    _hover={{
      boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
      transform: "translateY(-5px)",
    }}
    transition="all 0.3s ease"
    position="relative"
    cursor="pointer"
  >
    <Box
      h="200px"
      bgGradient="linear(135deg, blue.400, cyan.500)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      overflow="hidden"
    >
      <Icon as={FaChartLine} fontSize="8xl" color="white" opacity="0.85" />
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="blackAlpha.300"
        display="flex"
        alignItems="center"
        justifyContent="center"
        opacity="0"
        _hover={{ opacity: "1" }}
        transition="opacity 0.3s ease"
      >
        <Text color="white" fontSize="lg" fontWeight="bold">
          View Case Study
        </Text>
      </Box>
    </Box>
    <CardBody p={6}>
      <Text fontSize="lg" fontWeight="bold" color="blue.900" mb={3}>
        Multi-Robot Coordination
      </Text>
      <Text color="gray.600" lineHeight="1.6">
        Startup team built swarm robotics demo by booking extended sessions and collaborating through shared development environments.
      </Text>
    </CardBody>
  </Card>

  {/* Case Study 4 */}
  <Card
    bg="white"
    borderRadius="20px"
    overflow="hidden"
    boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
    _hover={{
      boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
      transform: "translateY(-5px)",
    }}
    transition="all 0.3s ease"
    position="relative"
    cursor="pointer"
  >
    <Box
      h="200px"
      bgGradient="linear(135deg, cyan.400, blue.600)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      overflow="hidden"
    >
      <Icon as={FaGraduationCap} fontSize="8xl" color="white" opacity="0.85" />
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="blackAlpha.300"
        display="flex"
        alignItems="center"
        justifyContent="center"
        opacity="0"
        _hover={{ opacity: "1" }}
        transition="opacity 0.3s ease"
      >
        <Text color="white" fontSize="lg" fontWeight="bold">
          View Case Study
        </Text>
      </Box>
    </Box>
    <CardBody p={6}>
      <Text fontSize="lg" fontWeight="bold" color="blue.900" mb={3}>
        Educational Technology Innovation
      </Text>
      <Text color="gray.600" lineHeight="1.6">
        Revolutionizing online learning with AI tutors that improved student engagement by 250%.
      </Text>
    </CardBody>
  </Card>

  {/* Case Study 5 */}
  <Card
    bg="white"
    borderRadius="20px"
    overflow="hidden"
    boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
    _hover={{
      boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
      transform: "translateY(-5px)",
    }}
    transition="all 0.3s ease"
    position="relative"
    cursor="pointer"
  >
    <Box
      h="200px"
      bgGradient="linear(135deg, blue.600, cyan.400)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      overflow="hidden"
    >
      <Icon as={FaLightbulb} fontSize="8xl" color="white" opacity="0.85" />
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="blackAlpha.300"
        display="flex"
        alignItems="center"
        justifyContent="center"
        opacity="0"
        _hover={{ opacity: "1" }}
        transition="opacity 0.3s ease"
      >
        <Text color="white" fontSize="lg" fontWeight="bold">
          View Case Study
        </Text>
      </Box>
    </Box>
    <CardBody p={6}>
      <Text fontSize="lg" fontWeight="bold" color="blue.900" mb={3}>
        Smart City Infrastructure
      </Text>
      <Text color="gray.600" lineHeight="1.6">
        Building intelligent urban systems that reduced energy consumption by 40% using IoT and AI.
      </Text>
    </CardBody>
  </Card>

  {/* Case Study 6 */}
  <Card
    bg="white"
    borderRadius="20px"
    overflow="hidden"
    boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
    _hover={{
      boxShadow: "0 20px 50px rgba(59, 130, 246, 0.2)",
      transform: "translateY(-5px)",
    }}
    transition="all 0.3s ease"
    position="relative"
    cursor="pointer"
  >
    <Box
      h="200px"
      bgGradient="linear(135deg, cyan.600, blue.400)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      position="relative"
      overflow="hidden"
    >
      <Icon as={FaShieldAlt} fontSize="8xl" color="white" opacity="0.85" />
      <Box
        position="absolute"
        top="0"
        left="0"
        right="0"
        bottom="0"
        bg="blackAlpha.300"
        display="flex"
        alignItems="center"
        justifyContent="center"
        opacity="0"
        _hover={{ opacity: "1" }}
        transition="opacity 0.3s ease"
      >
        <Text color="white" fontSize="lg" fontWeight="bold">
          View Case Study
        </Text>
      </Box>
    </Box>
    <CardBody p={6}>
      <Text fontSize="lg" fontWeight="bold" color="blue.900" mb={3}>
        Cybersecurity AI Defense
      </Text>
      <Text color="gray.600" lineHeight="1.6">
        Protecting enterprise networks with AI-powered threat detection that stopped 99.9% of attacks.
      </Text>
    </CardBody>
  </Card>
</SimpleGrid>

        </VStack>
      </Container>

      {/* Testimonials Section */}
      <Box bg="gray.50" py={20}>
        <Container maxW="7xl">
          <VStack spacing={16} w="full">
            <VStack spacing={6} textAlign="center">
              <Text
                fontSize={{ base: "3xl", md: "4xl", lg: "5xl" }}
                fontWeight="900"
                color="blue.900"
                lineHeight="1.2"
              >
                Hear it From Our{" "}
                <Text as="span" color="cyan.500">
                  Clients
                </Text>
              </Text>
              <Text
                fontSize="lg"
                color="gray.600"
                maxW="2xl"
                lineHeight="1.6"
              >
                Real feedback from businesses that have transformed with our AI solutions
              </Text>
            </VStack>
            
            {/* Single Testimonial */}
            <Card
              bg="white"
              border="2px solid"
              borderColor="blue.100"
              borderRadius="20px"
              boxShadow="0 20px 60px rgba(59, 130, 246, 0.1)"
              maxW="4xl"
              mx="auto"
              p={8}
            >
              <CardBody>
                <VStack spacing={8} textAlign="center">
                  {/* Quote Icon */}
                  <Icon as={FaQuoteLeft} fontSize="4xl" color="cyan.400" />
                  
                  {/* Testimonial Text */}
                  <Text
                    fontSize={{ base: "lg", md: "xl" }}
                    color="gray.700"
                    lineHeight="1.8"
                    fontStyle="italic"
                    maxW="3xl"
                  >
                    "Using the dedicated robotics development consoles has completely transformed how we work on our projects. We've been able to prototype faster, test more efficiently, and complete iterations in a fraction of the time. The booking system is seamless, and the support provided for the development environments is exceptional. I highly recommend this service to anyone looking to accelerate their robotics and programming projects."
                  </Text>
                  
                  {/* Star Rating */}
                  <HStack spacing={1}>
                    <Icon as={FaStar} color="yellow.400" fontSize="xl" />
                    <Icon as={FaStar} color="yellow.400" fontSize="xl" />
                    <Icon as={FaStar} color="yellow.400" fontSize="xl" />
                    <Icon as={FaStar} color="yellow.400" fontSize="xl" />
                    <Icon as={FaStar} color="yellow.400" fontSize="xl" />
                  </HStack>
                  
                  {/* Client Info */}
                  <HStack spacing={4} align="center">
                    <Avatar
                      size="lg"
                      name="Sarah Johnson"
                      src="https://images.unsplash.com/photo-1494790108755-2616b612b7e8?ixlib=rb-4.0.3&auto=format&fit=crop&w=150&q=80"
                    />
                    <VStack align="start" spacing={0}>
                      <Text fontSize="lg" fontWeight="bold" color="blue.900">
                        Sarah Johnson
                      </Text>
                      <Text fontSize="md" color="gray.600">
                        CEO, TechCorp Industries
                      </Text>
                      <Text fontSize="sm" color="cyan.500">
                        Manufacturing & Automation
                      </Text>
                    </VStack>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </Container>
      </Box>

      {/* FAQ + Contact Section */}
      <Container maxW="7xl" py={20}>
        <HStack
          spacing={20}
          align="start"
          w="full"
          flexDir={{ base: "column", lg: "row" }}
        >
          {/* Left Side - FAQ */}
          <VStack
            align="start"
            spacing={8}
            flex="1"
            w="full"
          >
            <VStack spacing={4} align="start" w="full">
              <Text
                fontSize={{ base: "2xl", md: "3xl", lg: "4xl" }}
                fontWeight="900"
                color="blue.900"
                lineHeight="1.2"
              >
                Frequently Asked{" "}
                <Text as="span" color="cyan.500">
                  Questions
                </Text>
              </Text>
              <Text
                fontSize="lg"
                color="gray.600"
                lineHeight="1.6"
              >
                Get answers to common questions about our AI and robotics solutions
              </Text>
            </VStack>
            
            <Card
              bg="white"
              border="2px solid"
              borderColor="blue.100"
              borderRadius="15px"
              boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
              w="full"
            >
              <CardBody p={4}>
                <Accordion allowMultiple>
                  <AccordionItem border="none">
                    <AccordionButton
                      _hover={{ bg: "blue.50" }}
                      borderRadius="md"
                      py={4}
                    >
                      <Box flex="1" textAlign="left">
                        <Text fontSize="lg" fontWeight="bold" color="blue.900">
                          What industries do you serve?
                        </Text>
                      </Box>
                      <AccordionIcon color="cyan.500" />
                    </AccordionButton>
                    <AccordionPanel pb={4} color="gray.600" fontSize="md" lineHeight="1.6">
                      We serve a wide range of industries including manufacturing, healthcare, 
                      retail, education, finance, and smart cities. Our console solutions are customizable 
                      to meet the specific needs of any business sector.
                    </AccordionPanel>
                  </AccordionItem>

                  <AccordionItem border="none">
                    <AccordionButton
                      _hover={{ bg: "blue.50" }}
                      borderRadius="md"
                      py={4}
                    >
                      <Box flex="1" textAlign="left">
                        <Text fontSize="lg" fontWeight="bold" color="blue.900">
                          How long does implementation take?
                        </Text>
                      </Box>
                      <AccordionIcon color="cyan.500" />
                    </AccordionButton>
                    <AccordionPanel pb={4} color="gray.600" fontSize="md" lineHeight="1.6">
                      Implementation timelines vary based on project complexity. Simple automation 
                      projects can be deployed in 2-4 weeks, while comprehensive console systems may 
                      take 3-6 months. We provide detailed timelines during consultation.
                    </AccordionPanel>
                  </AccordionItem>

                  <AccordionItem border="none">
                    <AccordionButton
                      _hover={{ bg: "blue.50" }}
                      borderRadius="md"
                      py={4}
                    >
                      <Box flex="1" textAlign="left">
                        <Text fontSize="lg" fontWeight="bold" color="blue.900">
                          Do you provide ongoing support?
                        </Text>
                      </Box>
                      <AccordionIcon color="cyan.500" />
                    </AccordionButton>
                    <AccordionPanel pb={4} color="gray.600" fontSize="md" lineHeight="1.6">
                      Yes, we offer comprehensive 24/7 support, regular system updates, 
                      performance monitoring, and continuous optimization to ensure your 
                      booking solutions deliver maximum value over time.
                    </AccordionPanel>
                  </AccordionItem>

                  <AccordionItem border="none">
                    <AccordionButton
                      _hover={{ bg: "blue.50" }}
                      borderRadius="md"
                      py={4}
                    >
                      <Box flex="1" textAlign="left">
                        <Text fontSize="lg" fontWeight="bold" color="blue.900">
                         How does booking a robotics development console improve your project efficiency?
                        </Text>
                      </Box>
                      <AccordionIcon color="cyan.500" />
                    </AccordionButton>
                    <AccordionPanel pb={4} color="gray.600" fontSize="md" lineHeight="1.6">
                      Booking a robotics development console significantly improves project efficiency by giving you access to dedicated computing resources and professional development environments. You can code, simulate, and test your robots in real-time without worrying about hardware limitations or setup delays. With tools like ROS, Gazebo, and real-time video feedback for TurtleBot, Robot Arms, and Manipulation systems, you can iterate faster, troubleshoot effectively, and focus on building and refining your robotics projects, saving both time and effort.
                    </AccordionPanel>
                  </AccordionItem>
                </Accordion>
              </CardBody>
            </Card>
          </VStack>
          
          {/* Right Side - Contact Form */}
          <VStack
            align="start"
            spacing={8}
            flex="1"
            w="full"
          >
            <VStack spacing={4} align="start" w="full">
              <Text
                fontSize={{ base: "2xl", md: "3xl", lg: "4xl" }}
                fontWeight="900"
                color="blue.900"
                lineHeight="1.2"
              >
                Get in{" "}
                <Text as="span" color="cyan.500">
                  Touch
                </Text>
              </Text>
              <Text
                fontSize="lg"
                color="gray.600"
                lineHeight="1.6"
              >
                Ready to transform your business with our easy to access tool? Let's discuss your project.
              </Text>
            </VStack>
            
            <Card
              bg="white"
              border="2px solid"
              borderColor="blue.100"
              borderRadius="15px"
              boxShadow="0 10px 30px rgba(59, 130, 246, 0.1)"
              w="full"
            >
              <CardBody p={8}>
                <VStack spacing={6} w="full">
                  <FormControl>
                    <FormLabel color="blue.900" fontWeight="semibold">
                      Full Name
                    </FormLabel>
                    <Input
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      placeholder="Enter your full name"
                      size="lg"
                      borderColor="blue.200"
                      _hover={{ borderColor: "cyan.400" }}
                      _focus={{ borderColor: "cyan.500", boxShadow: "0 0 0 1px var(--chakra-colors-cyan-500)" }}
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel color="blue.900" fontWeight="semibold">
                      Email Address
                    </FormLabel>
                    <Input
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      placeholder="Enter your email address"
                      size="lg"
                      borderColor="blue.200"
                      _hover={{ borderColor: "cyan.400" }}
                      _focus={{ borderColor: "cyan.500", boxShadow: "0 0 0 1px var(--chakra-colors-cyan-500)" }}
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel color="blue.900" fontWeight="semibold">
                      Message
                    </FormLabel>
                    <Textarea
                      name="message"
                      value={formData.message}
                      onChange={handleInputChange}
                      placeholder="Tell us about your project and how we can help..."
                      rows={5}
                      resize="vertical"
                      borderColor="blue.200"
                      _hover={{ borderColor: "cyan.400" }}
                      _focus={{ borderColor: "cyan.500", boxShadow: "0 0 0 1px var(--chakra-colors-cyan-500)" }}
                    />
                  </FormControl>
                  
                  <Button
                    size="lg"
                    w="full"
                    py={6}
                    fontSize="lg"
                    fontWeight="bold"
                    bgGradient="linear(135deg, cyan.400, blue.500)"
                    color="white"
                    boxShadow="0 8px 32px rgba(0, 255, 255, 0.3)"
                    isLoading={isSubmitting}
                    onClick={handleSubmitMessage}
                    _hover={{
                      bgGradient: "linear(135deg, cyan.300, blue.400)",
                      boxShadow: "0 12px 48px rgba(0, 255, 255, 0.4)",
                      transform: "translateY(-2px)",
                    }}
                    leftIcon={<FaArrowRight />}
                  >
                    Send Message
                  </Button>
                </VStack>
              </CardBody>
            </Card>
          </VStack>
        </HStack>
      </Container>

      {/* Footer */}
      {/* Hero Section */}
<Box
  position="relative"
  minH="50vh"
  bgImage="url('/img/hero.jpg')"
  py={16}
  bgSize="cover"
  bgPosition="center"
  bgRepeat="no-repeat"
  overflow="hidden"
>
  {/* Semi-transparent overlay for better text visibility */}
  <Box
    position="absolute"
    top={0}
    left={0}
    w="100%"
    h="100%"
    bg="rgba(0, 0, 0, 0.8)" // black overlay with 50% opacity
    zIndex={0}
  />

  {/* Background Circuit Pattern */}
  <Box
    position="absolute"
    top="0"
    left="0"
    right="0"
    bottom="0"
    opacity="0.1"
    backgroundImage="url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><path d=\"M10 10h20v20h-20zM40 10h20v20h-20zM70 10h20v20h-20zM10 40h20v20h-20zM40 40h20v20h-20zM70 40h20v20h-20zM10 70h20v20h-20zM40 70h20v20h-20zM70 70h20v20h-20z\" fill=\"none\" stroke=\"%23ffffff\" stroke-width=\"1\"/></svg>')"
    backgroundSize="60px 60px"
    zIndex={1}
  />
        <Container maxW="7xl" position="relative" zIndex="1">
          <VStack spacing={12} w="full">
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={10} w="full">
              {/* Company Info */}
              <VStack align="start" spacing={6}>
                <HStack spacing={3}>
                  <Icon as={FaRobot} fontSize="3xl" color="cyan.300" />
                  <Text fontSize="2xl" fontWeight="bold" color="white">
                    AI Robotics
                  </Text>
                </HStack>
                <Text color="blue.100" lineHeight="1.6" maxW="sm">
                  Book Your Robot Development Console Session</Text>
                <HStack spacing={4}>
                  <Link href="#" _hover={{ color: "cyan.300" }}>
                    <Icon as={FaFacebook} fontSize="xl" color="blue.200" />
                  </Link>
                  <Link href="#" _hover={{ color: "cyan.300" }}>
                    <Icon as={FaTwitter} fontSize="xl" color="blue.200" />
                  </Link>
                  <Link href="#" _hover={{ color: "cyan.300" }}>
                    <Icon as={FaLinkedin} fontSize="xl" color="blue.200" />
                  </Link>
                  <Link href="#" _hover={{ color: "cyan.300" }}>
                    <Icon as={FaGithub} fontSize="xl" color="blue.200" />
                  </Link>
                </HStack>
              </VStack>
              
              {/* Quick Links */}
              <VStack align="start" spacing={4}>
                <Text fontSize="lg" fontWeight="bold" color="cyan.300">
                  Quick Links
                </Text>
                <VStack align="start" spacing={2}>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    About Us
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Our Story
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Case Studies
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Blog
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Careers
                  </Link>
                </VStack>
              </VStack>
              
              {/* Services */}
              <VStack align="start" spacing={4}>
                <Text fontSize="lg" fontWeight="bold" color="cyan.300">
                  Services
                </Text>
                <VStack align="start" spacing={2}>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Robotic Automation
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Machine Learning
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Education & Science
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Predictive Analysis
                  </Link>
                  <Link href="#" color="blue.100" _hover={{ color: "white" }}>
                    Consulting
                  </Link>
                </VStack>
              </VStack>
              
              {/* Contact Info */}
              <VStack align="start" spacing={4}>
                <Text fontSize="lg" fontWeight="bold" color="cyan.300">
                  Contact Info
                </Text>
                <VStack align="start" spacing={3}>
                  <HStack spacing={3}>
                    <Icon as={FaMapMarkerAlt} color="cyan.400" />
                    <Text color="blue.100" fontSize="sm">
                      123 Innovation Drive, Tech City, TC 12345
                    </Text>
                  </HStack>
                  <HStack spacing={3}>
                    <Icon as={FaPhone} color="cyan.400" />
                    <Text color="blue.100" fontSize="sm">
                      +1 (555) 123-4567
                    </Text>
                  </HStack>
                  <HStack spacing={3}>
                    <Icon as={FaEnvelope} color="cyan.400" />
                    <Text color="blue.100" fontSize="sm">
                      contact@airobotics.com
                    </Text>
                  </HStack>
                </VStack>
              </VStack>
            </SimpleGrid>
            
            <Divider borderColor="blue.600" />
            
            {/* Copyright */}
            <Flex
              direction={{ base: "column", md: "row" }}
              justify="space-between"
              align="center"
              w="full"
              gap={4}
            >
              <Text color="blue.200" fontSize="sm">
                © 2024 AI Robotics. All rights reserved.
              </Text>
              <HStack spacing={6}>
                <Link href="#" color="blue.200" fontSize="sm" _hover={{ color: "white" }}>
                  Privacy Policy
                </Link>
                <Link href="#" color="blue.200" fontSize="sm" _hover={{ color: "white" }}>
                  Terms of Service
                </Link>
                <Link href="#" color="blue.200" fontSize="sm" _hover={{ color: "white" }}>
                  Cookie Policy
                </Link>
              </HStack>
            </Flex>
          </VStack>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;