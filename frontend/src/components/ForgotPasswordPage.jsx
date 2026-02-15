import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Text,
  useToast,
  Container,
  Card,
  CardBody,
} from "@chakra-ui/react";
import { useState } from "react";
import { forgotPassword } from "../api";

const ForgotPasswordPage = ({ onBack }) => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await forgotPassword(email);
      setSent(true);
      toast({
        title: "Reset email sent",
        description: "Check your inbox for password reset link",
        status: "success",
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      console.error("Forgot password error:", error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Could not send reset email",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <Container maxW="md" py={20}>
        <Card bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardBody textAlign="center">
            <VStack spacing={4}>
              <Text fontSize="4xl">📧</Text>
              <Heading size="lg" color="white">Check Your Email</Heading>
              <Text color="gray.300">
                If an account exists for <strong>{email}</strong>, you will receive a password reset link shortly.
              </Text>
              <Button variant="ghost" onClick={onBack} color="blue.400">
                ← Back to Login
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Container>
    );
  }

  return (
    <Container maxW="md" py={20}>
      <Card bg="gray.800" border="1px solid" borderColor="gray.600">
        <CardBody>
          <VStack spacing={4} as="form" onSubmit={handleSubmit}>
            <Text fontSize="4xl">🔒</Text>
            <Heading size="lg" color="white">Forgot Password</Heading>
            <Text color="gray.300" textAlign="center">
              Enter your email address and we'll send you a link to reset your password.
            </Text>

            <FormControl isRequired>
              <FormLabel color="gray.200">Email</FormLabel>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@example.com"
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
              w="full"
              isLoading={loading}
              loadingText="Sending..."
            >
              Send Reset Link
            </Button>

            <Button
              variant="link"
              onClick={onBack}
              color="gray.400"
            >
              ← Back to Login
            </Button>
          </VStack>
        </CardBody>
      </Card>
    </Container>
  );
};

export default ForgotPasswordPage;
