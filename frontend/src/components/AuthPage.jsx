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
  Link,
  Divider,
} from "@chakra-ui/react";
import { useState } from "react";
import { loginUser, registerUser, googleLogin } from "../api";
import { FcGoogle } from "react-icons/fc";

const AuthPage = ({ onAuth, onBack, onForgotPassword }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const toast = useToast();

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    
    try {
      // Load Google Identity Services library
      if (!window.google) {
        toast({
          title: "Google Sign-In unavailable",
          description: "Please check your internet connection or contact support",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        setIsGoogleLoading(false);
        return;
      }

      // Initialize Google Sign-In
      const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
      
      if (!googleClientId) {
        toast({
          title: "Google Sign-In not configured",
          description: "Please contact support to enable Google Sign-In",
          status: "warning",
          duration: 5000,
          isClosable: true,
        });
        setIsGoogleLoading(false);
        return;
      }
      
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          try {
            const result = await googleLogin(response.credential);
            
            // Store token in localStorage
            localStorage.setItem('authToken', result.access_token);
            
            onAuth(result.user, result.access_token);
            toast({
              title: "Google Sign-In successful",
              status: "success",
              duration: 3000,
              isClosable: true,
            });
          } catch (error) {
            console.error('Google login error:', error);
            toast({
              title: "Google Sign-In failed",
              description: error.response?.data?.detail || "Failed to authenticate with Google",
              status: "error",
              duration: 5000,
              isClosable: true,
            });
          } finally {
            setIsGoogleLoading(false);
          }
        }
      });

      // Prompt the user to sign in
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          // Fallback to button click
          window.google.accounts.id.renderButton(
            document.getElementById("google-signin-button"),
            { theme: "outline", size: "large", width: "100%" }
          );
          setIsGoogleLoading(false);
        }
      });
    } catch (error) {
      console.error('Google Sign-In initialization error:', error);
      toast({
        title: "Google Sign-In unavailable",
        description: "Please try again or use email/password login",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      setIsGoogleLoading(false);
    }
  };

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
        
        // Registration successful - email confirmation required
        toast({
          title: "Registration successful!",
          description: response.message || "Please check your email to confirm your account.",
          status: "success",
          duration: 10000,
          isClosable: true,
        });
        
        // Clear form
        setRegisterData({
          name: "",
          email: "",
          password: "",
          confirmPassword: ""
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
                      {/* Google Sign-In Button */}
                      <Button
                        leftIcon={<FcGoogle />}
                        colorScheme="gray"
                        variant="outline"
                        width="100%"
                        onClick={handleGoogleSignIn}
                        isLoading={isGoogleLoading}
                        loadingText="Signing in with Google..."
                      >
                        Continue with Google
                      </Button>
                      
                      <div id="google-signin-button" style={{ width: '100%' }}></div>
                      
                      <HStack width="100%" spacing={4}>
                        <Divider />
                        <Text fontSize="sm" color="gray.400" whiteSpace="nowrap">
                          or
                        </Text>
                        <Divider />
                      </HStack>

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

                      <Link
                        onClick={() => onForgotPassword && onForgotPassword()}
                        fontSize="sm"
                        color="blue.400"
                        alignSelf="flex-end"
                        cursor="pointer"
                        _hover={{ color: "blue.300", textDecoration: "underline" }}
                      >
                        Forgot Password?
                      </Link>

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
                      {/* Google Sign-In Button */}
                      <Button
                        leftIcon={<FcGoogle />}
                        colorScheme="gray"
                        variant="outline"
                        width="100%"
                        onClick={handleGoogleSignIn}
                        isLoading={isGoogleLoading}
                        loadingText="Signing in with Google..."
                      >
                        Continue with Google
                      </Button>
                      
                      <HStack width="100%" spacing={4}>
                        <Divider />
                        <Text fontSize="sm" color="gray.400" whiteSpace="nowrap">
                          or
                        </Text>
                        <Divider />
                      </HStack>

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

        <Button variant="ghost" onClick={onBack} color="gray.400">
          ← Back to Home
        </Button>
      </VStack>
    </Container>
  );
};

export default AuthPage;
