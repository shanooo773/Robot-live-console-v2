import { useState, useEffect } from "react";
import { Lock, Eye, EyeOff } from "lucide-react";
import { useToast } from "@chakra-ui/react";
import { resetPassword } from "../api";
import "../styles/login.css";

const ResetPasswordPage = ({ onSuccess, resetToken }) => {
  const [newPassword, setNewPassword]       = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword]     = useState(false);
  const [loading, setLoading]               = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (!resetToken) {
      toast({
        title: "Invalid reset link",
        description: "This password reset link is invalid or expired.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  }, [resetToken, toast]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast({ title: "Passwords do not match", status: "error", duration: 3000, isClosable: true });
      return;
    }

    if (newPassword.length < 8) {
      toast({ title: "Password too short", description: "Password must be at least 8 characters.", status: "error", duration: 3000, isClosable: true });
      return;
    }

    setLoading(true);
    try {
      await resetPassword(resetToken, newPassword);
      toast({ title: "Password reset successful", description: "You can now sign in with your new password.", status: "success", duration: 3000, isClosable: true });
      setTimeout(() => onSuccess?.(), 2000);
    } catch (error) {
      toast({
        title: "Reset failed",
        description: error.response?.data?.detail || "Invalid or expired token.",
        status: "error",
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (!resetToken) {
    return (
      <div className="login-wrapper">
        <div className="auth-form-panel">
          <div className="login-card" style={{ textAlign: "center" }}>
            <h2>❌ Invalid Link</h2>
            <p className="login-sub">This reset link is invalid or has expired.</p>
            <button className="login-btn" onClick={onSuccess}>Go to Login</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-wrapper">
      <div className="auth-hero">
        <div className="auth-hero__logo">🤖 Anybot</div>
        <div className="auth-hero__tagline">Build. Code. Simulate.<br /><span>Learn Robotics.</span></div>
        <p className="auth-hero__sub">Access real ROS + Gazebo development environments designed for STEM students and future robotics engineers.</p>
        <ul className="auth-hero__features">
          <li>TurtleBot Navigation</li>
          <li>Robot Arm Manipulation</li>
          <li>Real-Time Simulation</li>
          <li>Live Video Feedback</li>
        </ul>
      </div>

      <div className="auth-form-panel">
        <div className="login-card">
          <div className="auth-badge">🔑 Password Reset</div>
          <h2>Set New Password</h2>
          <p className="login-sub">Enter your new password below.</p>

          <form onSubmit={handleSubmit}>
            <div className="input-box">
              <Lock size={18} />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="New password (min 8 characters)"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
                minLength={8}
              />
              <button type="button" className="eye-btn" onClick={() => setShowPassword(p => !p)}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            <div className="input-box">
              <Lock size={18} />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <button className="login-btn" disabled={loading}>
              {loading ? "Resetting..." : "Reset Password"}
            </button>

            <p className="back-login" onClick={onSuccess}>← Back to Login</p>
          </form>

          <p className="secure-text">🔒 Your data is securely encrypted</p>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
