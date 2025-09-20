import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  FormControl,
  FormLabel,
  Container,
  Card,
  CardBody,
  CardHeader,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import { useState } from "react";
import { loginUser, registerUser } from "../api";

const AuthPage = ({ onAuth, onBack }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const toast = useToast();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (loginData.email && loginData.password) {
        const response = await loginUser({
          email: loginData.email,
          password: loginData.password
        });
        
        // Store token in localStorage
        localStorage.setItem('authToken', response.access_token);
        
        onAuth(response.user, response.access_token);
        toast({
          title: "Login successful",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Login failed",
          description: "Please enter both email and password",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Login error:', error);
      toast({
        title: "Login failed",
        description: error.response?.data?.detail || "Invalid email or password",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (registerData.name && registerData.email && registerData.password) {
        if (registerData.password !== registerData.confirmPassword) {
          toast({
            title: "Registration failed",
            description: "Passwords do not match",
            status: "error",
            duration: 3000,
            isClosable: true,
          });
          setIsLoading(false);
          return;
        }

        const response = await registerUser({
          name: registerData.name,
          email: registerData.email,
          password: registerData.password
        });
        
        // Store token in localStorage
        localStorage.setItem('authToken', response.access_token);
        
        onAuth(response.user, response.access_token);
        toast({
          title: "Registration successful",
          description: "Welcome to Robot Programming Console!",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Registration failed",
          description: "Please fill in all fields",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Registration error:', error);
      toast({
        title: "Registration failed",
        description: error.response?.data?.detail || "Registration failed. Please try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipAuth = () => {
    // Create a demo user object
    const demoUser = {
      id: "demo",
      name: "Demo User",
      email: "demo@example.com",
      role: "user",
      isDemoMode: true
    };
    
    // Set demo flag in localStorage
    localStorage.setItem('isDemoMode', 'true');
    
    // Call onAuth with demo user and no token
    onAuth(demoUser, null);
    
    toast({
      title: "Demo Mode Activated",
      description: "You now have full access without signing up!",
      status: "success",
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Container maxW="md" py={20}>
      <VStack spacing={8}>
        <VStack spacing={4} textAlign="center">
          <Text fontSize="4xl">🤖</Text>
          <Text fontSize="2xl" fontWeight="bold" color="white">
            Welcome Back
          </Text>
          <Text color="gray.300">
            Sign in to book your robot programming session
          </Text>
        </VStack>

        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardBody>
            <Tabs variant="enclosed" colorScheme="blue">
              <TabList>
                <Tab color="gray.300" _selected={{ color: "white", bg: "blue.600" }}>
                  Sign In
                </Tab>
                <Tab color="gray.300" _selected={{ color: "white", bg: "blue.600" }}>
                  Sign Up
                </Tab>
              </TabList>

              <TabPanels>
                {/* Login Tab */}
                <TabPanel px={0}>
                  <form onSubmit={handleLogin}>
                    <VStack spacing={4}>
                      <FormControl>
                        <FormLabel color="gray.300">Email</FormLabel>
                        <Input
                          type="email"
                          placeholder="Enter your email"
                          value={loginData.email}
                          onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                          bg="gray.700"
                          border="1px solid"
                          borderColor="gray.600"
                          color="white"
                          _placeholder={{ color: "gray.400" }}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel color="gray.300">Password</FormLabel>
                        <Input
                          type="password"
                          placeholder="Enter your password"
                          value={loginData.password}
                          onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                          bg="gray.700"
                          border="1px solid"
                          borderColor="gray.600"
                          color="white"
                          _placeholder={{ color: "gray.400" }}
                        />
                      </FormControl>

                      <Button
                        type="submit"
                        colorScheme="blue"
                        size="lg"
                        w="full"
                        isLoading={isLoading}
                        loadingText="Signing in..."
                      >
                        Sign In
                      </Button>
                    </VStack>
                  </form>
                </TabPanel>

                {/* Register Tab */}
                <TabPanel px={0}>
                  <form onSubmit={handleRegister}>
                    <VStack spacing={4}>
                      <FormControl>
                        <FormLabel color="gray.300">Full Name</FormLabel>
                        <Input
                          type="text"
                          placeholder="Enter your full name"
                          value={registerData.name}
                          onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
                          bg="gray.700"
                          border="1px solid"
                          borderColor="gray.600"
                          color="white"
                          _placeholder={{ color: "gray.400" }}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel color="gray.300">Email</FormLabel>
                        <Input
                          type="email"
                          placeholder="Enter your email"
                          value={registerData.email}
                          onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                          bg="gray.700"
                          border="1px solid"
                          borderColor="gray.600"
                          color="white"
                          _placeholder={{ color: "gray.400" }}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel color="gray.300">Password</FormLabel>
                        <Input
                          type="password"
                          placeholder="Choose a password"
                          value={registerData.password}
                          onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                          bg="gray.700"
                          border="1px solid"
                          borderColor="gray.600"
                          color="white"
                          _placeholder={{ color: "gray.400" }}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel color="gray.300">Confirm Password</FormLabel>
                        <Input
                          type="password"
                          placeholder="Confirm your password"
                          value={registerData.confirmPassword}
                          onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                          bg="gray.700"
                          border="1px solid"
                          borderColor="gray.600"
                          color="white"
                          _placeholder={{ color: "gray.400" }}
                        />
                      </FormControl>

                      <Button
                        type="submit"
                        colorScheme="green"
                        size="lg"
                        w="full"
                        isLoading={isLoading}
                        loadingText="Creating account..."
                      >
                        Create Account
                      </Button>
                    </VStack>
                  </form>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardBody>
        </Card>

        <Alert status="info" bg="blue.900" color="blue.100" border="1px solid" borderColor="blue.600">
          <AlertIcon color="blue.300" />
          <Text fontSize="sm">
            Sign in to manage your bookings and access exclusive features!
          </Text>
        </Alert>

        {/* Skip Authentication Button */}
        <Card bg="orange.800" borderColor="orange.600" border="1px solid">
          <CardBody>
            <VStack spacing={3}>
              <Text color="orange.200" textAlign="center" fontSize="sm">
                Want to skip authentication? Try our demo mode!
              </Text>
              <Button
                colorScheme="orange"
                size="lg"
                w="full"
                onClick={handleSkipAuth}
                variant="solid"
              >
                🚀 Skip & Go to Booking
              </Button>
              <Text color="orange.300" fontSize="xs" textAlign="center">
                Demo mode gives you full access without signing up
              </Text>
            </VStack>
          </CardBody>
        </Card>
        <Button variant="ghost" onClick={onBack} color="gray.400">
          ← Back to Home
        </Button>
      </VStack>
    </Container>
  );
};

export default AuthPage;
