import { useState, useEffect } from "react";
import { Box } from "@chakra-ui/react";
import LandingPage from "./components/LandingPage";
import AuthPage from "./components/AuthPage";
import Dashboard from "./components/Dashboard";
import BookingPage from "./components/BookingPage";
import NeonRobotConsole from "./components/NeonRobotConsole";
import AdminDashboard from "./components/AdminDashboard";
import CommunityPage from "./components/CommunityPage";
import DocsPage from "./components/DocsPage";
import ForgotPasswordPage from "./components/ForgotPasswordPage";
import ResetPasswordPage from "./components/ResetPasswordPage";
import VerifyEmailPage from "./components/VerifyEmailPage";
import { getCurrentUser, stopBookingContainer, stopTheiaContainer, githubLogin } from "./api";
import { startTheiaWarmup, stopTheiaWarmup } from "./utils/theiaWarmup";

function App() {
  const [currentPage, setCurrentPage] = useState("landing");
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [resetToken, setResetToken] = useState(null);
  const [verifyToken, setVerifyToken] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const path = window.location.pathname;

    if (path === '/verify-email' && token) {
      setVerifyToken(token);
      setCurrentPage("verifyEmail");
      return;
    }

    if (path === '/reset-password' && token) {
      setResetToken(token);
      setCurrentPage("resetPassword");
      return;
    }

    const code = urlParams.get('code');
    if (path === '/auth/github/callback' && code) {
      const redirectUri = `${window.location.origin}/auth/github/callback`;
      githubLogin(code, redirectUri)
        .then(result => {
          localStorage.setItem("authToken", result.access_token);
          window.history.replaceState({}, document.title, "/");
          handleAuth(result.user, result.access_token);
        })
        .catch((error) => {
          const detail = error?.response?.data?.detail || "GitHub authentication failed. Please try again.";
          setAuthError(detail);
          window.history.replaceState({}, document.title, "/");
          setCurrentPage("auth");
        });
      return;
    }

    if (!path.startsWith('/verify-email') && token) {
      setResetToken(token);
      setCurrentPage("resetPassword");
      return;
    }

    const authTokenStored = localStorage.getItem('authToken');
    if (authTokenStored) {
      getCurrentUser(authTokenStored)
        .then(userData => {
          setUser(userData);
          setAuthToken(authTokenStored);
          setCurrentPage("dashboard");
          startTheiaWarmup(authTokenStored);
        })
        .catch(() => {
          localStorage.removeItem('authToken');
        });
    }
  }, []);

  const handleAuth = (userData, token) => {
    setUser(userData);
    setAuthToken(token);
    setCurrentPage("dashboard");
    startTheiaWarmup(token);
  };

  const handleBooking = (slot) => {
    setSelectedSlot(slot);
    setCurrentPage("editor");
  };

  const handleLogout = async () => {
    stopTheiaWarmup();
    const token = authToken || localStorage.getItem('authToken');
    if (token) {
      try { await stopBookingContainer(token); } catch (_) { }
      try { await stopTheiaContainer(token); } catch (_) { }
    }
    setUser(null);
    setAuthToken(null);
    setSelectedSlot(null);
    localStorage.removeItem('authToken');
    setCurrentPage("landing");
  };

  const handleNavigate = (page) => {
    if (page === "editor") {
      setSelectedSlot({
        id: `code_preview_${Date.now()}`,
        robotType: 'turtlebot',
        date: new Date().toISOString().split('T')[0],
        startTime: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
        endTime: new Date(Date.now() + 1 * 60 * 60 * 1000).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }),
        bookingId: 'code_preview',
        available: true,
        bookedBy: user?.name,
        isPreview: true
      });
    }
    setCurrentPage(page);
  };

  const handleAdminAccess = () => setCurrentPage("admin");

  const sharedProps = {
    user,
    authToken,
    onLogout: handleLogout,
    onNavigate: handleNavigate,
    onAdminAccess: user?.role === 'admin' ? handleAdminAccess : null,
  };

  return (
    <Box
      minH="100vh"
      bg="#F0F4FF"
      color="gray.800"
      css={{ scrollBehavior: 'smooth', overflowX: 'hidden', overflowY: 'auto' }}
    >
      {currentPage === "landing" && (
        <LandingPage
          onLogin={() => { setAuthMode("login"); setCurrentPage("auth"); }}
          onSignup={() => { setAuthMode("register"); setCurrentPage("auth"); }}
        />
      )}

      {currentPage === "auth" && (
        <AuthPage
          mode={authMode}
          oauthError={authError}
          onAuth={handleAuth}
          onBack={() => setCurrentPage("landing")}
          onForgotPassword={() => setCurrentPage("forgotPassword")}
        />
      )}

      {currentPage === "forgotPassword" && (
        <ForgotPasswordPage onBack={() => setCurrentPage("auth")} />
      )}

      {currentPage === "resetPassword" && (
        <ResetPasswordPage
          resetToken={resetToken}
          onSuccess={() => { setResetToken(null); setCurrentPage("auth"); }}
        />
      )}

      {currentPage === "verifyEmail" && (
        <VerifyEmailPage
          token={verifyToken}
          onSuccess={() => { setVerifyToken(null); setCurrentPage("auth"); }}
        />
      )}

      {currentPage === "dashboard" && user && (
        <Dashboard
          {...sharedProps}
          onBooking={handleBooking}
        />
      )}

      {currentPage === "booking" && user && (
        <BookingPage
          {...sharedProps}
          onBooking={handleBooking}
        />
      )}

      {currentPage === "editor" && (
        <NeonRobotConsole
          user={user}
          slot={selectedSlot}
          authToken={authToken}
          onBack={() => setCurrentPage("dashboard")}
          onLogout={handleLogout}
        />
      )}

      {currentPage === "community" && user && (
        <CommunityPage
          {...sharedProps}
        />
      )}

      {currentPage === "docs" && user && (
        <DocsPage
          {...sharedProps}
        />
      )}

      {currentPage === "admin" && user?.role === 'admin' && (
        <AdminDashboard
          user={user}
          authToken={authToken}
          onBack={() => setCurrentPage("dashboard")}
          onLogout={handleLogout}
        />
      )}
    </Box>
  );
}

export default App;
