import {
  Box,
  VStack,
  Text,
  Button,
  Input,
  FormControl,
  FormLabel,
  Container,
  Card,
  CardBody,
  useToast,
} from "@chakra-ui/react";
import { useState } from "react";
import { forgotPassword } from "../api";

const ForgotPasswordPage = ({ onBack }) => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (email) {
        const response = await forgotPassword(email);
        
        setEmailSent(true);
        toast({
          title: "Email sent!",
          description: response.message || "Check your email for password reset instructions.",
          status: "success",
          duration: 10000,
          isClosable: true,
        });
        
        setEmail("");
      } else {
        toast({
          title: "Email required",
          description: "Please enter your email address",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Forgot password error:', error);
      toast({
        title: "Request failed",
        description: error.response?.data?.detail || "Failed to send reset email. Please try again.",
        status: "error",
        duration: 5000,
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
          <Text fontSize="4xl">🔑</Text>
          <Text fontSize="2xl" fontWeight="bold" color="white">
            Forgot Password
          </Text>
          <Text color="gray.300">
            Enter your email address and we'll send you a link to reset your password
          </Text>
        </VStack>

        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardBody>
            {!emailSent ? (
              <form onSubmit={handleSubmit}>
                <VStack spacing={4}>
                  <FormControl>
                    <FormLabel color="gray.300">Email Address</FormLabel>
                    <Input
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
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
                    loadingText="Sending..."
                  >
                    Send Reset Link
                  </Button>
                </VStack>
              </form>
            ) : (
              <VStack spacing={4}>
                <Text color="green.300" textAlign="center">
                  ✅ Password reset email sent successfully!
                </Text>
                <Text color="gray.300" fontSize="sm" textAlign="center">
                  Check your inbox and follow the instructions to reset your password.
                </Text>
                <Button
                  variant="outline"
                  colorScheme="blue"
                  onClick={() => setEmailSent(false)}
                >
                  Send Another Email
                </Button>
              </VStack>
            )}
          </CardBody>
        </Card>

        <Button variant="ghost" onClick={onBack} color="gray.400">
          ← Back to Login
        </Button>
      </VStack>
    </Container>
  );
};

export default ForgotPasswordPage;
