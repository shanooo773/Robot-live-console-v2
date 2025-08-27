import axios from "axios";

// Backend API (authentication, booking, and video serving)
const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

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

export const getBookingSchedule = async (startDate, endDate) => {
  const response = await API.get(`/bookings/schedule?start_date=${startDate}&end_date=${endDate}`);
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
