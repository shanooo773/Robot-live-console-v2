import { useState, useEffect } from "react";
import { Box } from "@chakra-ui/react";
import LandingPage from "./components/LandingPage";
import AuthPage from "./components/AuthPage";
import BookingPage from "./components/BookingPage";
import NeonRobotConsole from "./components/NeonRobotConsole";
import AdminDashboard from "./components/AdminDashboard";
import ForgotPasswordPage from "./components/ForgotPasswordPage";
import ResetPasswordPage from "./components/ResetPasswordPage";
import VerifyEmailPage from "./components/VerifyEmailPage";
import { getCurrentUser } from "./api";

function App() {
  const [currentPage, setCurrentPage] = useState("landing"); // landing, auth, booking, editor, admin, forgotPassword, resetPassword, verifyEmail
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [resetToken, setResetToken] = useState(null);
  const [verifyToken, setVerifyToken] = useState(null);

  useEffect(() => {
    // Check for special tokens in URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const path = window.location.pathname;

    // Email verification link: /verify-email?token=...
    if (path === '/verify-email' && token) {
      setVerifyToken(token);
      setCurrentPage("verifyEmail");
      return;
    }

    // Password reset link: /reset-password?token=...
    if (path === '/reset-password' && token) {
      setResetToken(token);
      setCurrentPage("resetPassword");
      return;
    }

    // Legacy: token in query string on root path (old reset-password flow)
    if (!path.startsWith('/verify-email') && token) {
      setResetToken(token);
      setCurrentPage("resetPassword");
      return;
    }

    // Check for existing authenticated session
    const authTokenStored = localStorage.getItem('authToken');
    if (authTokenStored) {
      getCurrentUser(authTokenStored)
        .then(userData => {
          setUser(userData);
          setAuthToken(authTokenStored);
          setCurrentPage("booking");
        })
        .catch(error => {
          console.error('Token validation failed:', error);
          localStorage.removeItem('authToken');
        });
    }
  }, []);

  const handleAuth = (userData, token) => {
    setUser(userData);
    setAuthToken(token);
    setCurrentPage("booking");
  };

  const handleBooking = (slot) => {
    setSelectedSlot(slot);
    setCurrentPage("editor");
  };

  const handleLogout = () => {
    setUser(null);
    setAuthToken(null);
    setSelectedSlot(null);
    localStorage.removeItem('authToken');
    setCurrentPage("landing");
  };

  const handleAdminAccess = () => {
    setCurrentPage("admin");
  };

  return (
    <Box 
      minH="100vh" 
      bg="#0f0a19" 
      color="gray.500"
      css={{ 
        scrollBehavior: 'smooth',
        overflowX: 'hidden',
        overflowY: 'auto'
      }}
    >
      {currentPage === "landing" && (
        <LandingPage onGetStarted={() => setCurrentPage("auth")} />
      )}
      {currentPage === "auth" && (
        <AuthPage 
          onAuth={handleAuth} 
          onBack={() => setCurrentPage("landing")}
          onForgotPassword={() => setCurrentPage("forgotPassword")}
        />
      )}
      {currentPage === "forgotPassword" && (
        <ForgotPasswordPage 
          onBack={() => setCurrentPage("auth")}
        />
      )}
      {currentPage === "resetPassword" && (
        <ResetPasswordPage 
          resetToken={resetToken}
          onSuccess={() => {
            setResetToken(null);
            setCurrentPage("auth");
          }}
        />
      )}
      {currentPage === "verifyEmail" && (
        <VerifyEmailPage
          token={verifyToken}
          onSuccess={() => {
            setVerifyToken(null);
            setCurrentPage("auth");
          }}
        />
      )}
      {currentPage === "booking" && (
        <BookingPage 
          user={user}
          authToken={authToken}
          onBooking={handleBooking} 
          onLogout={handleLogout}
          onAdminAccess={user?.role === 'admin' ? handleAdminAccess : null}
        />
      )}
      {currentPage === "editor" && (
        <NeonRobotConsole 
          user={user} 
          slot={selectedSlot} 
          authToken={authToken}
          onBack={() => setCurrentPage("booking")}
          onLogout={handleLogout}
        />
      )}
      {currentPage === "admin" && user?.role === 'admin' && (
        <AdminDashboard
          user={user}
          authToken={authToken}
          onBack={() => setCurrentPage("booking")}
          onLogout={handleLogout}
        />
      )}
    </Box>
  );
}

export default App;
