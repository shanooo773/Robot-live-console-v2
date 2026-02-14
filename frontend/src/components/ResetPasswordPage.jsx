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
import { useState, useEffect } from "react";
import { resetPassword } from "../api";

const ResetPasswordPage = ({ onBack, onSuccess }) => {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState("");
  const toast = useToast();

  useEffect(() => {
    // Get token from URL query parameters
    const params = new URLSearchParams(window.location.search);
    const resetToken = params.get("token");
    
    if (resetToken) {
      setToken(resetToken);
    } else {
      toast({
        title: "Invalid reset link",
        description: "No reset token found in the URL",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (!token) {
        toast({
          title: "Invalid reset link",
          description: "No reset token found. Please request a new password reset.",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        setIsLoading(false);
        return;
      }

      if (newPassword !== confirmPassword) {
        toast({
          title: "Passwords don't match",
          description: "Please make sure both passwords are the same",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
        setIsLoading(false);
        return;
      }

      if (newPassword.length < 6) {
        toast({
          title: "Password too short",
          description: "Password must be at least 6 characters long",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
        setIsLoading(false);
        return;
      }

      const response = await resetPassword(token, newPassword);
      
      toast({
        title: "Password reset successful!",
        description: response.message || "You can now log in with your new password.",
        status: "success",
        duration: 5000,
        isClosable: true,
      });

      // Clear form and redirect to login
      setNewPassword("");
      setConfirmPassword("");
      
      setTimeout(() => {
        if (onSuccess) {
          onSuccess();
        } else {
          window.location.href = "/";
        }
      }, 2000);
      
    } catch (error) {
      console.error('Reset password error:', error);
      toast({
        title: "Password reset failed",
        description: error.response?.data?.detail || "Failed to reset password. The link may have expired.",
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
          <Text fontSize="4xl">🔐</Text>
          <Text fontSize="2xl" fontWeight="bold" color="white">
            Reset Password
          </Text>
          <Text color="gray.300">
            Enter your new password below
          </Text>
        </VStack>

        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardBody>
            <form onSubmit={handleSubmit}>
              <VStack spacing={4}>
                <FormControl>
                  <FormLabel color="gray.300">New Password</FormLabel>
                  <Input
                    type="password"
                    placeholder="Enter new password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
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
                    placeholder="Confirm new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
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
                  loadingText="Resetting..."
                  isDisabled={!token}
                >
                  Reset Password
                </Button>
              </VStack>
            </form>
          </CardBody>
        </Card>

        <Button variant="ghost" onClick={onBack} color="gray.400">
          ← Back to Login
        </Button>
      </VStack>
    </Container>
  );
};

export default ResetPasswordPage;
