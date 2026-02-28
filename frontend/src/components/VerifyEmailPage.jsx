import {
  Box,
  Button,
  VStack,
  Heading,
  Text,
  useToast,
  Container,
  Card,
  CardBody,
  Alert,
  AlertIcon,
  Spinner,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { confirmEmail } from "../api";

const VerifyEmailPage = ({ token, onSuccess }) => {
  const [status, setStatus] = useState("loading"); // loading | success | error
  const [errorMessage, setErrorMessage] = useState("");
  const toast = useToast();

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMessage("No verification token found in the URL.");
      return;
    }

    confirmEmail(token)
      .then(() => {
        setStatus("success");
        toast({
          title: "Email verified!",
          description: "Your account is now active. You can sign in.",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      })
      .catch((error) => {
        setStatus("error");
        const detail =
          error.response?.data?.detail ||
          "This verification link is invalid or has expired.";
        setErrorMessage(detail);
      });
  }, [token, toast]);

  return (
    <Container maxW="md" py={20}>
      <Card bg="gray.800" border="1px solid" borderColor="gray.600">
        <CardBody>
          <VStack spacing={6}>
            {status === "loading" && (
              <>
                <Spinner size="xl" color="blue.400" />
                <Heading size="md" color="white">
                  Verifying your email…
                </Heading>
              </>
            )}

            {status === "success" && (
              <>
                <Text fontSize="4xl">✅</Text>
                <Heading size="lg" color="white">
                  Email Verified!
                </Heading>
                <Alert
                  status="success"
                  bg="green.900"
                  color="green.100"
                  border="1px solid"
                  borderColor="green.600"
                >
                  <AlertIcon color="green.300" />
                  <Text fontSize="sm">
                    Your account has been activated. You can now sign in.
                  </Text>
                </Alert>
                <Button colorScheme="blue" w="full" onClick={onSuccess}>
                  Go to Sign In
                </Button>
              </>
            )}

            {status === "error" && (
              <>
                <Text fontSize="4xl">❌</Text>
                <Heading size="lg" color="white">
                  Verification Failed
                </Heading>
                <Alert
                  status="error"
                  bg="red.900"
                  color="red.100"
                  border="1px solid"
                  borderColor="red.600"
                >
                  <AlertIcon color="red.300" />
                  <Text fontSize="sm">{errorMessage}</Text>
                </Alert>
                <Button colorScheme="blue" w="full" onClick={onSuccess}>
                  Back to Sign In
                </Button>
              </>
            )}
          </VStack>
        </CardBody>
      </Card>
    </Container>
  );
};

export default VerifyEmailPage;
