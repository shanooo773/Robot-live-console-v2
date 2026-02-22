import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Container,
  Card,
  CardBody,
  CardHeader,
  SimpleGrid,
  Badge,
  Avatar,
  Divider,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  Switch,
  IconButton,
} from "@chakra-ui/react";
import { useState, useEffect, useRef } from "react";
import { 
  getAllUsers, 
  getAllBookings, 
  getAdminStats, 
  updateBookingStatus, 
  deleteBooking, 
  getAllMessages, 
  updateMessageStatus, 
  deleteMessage,
  getAllAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  getAllRobots,
  createRobot,
  updateRobot,
  deleteRobot,
  deleteUser,
  updateUserRole,
  changeAdminPassword,
  ensureArray
} from "../api";
import { ChevronDownIcon, DeleteIcon, EditIcon, AddIcon, ViewIcon } from "@chakra-ui/icons";

const AdminDashboard = ({ user, authToken, onBack, onLogout }) => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [messages, setMessages] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [robots, setRobots] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [selectedAnnouncement, setSelectedAnnouncement] = useState(null);
  const [selectedRobot, setSelectedRobot] = useState(null);
  const [isAnnouncementModalOpen, setIsAnnouncementModalOpen] = useState(false);
  const [isRobotModalOpen, setIsRobotModalOpen] = useState(false);
  const [announcementForm, setAnnouncementForm] = useState({
    title: "",
    content: "",
    priority: "normal",
    is_active: true
  });
  const [robotForm, setRobotForm] = useState({
    name: "",
    type: "",
    webrtc_url: "",
    rtsp_url: "",
    upload_endpoint: ""
  });
  const [isEditingAnnouncement, setIsEditingAnnouncement] = useState(false);
  const [isEditingRobot, setIsEditingRobot] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isUserDeleteModalOpen, setIsUserDeleteModalOpen] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const toast = useToast();
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { 
    isOpen: isMessageOpen, 
    onOpen: onMessageOpen, 
    onClose: onMessageClose 
  } = useDisclosure();
  const cancelRef = useRef();

  useEffect(() => {
    loadDashboardData();
  }, [authToken]);

  const loadDashboardData = async () => {
    // Prevent multiple concurrent calls
    if (isLoading) return;
    
    setIsLoading(true);
    setHasError(false);
    
    try {
      const [statsData, usersData, bookingsData, messagesData, announcementsData, robotsData] = await Promise.all([
        getAdminStats(authToken),
        getAllUsers(authToken),
        getAllBookings(authToken),
        getAllMessages(authToken),
        getAllAnnouncements(authToken),
        getAllRobots(authToken)
      ]);
    setStats(statsData || null);
    setUsers(ensureArray(usersData));
    setBookings(ensureArray(bookingsData));
    setMessages(ensureArray(messagesData));
    setAnnouncements(ensureArray(announcementsData));
    setRobots(ensureArray(robotsData));
  } catch (error) {
    console.error("Failed to load dashboard data:", error);
    setHasError(true);
    // Ensure state holds arrays even on error
    setStats(null);
    setUsers([]);
    setBookings([]);
    setMessages([]);
    setAnnouncements([]);
    setRobots([]);  
      // Use setTimeout to ensure toast appears after state updates
      setTimeout(() => {
        toast({
          title: "Error loading dashboard",
          description: "Failed to load admin dashboard data",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }, 100);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateBookingStatus = async (bookingId, newStatus) => {
    try {
      await updateBookingStatus(bookingId, newStatus, authToken);
      await loadDashboardData();
      toast({
        title: "Booking updated",
        description: `Booking status changed to ${newStatus}`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error updating booking:', error);
      toast({
        title: "Update failed",
        description: "Failed to update booking status",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDeleteBooking = async () => {
    try {
      await deleteBooking(selectedBooking.id, authToken);
      await loadDashboardData();
      onClose();
      toast({
        title: "Booking deleted",
        description: "Booking has been successfully deleted",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error deleting booking:', error);
      toast({
        title: "Delete failed",
        description: "Failed to delete booking",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const confirmDeleteBooking = (booking) => {
    setSelectedBooking(booking);
    onOpen();
  };

  // User management handlers
  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    
    try {
      await deleteUser(selectedUser.id, authToken);
      await loadDashboardData();
      setIsUserDeleteModalOpen(false);
      setSelectedUser(null);
      toast({
        title: "User deleted",
        description: "User and their workspace have been removed",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error deleting user:', error);
      toast({
        title: "Delete failed",
        description: error.response?.data?.detail || "Could not delete user",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handlePromoteUser = async (userId, newRole) => {
    try {
      await updateUserRole(userId, newRole, authToken);
      await loadDashboardData();
      toast({
        title: newRole === 'admin' 
          ? 'User promoted to admin' 
          : 'User role changed to user',
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error updating user role:', error);
      toast({
        title: "Role update failed",
        description: error.response?.data?.detail || "Could not update user role",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast({
        title: "Passwords do not match",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      await changeAdminPassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      }, authToken);
      
      toast({
        title: "Password updated successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      
      setIsPasswordModalOpen(false);
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      console.error('Error changing password:', error);
      toast({
        title: "Password change failed",
        description: error.response?.data?.detail || "Could not change password",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const confirmDeleteUser = (user) => {
    setSelectedUser(user);
    setIsUserDeleteModalOpen(true);
  };

  // Message handlers
  const handleUpdateMessageStatus = async (messageId, newStatus) => {
    try {
      await updateMessageStatus(messageId, newStatus, authToken);
      await loadDashboardData();
      toast({
        title: "Message updated",
        description: `Message marked as ${newStatus}`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error updating message:', error);
      toast({
        title: "Update failed",
        description: "Failed to update message status",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await deleteMessage(messageId, authToken);
      await loadDashboardData();
      toast({
        title: "Message deleted",
        description: "Message has been successfully deleted",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error deleting message:', error);
      toast({
        title: "Delete failed",
        description: "Failed to delete message",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const viewMessage = (message) => {
    setSelectedMessage(message);
    onMessageOpen();
  };

  // Announcement handlers
  const openAnnouncementModal = (announcement = null) => {
    if (announcement) {
      setAnnouncementForm({
        title: announcement.title,
        content: announcement.content,
        priority: announcement.priority,
        is_active: announcement.is_active
      });
      setSelectedAnnouncement(announcement);
      setIsEditingAnnouncement(true);
    } else {
      setAnnouncementForm({
        title: "",
        content: "",
        priority: "normal",
        is_active: true
      });
      setSelectedAnnouncement(null);
      setIsEditingAnnouncement(false);
    }
    setIsAnnouncementModalOpen(true);
  };

  const handleAnnouncementSubmit = async () => {
    try {
      if (isEditingAnnouncement && selectedAnnouncement) {
        await updateAnnouncement(selectedAnnouncement.id, announcementForm, authToken);
        toast({
          title: "Announcement updated",
          description: "Announcement has been updated successfully",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else {
        await createAnnouncement(announcementForm, authToken);
        toast({
          title: "Announcement created",
          description: "New announcement has been created successfully",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      }
      setIsAnnouncementModalOpen(false);
      await loadDashboardData();
    } catch (error) {
      console.error('Error saving announcement:', error);
      toast({
        title: "Save failed",
        description: "Failed to save announcement",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDeleteAnnouncement = async (announcementId) => {
    try {
      await deleteAnnouncement(announcementId, authToken);
      await loadDashboardData();
      toast({
        title: "Announcement deleted",
        description: "Announcement has been successfully deleted",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error deleting announcement:', error);
      toast({
        title: "Delete failed",
        description: "Failed to delete announcement",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Robot CRUD Functions
  const handleCreateRobot = async () => {
    // Client-side validation for rtsp_url
    if (robotForm.rtsp_url && robotForm.rtsp_url.trim() && !robotForm.rtsp_url.trim().startsWith('rtsp://')) {
      toast({
        title: "Validation Error",
        description: "RTSP URL must start with 'rtsp://'",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      await createRobot(robotForm, authToken);
      await loadDashboardData();
      setIsRobotModalOpen(false);
      setRobotForm({ name: "", type: "", webrtc_url: "", rtsp_url: "", upload_endpoint: "" });
      setIsEditingRobot(false);
      toast({
        title: "Robot created",
        description: "Robot has been successfully created",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error creating robot:', error);
      toast({
        title: "Create failed",
        description: "Failed to create robot",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleUpdateRobot = async () => {
    // Client-side validation for rtsp_url
    if (robotForm.rtsp_url && robotForm.rtsp_url.trim() && !robotForm.rtsp_url.trim().startsWith('rtsp://')) {
      toast({
        title: "Validation Error",
        description: "RTSP URL must start with 'rtsp://'",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      await updateRobot(selectedRobot.id, robotForm, authToken);
      await loadDashboardData();
      setIsRobotModalOpen(false);
      setRobotForm({ name: "", type: "", webrtc_url: "", rtsp_url: "", upload_endpoint: "" });
      setSelectedRobot(null);
      setIsEditingRobot(false);
      toast({
        title: "Robot updated",
        description: "Robot has been successfully updated",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error updating robot:', error);
      toast({
        title: "Update failed",
        description: "Failed to update robot",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDeleteRobot = async (robotId) => {
    try {
      await deleteRobot(robotId, authToken);
      await loadDashboardData();
      toast({
        title: "Robot deleted",
        description: "Robot has been successfully deleted",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error deleting robot:', error);
      toast({
        title: "Delete failed",
        description: "Failed to delete robot",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const openRobotModal = (robot = null) => {
    if (robot) {
      setSelectedRobot(robot);
      setRobotForm({
        name: robot.name,
        type: robot.type,
        webrtc_url: robot.webrtc_url || "",
        rtsp_url: robot.rtsp_url || "",
        upload_endpoint: robot.upload_endpoint || ""
      });
      setIsEditingRobot(true);
    } else {
      setSelectedRobot(null);
      setRobotForm({ name: "", type: "", webrtc_url: "", rtsp_url: "", upload_endpoint: "" });
      setIsEditingRobot(false);
    }
    setIsRobotModalOpen(true);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'cancelled':
        return 'red';
      case 'completed':
        return 'blue';
      default:
        return 'gray';
    }
  };

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8}>
        {/* Header */}
        <HStack w="full" justify="space-between">
          <VStack align="start" spacing={1}>
            <Text fontSize="3xl" fontWeight="bold" color="white">
              Admin Dashboard
            </Text>
            <HStack>
              <Avatar size="sm" name={user.name} />
              <Text color="gray.300">Welcome, {user.name}</Text>
              <Badge colorScheme="purple">Admin</Badge>
              {(user?.isDemoAdmin || localStorage.getItem('isDemoAdmin')) && (
                <Badge colorScheme="orange">DEMO MODE</Badge>
              )}
            </HStack>
          </VStack>
          <HStack spacing={3}>
            <Button variant="ghost" onClick={onBack} color="gray.400">
              ← Back to Booking
            </Button>
            <Button variant="ghost" onClick={onLogout} color="gray.400">
              Logout
            </Button>
          </HStack>
        </HStack>

        {/* Statistics Cards */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6} w="full">
          {isLoading ? (
            // Loading state for statistics
            Array.from({ length: 6 }).map((_, index) => (
              <Card key={index} bg="gray.800" border="1px solid" borderColor="gray.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="gray.400">Loading...</StatLabel>
                    <StatNumber color="gray.400" fontSize="3xl">--</StatNumber>
                    <StatHelpText color="gray.500">Please wait</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            ))
          ) : hasError ? (
            // Error state for statistics
            <Card bg="red.900" border="1px solid" borderColor="red.600" gridColumn="1 / -1">
              <CardBody textAlign="center">
                <Text color="red.200" fontSize="lg" mb={2}>❌ Failed to Load Dashboard Statistics</Text>
                <Text color="red.300" fontSize="sm">Unable to connect to the server. Please check your connection and try again.</Text>
                <Button 
                  mt={4} 
                  colorScheme="red" 
                  variant="outline" 
                  onClick={loadDashboardData}
                  size="sm"
                >
                  Retry
                </Button>
              </CardBody>
            </Card>
          ) : stats ? (
            // Success state - show actual statistics
            <>
              <Card bg="blue.900" border="1px solid" borderColor="blue.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="blue.100">Total Users</StatLabel>
                    <StatNumber color="white" fontSize="3xl">{stats.total_users}</StatNumber>
                    <StatHelpText color="blue.200">Registered users</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card bg="green.900" border="1px solid" borderColor="green.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="green.100">Total Bookings</StatLabel>
                    <StatNumber color="white" fontSize="3xl">{stats.total_bookings}</StatNumber>
                    <StatHelpText color="green.200">All time bookings</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card bg="purple.900" border="1px solid" borderColor="purple.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="purple.100">Active Bookings</StatLabel>
                    <StatNumber color="white" fontSize="3xl">{stats.active_bookings}</StatNumber>
                    <StatHelpText color="purple.200">Currently active</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card bg="cyan.900" border="1px solid" borderColor="cyan.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="cyan.100">Messages</StatLabel>
                    <StatNumber color="white" fontSize="3xl">{stats.total_messages || 0}</StatNumber>
                    <StatHelpText color="cyan.200">{stats.unread_messages || 0} unread</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card bg="teal.900" border="1px solid" borderColor="teal.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="teal.100">Announcements</StatLabel>
                    <StatNumber color="white" fontSize="3xl">{stats.total_announcements || 0}</StatNumber>
                    <StatHelpText color="teal.200">{stats.active_announcements || 0} active</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card bg="pink.900" border="1px solid" borderColor="pink.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="pink.100">Robots</StatLabel>
                    <StatNumber color="white" fontSize="3xl">{stats.total_robots || 0}</StatNumber>
                    <StatHelpText color="pink.200">In registry</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>

              <Card bg="orange.900" border="1px solid" borderColor="orange.600">
                <CardBody>
                  <Stat>
                    <StatLabel color="orange.100">Utilization</StatLabel>
                    <StatNumber color="white" fontSize="3xl">
                      {stats.total_bookings > 0 ? Math.round((stats.active_bookings / stats.total_bookings) * 100) : 0}%
                    </StatNumber>
                    <StatHelpText color="orange.200">Active rate</StatHelpText>
                  </Stat>
                </CardBody>
              </Card>
            </>
          ) : null}
        </SimpleGrid>

        {/* User Management */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between">
              <Text fontSize="lg" fontWeight="bold" color="white">
                User Management
              </Text>
              <Button
                colorScheme="blue"
                size="sm"
                onClick={() => setIsPasswordModalOpen(true)}
              >
                Change My Password
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th color="gray.300">ID</Th>
                    <Th color="gray.300">Name</Th>
                    <Th color="gray.300">Email</Th>
                    <Th color="gray.300">Role</Th>
                    <Th color="gray.300">Active</Th>
                    <Th color="gray.300">Last Login</Th>
                    <Th color="gray.300">Login Count</Th>
                    <Th color="gray.300">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {isLoading ? (
                    <Tr>
                      <Td colSpan={8} textAlign="center" color="gray.400" py={8}>
                        Loading users...
                      </Td>
                    </Tr>
                  ) : hasError ? (
                    <Tr>
                      <Td colSpan={8} textAlign="center" color="red.400" py={8}>
                        ❌ Failed to load users data
                      </Td>
                    </Tr>
                  ) : users.length > 0 ? (
                    users.map((userData) => (
                      <Tr key={userData.id}>
                        <Td color="white">{userData.id}</Td>
                        <Td color="white">
                          <HStack>
                            <Avatar size="xs" name={userData.name} />
                            <Text>{userData.name}</Text>
                          </HStack>
                        </Td>
                        <Td color="gray.300">{userData.email}</Td>
                        <Td>
                          <Badge colorScheme={userData.role === 'admin' ? 'purple' : 'gray'}>
                            {userData.role}
                          </Badge>
                        </Td>
                        <Td>
                          <Badge colorScheme={userData.is_active ? 'green' : 'red'}>
                            {userData.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </Td>
                        <Td color="gray.400">
                          {userData.last_login ? new Date(userData.last_login).toLocaleDateString() : 'Never'}
                        </Td>
                        <Td color="gray.400">{userData.login_count || 0}</Td>
                        <Td>
                          <HStack spacing={2}>
                            {userData.role !== 'admin' && (
                              <Button
                                size="xs"
                                colorScheme="green"
                                onClick={() => handlePromoteUser(userData.id, 'admin')}
                              >
                                Promote
                              </Button>
                            )}
                            {userData.role === 'admin' && (
                              <Button
                                size="xs"
                                colorScheme="orange"
                                onClick={() => handlePromoteUser(userData.id, 'user')}
                              >
                                Demote
                              </Button>
                            )}
                            <Button
                              size="xs"
                              colorScheme="red"
                              onClick={() => confirmDeleteUser(userData)}
                            >
                              Delete
                            </Button>
                          </HStack>
                        </Td>
                      </Tr>
                    ))
                  ) : (
                    <Tr>
                      <Td colSpan={8} textAlign="center" color="gray.400" py={8}>
                        No users found
                      </Td>
                    </Tr>
                  )}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>

        {/* All Bookings */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <Text fontSize="lg" fontWeight="bold" color="white">
              All Bookings
            </Text>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th color="gray.300">User</Th>
                    <Th color="gray.300">Robot Type</Th>
                    <Th color="gray.300">Date</Th>
                    <Th color="gray.300">Time</Th>
                    <Th color="gray.300">Status</Th>
                    <Th color="gray.300">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {isLoading ? (
                    <Tr>
                      <Td colSpan={6} textAlign="center" color="gray.400" py={8}>
                        Loading bookings...
                      </Td>
                    </Tr>
                  ) : hasError ? (
                    <Tr>
                      <Td colSpan={6} textAlign="center" color="red.400" py={8}>
                        ❌ Failed to load bookings data
                      </Td>
                    </Tr>
                  ) : bookings.length > 0 ? (
                    bookings.map((booking) => (
                      <Tr key={booking.id}>
                        <Td color="white">
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="semibold">{booking.user_name}</Text>
                            <Text fontSize="xs" color="gray.400">{booking.user_email}</Text>
                          </VStack>
                        </Td>
                        <Td color="gray.300">
                          <Badge colorScheme="cyan">{booking.robot_type}</Badge>
                        </Td>
                        <Td color="gray.300">{formatDate(booking.date)}</Td>
                        <Td color="gray.300">{booking.start_time} - {booking.end_time}</Td>
                        <Td>
                          <Badge colorScheme={getStatusColor(booking.status)}>
                            {booking.status}
                          </Badge>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            <Menu>
                              <MenuButton as={Button} size="xs" rightIcon={<ChevronDownIcon />}>
                                Status
                              </MenuButton>
                              <MenuList>
                                <MenuItem onClick={() => handleUpdateBookingStatus(booking.id, 'active')}>
                                  Mark Active
                                </MenuItem>
                                <MenuItem onClick={() => handleUpdateBookingStatus(booking.id, 'completed')}>
                                  Mark Completed
                                </MenuItem>
                                <MenuItem onClick={() => handleUpdateBookingStatus(booking.id, 'cancelled')}>
                                  Mark Cancelled
                                </MenuItem>
                              </MenuList>
                            </Menu>
                            <Button
                              size="xs"
                              colorScheme="red"
                              onClick={() => confirmDeleteBooking(booking)}
                            >
                              Delete
                            </Button>
                          </HStack>
                        </Td>
                      </Tr>
                    ))
                  ) : (
                    <Tr>
                      <Td colSpan={6} textAlign="center" color="gray.400" py={8}>
                        No bookings found
                      </Td>
                    </Tr>
                  )}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>

        {/* Messages */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between">
              <Text fontSize="lg" fontWeight="bold" color="white">
                Contact Messages
              </Text>
              <Badge colorScheme="cyan" fontSize="sm">
                {hasError ? 0 : messages.filter(m => m.status === 'unread').length} unread
              </Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th color="gray.300">Name</Th>
                    <Th color="gray.300">Email</Th>
                    <Th color="gray.300">Status</Th>
                    <Th color="gray.300">Date</Th>
                    <Th color="gray.300">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {isLoading ? (
                    <Tr>
                      <Td colSpan={5} textAlign="center" color="gray.400" py={8}>
                        Loading messages...
                      </Td>
                    </Tr>
                  ) : hasError ? (
                    <Tr>
                      <Td colSpan={5} textAlign="center" color="red.400" py={8}>
                        ❌ Failed to load messages data
                      </Td>
                    </Tr>
                  ) : messages.length > 0 ? (
                    messages.map((message) => (
                      <Tr key={message.id}>
                        <Td color="white">{message.name}</Td>
                        <Td color="gray.300">{message.email}</Td>
                        <Td>
                          <Badge colorScheme={message.status === 'read' ? 'green' : 'orange'}>
                            {message.status}
                          </Badge>
                        </Td>
                        <Td color="gray.300">{formatDate(message.created_at)}</Td>
                        <Td>
                          <HStack spacing={2}>
                            <IconButton
                              size="xs"
                              icon={<ViewIcon />}
                              onClick={() => viewMessage(message)}
                              aria-label="View message"
                            />
                            <Menu>
                              <MenuButton as={Button} size="xs" rightIcon={<ChevronDownIcon />}>
                                Status
                              </MenuButton>
                              <MenuList>
                                <MenuItem onClick={() => handleUpdateMessageStatus(message.id, 'read')}>
                                  Mark as Read
                                </MenuItem>
                                <MenuItem onClick={() => handleUpdateMessageStatus(message.id, 'unread')}>
                                  Mark as Unread
                                </MenuItem>
                              </MenuList>
                            </Menu>
                            <IconButton
                              size="xs"
                              colorScheme="red"
                              icon={<DeleteIcon />}
                              onClick={() => handleDeleteMessage(message.id)}
                              aria-label="Delete message"
                            />
                          </HStack>
                        </Td>
                      </Tr>
                    ))
                  ) : (
                    <Tr>
                      <Td colSpan={5} textAlign="center" color="gray.400" py={8}>
                        No messages found
                      </Td>
                    </Tr>
                  )}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>

        {/* Announcements */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between">
              <Text fontSize="lg" fontWeight="bold" color="white">
                Announcements
              </Text>
              <Button
                size="sm"
                colorScheme="blue"
                leftIcon={<AddIcon />}
                onClick={() => openAnnouncementModal()}
              >
                New Announcement
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th color="gray.300">Title</Th>
                    <Th color="gray.300">Priority</Th>
                    <Th color="gray.300">Status</Th>
                    <Th color="gray.300">Created</Th>
                    <Th color="gray.300">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {isLoading ? (
                    <Tr>
                      <Td colSpan={5} textAlign="center" color="gray.400" py={8}>
                        Loading announcements...
                      </Td>
                    </Tr>
                  ) : hasError ? (
                    <Tr>
                      <Td colSpan={5} textAlign="center" color="red.400" py={8}>
                        ❌ Failed to load announcements data
                      </Td>
                    </Tr>
                  ) : announcements.length > 0 ? (
                    announcements.map((announcement) => (
                      <Tr key={announcement.id}>
                        <Td color="white">{announcement.title}</Td>
                        <Td>
                          <Badge 
                            colorScheme={
                              announcement.priority === 'high' ? 'red' : 
                              announcement.priority === 'normal' ? 'blue' : 'gray'
                            }
                          >
                            {announcement.priority}
                          </Badge>
                        </Td>
                        <Td>
                          <Badge colorScheme={announcement.is_active ? 'green' : 'gray'}>
                            {announcement.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </Td>
                        <Td color="gray.300">{formatDate(announcement.created_at)}</Td>
                        <Td>
                          <HStack spacing={2}>
                            <IconButton
                              size="xs"
                              icon={<EditIcon />}
                              onClick={() => openAnnouncementModal(announcement)}
                              aria-label="Edit announcement"
                            />
                            <IconButton
                              size="xs"
                              colorScheme="red"
                              icon={<DeleteIcon />}
                              onClick={() => handleDeleteAnnouncement(announcement.id)}
                              aria-label="Delete announcement"
                            />
                          </HStack>
                        </Td>
                      </Tr>
                    ))
                  ) : (
                    <Tr>
                      <Td colSpan={5} textAlign="center" color="gray.400" py={8}>
                        No announcements found
                      </Td>
                    </Tr>
                  )}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>

        {/* Robot Registry */}
        <Card w="full" bg="gray.800" border="1px solid" borderColor="gray.600">
          <CardHeader>
            <HStack justify="space-between">
              <Text fontSize="lg" fontWeight="bold" color="white">
                Robot Registry
              </Text>
              <Button
                size="sm"
                colorScheme="green"
                leftIcon={<AddIcon />}
                onClick={() => openRobotModal()}
              >
                Add Robot
              </Button>
            </HStack>
          </CardHeader>
          <CardBody>
            <TableContainer>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th color="gray.300">Name</Th>
                    <Th color="gray.300">Type</Th>
                    <Th color="gray.300">WebRTC URL</Th>
                    <Th color="gray.300">Upload Endpoint</Th>
                    <Th color="gray.300">Created</Th>
                    <Th color="gray.300">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {isLoading ? (
                    <Tr>
                      <Td colSpan={6} textAlign="center" color="gray.400" py={8}>
                        Loading robots...
                      </Td>
                    </Tr>
                  ) : hasError ? (
                    <Tr>
                      <Td colSpan={6} textAlign="center" color="red.400" py={8}>
                        ❌ Failed to load robots data
                      </Td>
                    </Tr>
                  ) : robots.length > 0 ? (
                    robots.map((robot) => (
                      <Tr key={robot.id}>
                        <Td color="white">{robot.name}</Td>
                        <Td>
                          <Badge colorScheme="purple">
                            {robot.type}
                          </Badge>
                        </Td>
                        <Td color="gray.300" maxW="200px" overflow="hidden" textOverflow="ellipsis">
                          {robot.webrtc_url || 'Not configured'}
                        </Td>
                        <Td color="gray.300" maxW="200px" overflow="hidden" textOverflow="ellipsis">
                          {robot.upload_endpoint || 'Not configured'}
                        </Td>
                        <Td color="gray.300">{formatDate(robot.created_at)}</Td>
                        <Td>
                          <HStack spacing={2}>
                            <IconButton
                              size="xs"
                              colorScheme="blue"
                              icon={<EditIcon />}
                              onClick={() => openRobotModal(robot)}
                              aria-label="Edit robot"
                            />
                            <IconButton
                              size="xs"
                              colorScheme="red"
                              icon={<DeleteIcon />}
                              onClick={() => handleDeleteRobot(robot.id)}
                              aria-label="Delete robot"
                            />
                          </HStack>
                        </Td>
                      </Tr>
                    ))
                  ) : (
                    <Tr>
                      <Td colSpan={6} textAlign="center" color="gray.400" py={8}>
                        No robots found
                      </Td>
                    </Tr>
                  )}
                </Tbody>
              </Table>
            </TableContainer>
          </CardBody>
        </Card>
      </VStack>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        isOpen={isOpen}
        leastDestructiveRef={cancelRef}
        onClose={onClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent bg="gray.800" border="1px solid" borderColor="gray.600">
            <AlertDialogHeader fontSize="lg" fontWeight="bold" color="white">
              Delete Booking
            </AlertDialogHeader>

            <AlertDialogBody color="gray.300">
              Are you sure you want to delete this booking? This action cannot be undone.
              {selectedBooking && (
                <Box mt={4} p={4} bg="gray.700" borderRadius="md">
                  <Text><strong>User:</strong> {selectedBooking.user_name}</Text>
                  <Text><strong>Robot:</strong> {selectedBooking.robot_type}</Text>
                  <Text><strong>Date:</strong> {selectedBooking.date}</Text>
                  <Text><strong>Time:</strong> {selectedBooking.start_time} - {selectedBooking.end_time}</Text>
                </Box>
              )}
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onClose}>
                Cancel
              </Button>
              <Button colorScheme="red" onClick={handleDeleteBooking} ml={3}>
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      {/* Message View Modal */}
      <Modal isOpen={isMessageOpen} onClose={onMessageClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="gray.800" border="1px solid" borderColor="gray.600">
          <ModalHeader color="white">Contact Message</ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody>
            {selectedMessage && (
              <VStack spacing={4} align="start">
                <Text color="white"><strong>From:</strong> {selectedMessage.name}</Text>
                <Text color="white"><strong>Email:</strong> {selectedMessage.email}</Text>
                <Text color="white"><strong>Date:</strong> {formatDate(selectedMessage.created_at)}</Text>
                <Text color="white"><strong>Status:</strong> 
                  <Badge ml={2} colorScheme={selectedMessage.status === 'read' ? 'green' : 'orange'}>
                    {selectedMessage.status}
                  </Badge>
                </Text>
                <Divider />
                <Text color="white"><strong>Message:</strong></Text>
                <Text color="gray.300" whiteSpace="pre-wrap">
                  {selectedMessage.message}
                </Text>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" onClick={onMessageClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Announcement Create/Edit Modal */}
      <Modal isOpen={isAnnouncementModalOpen} onClose={() => setIsAnnouncementModalOpen(false)} size="lg">
        <ModalOverlay />
        <ModalContent bg="gray.800" border="1px solid" borderColor="gray.600">
          <ModalHeader color="white">
            {isEditingAnnouncement ? 'Edit Announcement' : 'Create New Announcement'}
          </ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel color="white">Title</FormLabel>
                <Input
                  value={announcementForm.title}
                  onChange={(e) => setAnnouncementForm({...announcementForm, title: e.target.value})}
                  placeholder="Enter announcement title"
                  bg="gray.700"
                  color="white"
                  borderColor="gray.600"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel color="white">Content</FormLabel>
                <Textarea
                  value={announcementForm.content}
                  onChange={(e) => setAnnouncementForm({...announcementForm, content: e.target.value})}
                  placeholder="Enter announcement content"
                  rows={5}
                  bg="gray.700"
                  color="white"
                  borderColor="gray.600"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel color="white">Priority</FormLabel>
                <Select
                  value={announcementForm.priority}
                  onChange={(e) => setAnnouncementForm({...announcementForm, priority: e.target.value})}
                  bg="gray.700"
                  color="white"
                  borderColor="gray.600"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                </Select>
              </FormControl>
              
              <FormControl display="flex" alignItems="center">
                <FormLabel color="white" mb="0">
                  Active
                </FormLabel>
                <Switch
                  isChecked={announcementForm.is_active}
                  onChange={(e) => setAnnouncementForm({...announcementForm, is_active: e.target.checked})}
                  colorScheme="blue"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => setIsAnnouncementModalOpen(false)}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleAnnouncementSubmit}>
              {isEditingAnnouncement ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Robot Modal */}
      <Modal isOpen={isRobotModalOpen} onClose={() => setIsRobotModalOpen(false)}>
        <ModalOverlay />
        <ModalContent bg="gray.800" border="1px solid" borderColor="gray.600">
          <ModalHeader color="white">
            {isEditingRobot ? 'Edit Robot' : 'Add New Robot'}
          </ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel color="gray.200">Robot Name</FormLabel>
                <Input
                  placeholder="Enter robot name"
                  value={robotForm.name}
                  onChange={(e) => setRobotForm({...robotForm, name: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel color="gray.200">Robot Type</FormLabel>
                <Select
                  placeholder="Select robot type"
                  value={robotForm.type}
                  onChange={(e) => setRobotForm({...robotForm, type: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                >
                  <option value="turtlebot">TurtleBot</option>
                  <option value="arm">Robot Arm</option>
                  <option value="hand">Robot Hand</option>
                  <option value="quadruped">Quadruped</option>
                  <option value="humanoid">Humanoid</option>
                  <option value="drone">Drone</option>
                  <option value="other">Other</option>
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel color="gray.200">WebRTC URL</FormLabel>
                <Input
                  placeholder="http://robot-ip:8080"
                  value={robotForm.webrtc_url}
                  onChange={(e) => setRobotForm({...robotForm, webrtc_url: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>

              <FormControl>
                <FormLabel color="gray.200">RTSP URL (Admin Only)</FormLabel>
                <Input
                  placeholder="rtsp://camera-host:8554/stream"
                  value={robotForm.rtsp_url}
                  onChange={(e) => setRobotForm({...robotForm, rtsp_url: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>

              <FormControl>
                <FormLabel color="gray.200">Upload Endpoint</FormLabel>
                <Input
                  placeholder="http://robot-api:8080/upload"
                  value={robotForm.upload_endpoint}
                  onChange={(e) => setRobotForm({...robotForm, upload_endpoint: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => setIsRobotModalOpen(false)}>
              Cancel
            </Button>
            <Button 
              colorScheme="green" 
              onClick={isEditingRobot ? handleUpdateRobot : handleCreateRobot}
              isDisabled={!robotForm.name || !robotForm.type}
            >
              {isEditingRobot ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* User Delete Confirmation Modal */}
      <Modal isOpen={isUserDeleteModalOpen} onClose={() => setIsUserDeleteModalOpen(false)}>
        <ModalOverlay />
        <ModalContent bg="gray.800" border="1px solid" borderColor="gray.600">
          <ModalHeader color="white">Confirm Delete User</ModalHeader>
          <ModalCloseButton color="gray.400" />
          <ModalBody>
            <Text color="gray.300">
              Are you sure you want to delete user <strong>{selectedUser?.email}</strong>?
            </Text>
            <Text mt={2} color="red.400" fontSize="sm">
              This will permanently delete:
            </Text>
            <VStack align="start" mt={2} spacing={1} pl={4}>
              <Text color="red.300" fontSize="sm">• User account</Text>
              <Text color="red.300" fontSize="sm">• Workspace files</Text>
              <Text color="red.300" fontSize="sm">• Theia container</Text>
              <Text color="red.300" fontSize="sm">• All bookings and sessions</Text>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button mr={3} onClick={() => setIsUserDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button colorScheme="red" onClick={handleDeleteUser}>
              Delete User
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Change Password Modal */}
      <Modal isOpen={isPasswordModalOpen} onClose={() => setIsPasswordModalOpen(false)}>
        <ModalOverlay />
        <ModalContent bg="gray.800" border="1px solid" borderColor="gray.600">
          <ModalHeader color="white">Change Admin Password</ModalHeader>
          <ModalCloseButton color="gray.400" />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel color="gray.200">Current Password</FormLabel>
                <Input
                  type="password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel color="gray.200">New Password</FormLabel>
                <Input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel color="gray.200">Confirm New Password</FormLabel>
                <Input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                  bg="gray.700"
                  border="1px solid"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button mr={3} onClick={() => setIsPasswordModalOpen(false)}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleChangePassword}>
              Update Password
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  );
};

export default AdminDashboard;
