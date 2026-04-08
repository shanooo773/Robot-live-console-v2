import "../styles/login.css";
import { useState, useEffect, useCallback } from "react";
import { Github, Mail, Lock, Eye, EyeOff, User } from "lucide-react";
import { loginUser, registerUser, googleLogin, resendConfirmation } from "../api";
import { useToast } from "@chakra-ui/react";
import { FcGoogle } from "react-icons/fc";

const AuthPage = ({ onAuth, onBack, onForgotPassword, mode }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showRegPassword, setShowRegPassword] = useState(false);

  // "login" or "register" or "emailSent"
  const [activeView, setActiveView] = useState(mode || "login");
  useEffect(() => {
    if (mode) {
      setActiveView(mode);
    }
  }, [mode]);

  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const [registrationEmail, setRegistrationEmail] = useState(null);

  const [errorMsg, setErrorMsg] = useState("");

  const toast = useToast();

  // Memoize Google response handler to prevent unnecessary re-renders
  // Fix: store JWT under 'token' so API interceptor attaches it
  const handleGoogleResponse = useCallback(async (response) => {
    try {
      setIsLoading(true);
      const result = await googleLogin(response.credential);

      // Store token consistently
      localStorage.setItem("token", result.access_token);
      localStorage.setItem("user", JSON.stringify(result.user));

      onAuth(result.user, result.access_token);
      toast({
        title: "Google login successful",
        description: "Welcome to Robot Programming Console!",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error("Google login failed:", error);
      toast({
        title: "Google login failed",
        description: error.response?.data?.detail || "Could not sign in with Google",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  }, [onAuth, toast]);

  // Initialize Google Sign-In
  useEffect(() => {
    if (window.google && import.meta.env.VITE_GOOGLE_CLIENT_ID) {
      try {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
          callback: handleGoogleResponse,
          auto_select: false,
        });
      } catch (error) {
        console.error("Google Sign-In initialization failed:", error);
      }
    }
  }, [handleGoogleResponse]);

  const handleGoogleSignIn = () => {
    if (window.google && import.meta.env.VITE_GOOGLE_CLIENT_ID) {
      window.google.accounts.id.prompt();
    } else {
      toast({
        title: "Google Sign-In not available",
        description: "Google Sign-In is not configured",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setIsLoading(true);

    try {
      if (loginData.email && loginData.password) {
        const response = await loginUser({
          email: loginData.email,
          password: loginData.password
        });

        // Store token in localStorage
        localStorage.setItem("authToken", response.access_token);

        onAuth(response.user, response.access_token);
        toast({
          title: "Login successful",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else {
        setErrorMsg("Please enter both email and password");
        toast({
          title: "Login failed",
          description: "Please enter both email and password",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Login error:", error);
      const msg = error.response?.data?.detail || "Invalid email or password";
      setErrorMsg(msg);
      toast({
        title: "Login failed",
        description: msg,
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
    setErrorMsg("");
    setIsLoading(true);

    try {
      if (registerData.name && registerData.email && registerData.password) {
        if (registerData.password !== registerData.confirmPassword) {
          const msg = "Passwords do not match";
          setErrorMsg(msg);
          toast({
            title: "Registration failed",
            description: msg,
            status: "error",
            duration: 3000,
            isClosable: true,
          });
          setIsLoading(false);
          return;
        }

        await registerUser({
          name: registerData.name,
          email: registerData.email,
          password: registerData.password
        });

        // Show "check your email" state
        setRegistrationEmail(registerData.email);
        setActiveView("emailSent");
        toast({
          title: "Account created!",
          description: "Please check your email to verify your account.",
          status: "success",
          duration: 6000,
          isClosable: true,
        });
      } else {
        const msg = "Please fill in all fields";
        setErrorMsg(msg);
        toast({
          title: "Registration failed",
          description: msg,
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Registration error:", error);
      const msg = error.response?.data?.detail || "Registration failed. Please try again.";
      setErrorMsg(msg);
      toast({
        title: "Registration failed",
        description: msg,
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (!registrationEmail) return;
    try {
      await resendConfirmation(registrationEmail);
      toast({
        title: "Email resent",
        description: "If your account needs confirmation, a new email has been sent.",
        status: "info",
        duration: 4000,
        isClosable: true,
      });
    } catch {
      toast({
        title: "Could not resend",
        description: "Please try again in a moment.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // "Check your email" screen shown after successful registration
  if (activeView === "emailSent") {
    return (
      <div className="login-wrapper">
        <div className="login-card">
          <div className="login-logo">🤖 My Anybot</div>
          <h2>📧 Check Your Email</h2>
          <p className="login-sub">
            We sent a confirmation link to <strong>{registrationEmail}</strong>.
            Click the link to activate your account, then sign in.
          </p>
          <p className="login-sub" style={{ fontSize: "13px", marginTop: "-15px" }}>
            Didn't receive it? Check your spam folder or resend.
          </p>
          <button
            className="login-btn"
            onClick={handleResendConfirmation}
            style={{ marginBottom: "12px" }}
          >
            Resend Confirmation Email
          </button>
          <button
            className="login-btn"
            style={{ background: "transparent", color: "#64748b", boxShadow: "none", border: "1px solid #e2e8f0" }}
            onClick={() => { setRegistrationEmail(null); setActiveView("login"); }}
          >
            Back to Sign In
          </button>
          <p className="secure-text">🔒 Your data is securely encrypted</p>
        </div>
      </div>
    );
  }

  // Login view
  if (activeView === "login") {
    return (
      <div className="login-wrapper">
        <div className="login-card">

          {/* LOGO */}
          <div className="login-logo">🤖 My Anybot</div>

          <h2>Welcome Back <span className="robot">🤖</span></h2>

          <p className="login-sub">Login to continue to your robotics console</p>

          {errorMsg && (
            <p style={{ color: "#ef4444", fontSize: "13px", textAlign: "center", marginBottom: "10px" }}>
              {errorMsg}
            </p>
          )}

          <form onSubmit={handleLogin}>

            {/* EMAIL */}
            <div className="input-box">
              <Mail size={18} />
              <input
                type="email"
                placeholder="Enter your email"
                required
                value={loginData.email}
                onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
              />
            </div>

            {/* PASSWORD */}
            <div className="input-box">
              <Lock size={18} />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                required
                minLength={6}
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
              />
              <button
                type="button"
                className="eye-btn"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            {/* FORGOT PASSWORD */}
            <p className="forgot-pass">
              {onForgotPassword && (
                <button
                  type="button"
                  style={{ background: "none", border: "none", cursor: "pointer", color: "#4f46e5", fontSize: "13px", padding: 0 }}
                  onClick={onForgotPassword}
                >
                  Forgot password?
                </button>
              )}
            </p>

            {/* LOGIN BUTTON */}
            <button className="login-btn" disabled={isLoading}>
              {isLoading ? "Signing In..." : "Continue to Robotics Console"}
            </button>

          </form>

          {/* DIVIDER */}
          <div className="login-divider">
            <span></span>
            <p>or</p>
            <span></span>
          </div>

          {/* SOCIAL LOGIN */}
          <div className="social-buttons">

            <button className="social-btn" onClick={handleGoogleSignIn} disabled={isLoading}>
              <FcGoogle size={18} />
              Continue with Google
            </button>

            <button className="social-btn" disabled>
              <Github size={18} />
              Continue with GitHub
            </button>

          </div>

          {/* CREATE ACCOUNT */}
          <p className="create-account">
            New to Anybot?{" "}
            <button
              type="button"
              style={{ background: "none", border: "none", cursor: "pointer", color: "#4f46e5", fontWeight: 600, fontSize: "inherit", padding: 0 }}
              onClick={() => { setErrorMsg(""); setActiveView("register"); }}
            >
              Create Account
            </button>
          </p>

          {/* BACK TO HOME */}
          <p className="create-account" style={{ marginTop: "8px" }}>
            <button
              type="button"
              style={{ background: "none", border: "none", cursor: "pointer", color: "#64748b", fontSize: "13px", padding: 0 }}
              onClick={onBack}
            >
              ← Back to Home
            </button>
          </p>

          {/* SECURITY MESSAGE */}
          <p className="secure-text">🔒 Your data is securely encrypted</p>

        </div>
      </div>
    );
  }

  // Register view
  return (
    <div className="login-wrapper">
      <div className="login-card">

        {/* LOGO */}
        <div className="login-logo">🤖 My Anybot</div>

        <h2>Create Your Account 🚀</h2>

        <p className="login-sub">Start your robotics journey with My Anybot</p>

        {errorMsg && (
          <p style={{ color: "#ef4444", fontSize: "13px", textAlign: "center", marginBottom: "10px" }}>
            {errorMsg}
          </p>
        )}

        <form onSubmit={handleRegister}>

          {/* NAME */}
          <div className="input-box">
            <User size={18} />
            <input
              type="text"
              placeholder="Enter your full name"
              required
              value={registerData.name}
              onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
            />
          </div>

          {/* EMAIL */}
          <div className="input-box">
            <Mail size={18} />
            <input
              type="email"
              placeholder="Enter your email"
              required
              value={registerData.email}
              onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
            />
          </div>

          {/* PASSWORD */}
          <div className="input-box">
            <Lock size={18} />
            <input
              type={showRegPassword ? "text" : "password"}
              placeholder="Create a password"
              required
              minLength={6}
              value={registerData.password}
              onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
            />
            <button
              type="button"
              className="eye-btn"
              onClick={() => setShowRegPassword(!showRegPassword)}
            >
              {showRegPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* CONFIRM PASSWORD */}
          <div className="input-box">
            <Lock size={18} />
            <input
              type={showRegPassword ? "text" : "password"}
              placeholder="Confirm your password"
              required
              minLength={6}
              value={registerData.confirmPassword}
              onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
            />
          </div>

          <button type="submit" className="login-btn" disabled={isLoading}>
            {isLoading ? "Creating Account..." : "Create Account"}
          </button>

        </form>

        {/* DIVIDER */}
        <div className="login-divider">
          <span></span>
          <p>or</p>
          <span></span>
        </div>

        {/* SOCIAL SIGNUP */}
        <div className="social-buttons">

          <button type="button" className="social-btn" onClick={handleGoogleSignIn} disabled={isLoading}>
            <FcGoogle size={18} />
            Sign up with Google
          </button>

          <button type="button" className="social-btn" disabled>
            <Github size={18} />
            Sign up with GitHub
          </button>

        </div>

        {/* ALREADY HAVE ACCOUNT */}
        <p className="create-account">
          Already have an account?{" "}
          <button
            type="button"
            style={{ background: "none", border: "none", cursor: "pointer", color: "#4f46e5", fontWeight: 600, fontSize: "inherit", padding: 0 }}
            onClick={() => { setErrorMsg(""); setActiveView("login"); }}
          >
            Login
          </button>
        </p>

        {/* SECURITY MESSAGE */}
        <p className="secure-text">🔒 Your data is securely encrypted</p>

      </div>
    </div>
  );
};

export default AuthPage;
