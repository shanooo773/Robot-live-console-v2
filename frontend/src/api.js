import axios from "axios";

// Environment-based API URL configuration
const getApiUrl = () => {
  // Check for environment variable first
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Production detection
  if (import.meta.env.PROD) {
    // In production, try to use the same host with /api prefix
    return `${window.location.origin}/api`;
  }
  
  // Development fallback - use localhost for testing
  return "http://localhost:8000"
};

// Backend API (authentication, booking, and video serving)
const API = axios.create({
  baseURL: getApiUrl(),
});

// Log the API URL for debugging
console.log("API Base URL:", getApiUrl());

// Authentication API
export const registerUser = async (userData) => {
  const response = await API.post("/auth/register", userData);
  return response.data;
};

export const loginUser = async (credentials) => {
  const response = await API.post("/auth/login", credentials);
  return response.data;
};

export const getCurrentUser = async (token) => {
  const response = await API.get("/auth/me", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Booking API
export const createBooking = async (bookingData, token) => {
  const response = await API.post("/bookings", bookingData, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getUserBookings = async (token) => {
  const response = await API.get("/bookings", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getMyActiveBookings = async (token) => {
  const response = await API.get("/my-bookings", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getBookingSchedule = async (startDate, endDate) => {
  const response = await API.get(`/bookings/schedule?start_date=${startDate}&end_date=${endDate}`);
  return response.data;
};

export const getAvailableSlots = async (date, robotType, token) => {
  const response = await API.get(`/bookings/available-slots?date=${date}&robot_type=${robotType}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Admin API
export const getAllUsers = async (token) => {
  const response = await API.get("/admin/users", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getAllBookings = async (token) => {
  const response = await API.get("/bookings/all", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getAdminStats = async (token) => {
  const response = await API.get("/admin/stats", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const updateBookingStatus = async (bookingId, status, token) => {
  const response = await API.put(`/bookings/${bookingId}`, { status }, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const deleteBooking = async (bookingId, token) => {
  const response = await API.delete(`/bookings/${bookingId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Video and Access Control API
export const getVideo = async (robotType, token) => {
  const response = await API.get(`/videos/${robotType}`, {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  });
  return response.data;
};

export const checkAccess = async (token) => {
  const response = await API.get("/access/check", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getAvailableVideos = async (token) => {
  const response = await API.get("/videos/available", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Robot information API
export const getAvailableRobots = async () => {
  const response = await API.get("/robots");
  return response.data;
};

// Health check API
export const getSystemHealth = async () => {
  const response = await API.get("/health");
  return response.data;
};

export const getServiceStatus = async () => {
  const response = await API.get("/health/services");
  return response.data;
};

export const getAvailableFeatures = async () => {
  const response = await API.get("/health/features");
  return response.data;
};

// Message API
export const submitContactMessage = async (messageData) => {
  const response = await API.post("/messages", messageData);
  return response.data;
};

export const getAllMessages = async (token) => {
  const response = await API.get("/messages", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const updateMessageStatus = async (messageId, status, token) => {
  const response = await API.put(`/messages/${messageId}/status`, { status }, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const deleteMessage = async (messageId, token) => {
  const response = await API.delete(`/messages/${messageId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Announcement API
export const createAnnouncement = async (announcementData, token) => {
  const response = await API.post("/announcements", announcementData, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getAllAnnouncements = async (token) => {
  const response = await API.get("/announcements", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getActiveAnnouncements = async () => {
  const response = await API.get("/announcements/active");
  return response.data;
};

export const updateAnnouncement = async (announcementId, announcementData, token) => {
  const response = await API.put(`/announcements/${announcementId}`, announcementData, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const deleteAnnouncement = async (announcementId, token) => {
  const response = await API.delete(`/announcements/${announcementId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Robot Code Execution API (to be implemented in backend)
export const executeRobotCode = async (sourceCode, robotType = null, filename = null) => {
  // Get token from localStorage if available
  const token = localStorage.getItem('authToken');
  
  try {
    const response = await API.post("/robot/execute", {
      code: sourceCode,
      robot_type: robotType, // Can be null to use first active booking
      language: "python", // Default to Python, could be dynamic
      filename: filename
    }, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    // Handle API errors properly
    if (error.response) {
      throw new Error(error.response.data.detail || 'Robot execution failed');
    } else {
      throw new Error('Network error: Unable to connect to robot API');
    }
  }
};

// WebRTC API - for real-time video streaming (updated for direct robot connection)
export const getWebRTCConfig = async (token) => {
  const response = await API.get("/webrtc/config", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const getRobotWebRTCUrl = async (robotType, token) => {
  const response = await API.post("/webrtc/offer", {
    robot_type: robotType,
    sdp: "dummy",  // Backend now returns WebRTC URL instead of processing offer
    type: "offer"
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Direct robot WebRTC signaling functions
export const sendOfferToRobot = async (webrtcUrl, offer) => {
  const response = await fetch(`${webrtcUrl}/offer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sdp: offer.sdp,
      type: offer.type
    })
  });
  
  if (!response.ok) {
    throw new Error(`Robot WebRTC offer failed: ${response.statusText}`);
  }
  
  return await response.json();
};

export const sendICECandidateToRobot = async (webrtcUrl, peerId, candidate) => {
  const response = await fetch(`${webrtcUrl}/ice-candidate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      peer_id: peerId,
      candidate: candidate
    })
  });
  
  if (!response.ok) {
    throw new Error(`Robot ICE candidate failed: ${response.statusText}`);
  }
  
  return await response.json();
};

// Robot Registry Admin API
export const getAllRobots = async (token) => {
  const response = await API.get("/admin/robots", {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const createRobot = async (robotData, token) => {
  const response = await API.post("/admin/robots", robotData, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const updateRobot = async (robotId, robotData, token) => {
  const response = await API.put(`/admin/robots/${robotId}`, robotData, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const deleteRobot = async (robotId, token) => {
  const response = await API.delete(`/admin/robots/${robotId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};
