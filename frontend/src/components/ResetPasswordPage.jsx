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
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { resetPassword } from "../api";

const ResetPasswordPage = ({ onSuccess, resetToken }) => {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const toast = useToast();

  // Validate resetToken is provided
  useEffect(() => {
    if (!resetToken) {
      toast({
        title: "Invalid reset link",
        description: "This password reset link is invalid or expired",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  }, [resetToken, toast]);

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

  // Show error if no token
  if (!resetToken) {
    return (
            <div className="login-wrapper">
        <div className="login-card" style={{ textAlign: "center" }}>
          <h2>❌ Invalid Link</h2>

          <p className="login-sub">
            This reset link is invalid or expired.
          </p>

          <button className="login-btn" onClick={onSuccess}>
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (

        <div className="login-wrapper">

      <div className="login-card">

        <h2>Reset Password 🔑</h2>

        <p className="login-sub">
          Enter your new password below
        </p>

        <form onSubmit={handleSubmit}>

          {/* PASSWORD */}
          <div className="input-box">
            <Lock size={18} />

            <input
              type={showPassword ? "text" : "password"}
              placeholder="At least 8 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />

            <button
              type="button"
              className="eye-btn"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* CONFIRM PASSWORD */}
          <div className="input-box">
            <Lock size={18} />

            <input
              type={showPassword ? "text" : "password"}
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>

          {/* BUTTON */}
          <button className="login-btn" disabled={loading}>
            {loading ? "Resetting..." : "Reset Password"}
          </button>

          {/* BACK */}
          <p className="back-login" onClick={onSuccess}>
            ← Back to Login
          </p>

        </form>

      </div>

    </div>
  );
};

export default ResetPasswordPage;
