import { useState, useEffect } from "react";
import { Box } from "@chakra-ui/react";
import LandingPage from "./components/LandingPage";
import AuthPage from "./components/AuthPage";
import BookingPage from "./components/BookingPage";
import NeonRobotConsole from "./components/NeonRobotConsole";
import AdminDashboard from "./components/AdminDashboard";
import { getCurrentUser } from "./api";

function App() {
  const [currentPage, setCurrentPage] = useState("landing"); // landing, auth, booking, editor, admin
  const [user, setUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('authToken');
    const isDemoUser = localStorage.getItem('isDemoUser');
    const isDemoAdmin = localStorage.getItem('isDemoAdmin');
    const isDemoMode = localStorage.getItem('isDemoMode');
    
    // Handle demo sessions
    if (isDemoUser || isDemoAdmin || isDemoMode) {
      const demoUser = isDemoUser ? {
        username: "demo_user",
        name: "Demo User", 
        email: "demo.user@example.com",
        role: "user",
        isDemoUser: true,
      } : isDemoAdmin ? {
        username: "demo_admin",
        name: "Demo Admin",
        email: "demo.admin@example.com", 
        role: "admin",
        isDemoAdmin: true,
      } : {
        id: "demo",
        name: "Demo User",
        email: "demo@example.com",
        role: "user",
        isDemoMode: true
      };
      
      setUser(demoUser);
      setCurrentPage("booking");
      return;
    }
    
    // Handle regular token-based sessions
    if (token) {
      getCurrentUser(token)
        .then(userData => {
          setUser(userData);
          setAuthToken(token);
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
    // Clear all session storage including demo flags
    localStorage.removeItem('authToken');
    localStorage.removeItem('isDemoUser');
    localStorage.removeItem('isDemoAdmin');
    localStorage.removeItem('isDummy');
    localStorage.removeItem('isDemoMode');
    setCurrentPage("landing");
  };

  const handleAdminAccess = () => {
    setCurrentPage("admin");
  };

  return (
    <Box minH="100vh" bg="#0f0a19" color="gray.500">
      {currentPage === "landing" && (
        <LandingPage onGetStarted={() => setCurrentPage("auth")} />
      )}
      {currentPage === "auth" && (
        <AuthPage onAuth={handleAuth} onBack={() => setCurrentPage("landing")} />
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
