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
import { useState, useEffect } from "react";
import { resetPassword } from "../api";

const ResetPasswordPage = ({ onSuccess, resetToken }) => {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast({
        title: "Passwords do not match",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (newPassword.length < 8) {
      toast({
        title: "Password too short",
        description: "Password must be at least 8 characters",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setLoading(true);
    try {
      await resetPassword(resetToken, newPassword);

      toast({
        title: "Password reset successful",
        description: "You can now login with your new password",
        status: "success",
        duration: 3000,
        isClosable: true,
      });

      // Navigate back to auth page after success
      if (onSuccess) {
        setTimeout(() => onSuccess(), 2000);
      }
    } catch (error) {
      console.error("Reset password error:", error);
      toast({
        title: "Reset failed",
        description: error.response?.data?.detail || "Invalid or expired token",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxW="md" py={20}>
      <Card bg="gray.800" border="1px solid" borderColor="gray.600">
        <CardBody>
          <VStack spacing={4} as="form" onSubmit={handleSubmit}>
            <Text fontSize="4xl">🔑</Text>
            <Heading size="lg" color="white">Reset Password</Heading>
            <Text color="gray.300" textAlign="center">
              Enter your new password below
            </Text>

            <FormControl isRequired>
              <FormLabel color="gray.200">New Password</FormLabel>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={8}
                placeholder="At least 8 characters"
                bg="gray.700"
                border="1px solid"
                borderColor="gray.600"
                color="white"
                _placeholder={{ color: "gray.400" }}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel color="gray.200">Confirm Password</FormLabel>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={8}
                placeholder="Re-enter your password"
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
              loadingText="Resetting..."
            >
              Reset Password
            </Button>
          </VStack>
        </CardBody>
      </Card>
    </Container>
  );
};

export default ResetPasswordPage;
