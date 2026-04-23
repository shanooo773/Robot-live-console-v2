import { useState, useEffect, useMemo } from "react";
import { useToast } from "@chakra-ui/react";
import {
  Play, Cpu, Clock, Layers, Rocket, BookOpen, FileText, Users,
  MoreHorizontal, ChevronRight, Calendar, CheckCircle
} from "lucide-react";
import Navbar from "./Navbar";
import "../styles/navbar.css";
import "../styles/dashboard.css";
import {
  getUserBookings, getAvailableRobots, createBooking, getAvailableSlots
} from "../api";

const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const DAY_NAMES = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

const Dashboard = ({ user, authToken, onNavigate, onBooking, onLogout, onAdminAccess }) => {
  const [userBookings, setUserBookings] = useState([]);
  const [availableRobots, setAvailableRobots] = useState({});
  const [calDate, setCalDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState(null);
  const [timeSlots, setTimeSlots] = useState([]);
  const [selectedRobotId, setSelectedRobotId] = useState("");
  const [isBooking, setIsBooking] = useState(false);
  const toast = useToast();

  useEffect(() => {
    loadData();
  }, [authToken]);

  const loadData = async () => {
    try {
      const [bookings, robotData] = await Promise.all([
        getUserBookings(authToken).catch(() => []),
        getAvailableRobots().catch(() => ({ registry: [] })),
      ]);
      setUserBookings(Array.isArray(bookings) ? bookings : []);

      const registry = Array.isArray(robotData.registry) ? robotData.registry : [];
      const map = {};
      registry.forEach(r => {
        map[String(r.id)] = {
          id: r.id,
          name: r.name || r.type,
          type: r.type || "",
          emoji: r.type?.includes("arm") ? "🦾" : r.type?.includes("hand") ? "🤲" : "🤖",
        };
      });
      setAvailableRobots(map);
      if (registry.length > 0) setSelectedRobotId(String(registry[0].id));
    } catch (e) {
      console.error(e);
    }
  };

  // Stats
  const stats = useMemo(() => {
    const now = new Date();
    const active = userBookings.filter(b => {
      const start = new Date(`${b.date}T${b.start_time}`);
      const end = new Date(`${b.date}T${b.end_time}`);
      return start <= now && now <= end;
    }).length;
    const completed = userBookings.filter(b => new Date(`${b.date}T${b.end_time}`) < now).length;
    const hours = userBookings.reduce((acc, b) => {
      const s = new Date(`${b.date}T${b.start_time}`);
      const e = new Date(`${b.date}T${b.end_time}`);
      return acc + Math.max(0, (e - s) / 3600000);
    }, 0);
    const available = Object.keys(availableRobots).length;
    return { active, completed, hours: Math.round(hours), available };
  }, [userBookings, availableRobots]);

  // Recent projects (last 6 bookings)
  const recentProjects = useMemo(() => {
    return [...userBookings]
      .sort((a, b) => new Date(`${b.date}T${b.start_time}`) - new Date(`${a.date}T${a.start_time}`))
      .slice(0, 6);
  }, [userBookings]);

  // Calendar helpers
  const calYear = calDate.getFullYear();
  const calMonth = calDate.getMonth();
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const today = new Date();

  const bookedDays = new Set(
    userBookings.map(b => {
      const d = new Date(b.date);
      if (d.getFullYear() === calYear && d.getMonth() === calMonth) return d.getDate();
      return null;
    }).filter(Boolean)
  );

  // Load time slots when day or robot changes
  useEffect(() => {
    if (!selectedDay || !selectedRobotId || !authToken) { setTimeSlots([]); return; }
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2, "0")}-${String(selectedDay).padStart(2, "0")}`;
    getAvailableSlots(dateStr, selectedRobotId, authToken, availableRobots[selectedRobotId]?.type)
      .then(res => setTimeSlots(res.available_slots || []))
      .catch(() => setTimeSlots([]));
  }, [selectedDay, selectedRobotId, authToken, calYear, calMonth]);

  const handleBookSession = async (slot) => {
    if (!authToken) return;
    setIsBooking(true);
    try {
      const booking = await createBooking({
        robot_id: slot.robot_id || selectedRobotId,
        robot_type: slot.robot_type,
        date: slot.date,
        start_time: slot.start_time,
        end_time: slot.end_time,
      }, authToken);
      toast({ title: "Session booked!", status: "success", duration: 3000, isClosable: true });
      await loadData();
      onBooking({ ...slot, bookingId: booking.id, robotType: slot.robot_type, robotId: slot.robot_id || selectedRobotId, startTime: slot.start_time, endTime: slot.end_time, bookedBy: user.name });
    } catch (e) {
      toast({ title: "Booking failed", description: e?.response?.data?.detail || e.message, status: "error", duration: 4000, isClosable: true });
    } finally {
      setIsBooking(false);
    }
  };

  const robotList = Object.values(availableRobots);

  return (
    <div className="db-page">
      <Navbar
        user={user}
        onNavigate={onNavigate}
        currentPage="dashboard"
        onLogout={onLogout}
        onAdminAccess={onAdminAccess}
      />

      <div className="db-container">
        {/* Hero Banner */}
        <div className="db-hero">
          <div className="db-hero__left">
            <h1 className="db-hero__title">Welcome back, {user?.name?.split(" ")[0]} 👋</h1>
            <p className="db-hero__sub">Ready to build your next robotics project?</p>
            <button className="db-hero__btn" onClick={() => onNavigate("booking")}>
              <Play size={16} /> Start New Session
            </button>
          </div>
          <div className="db-hero__right">
            <img src="https://img.icons8.com/fluency/200/robot-2.png" alt="robot" className="db-hero__img" onError={e => e.target.style.display='none'} />
          </div>
        </div>

        {/* Stats Row */}
        <div className="db-stats">
          <div className="db-stat-card">
            <div className="db-stat-card__icon" style={{ background: "#EFF6FF" }}>
              <Layers size={20} color="#2563EB" />
            </div>
            <div>
              <div className="db-stat-card__value">{stats.active}</div>
              <div className="db-stat-card__label">Active Projects</div>
              <div className="db-stat-card__bar"><div style={{ width: `${Math.min(stats.active * 20, 100)}%`, background: "#2563EB" }} /></div>
            </div>
          </div>
          <div className="db-stat-card">
            <div className="db-stat-card__icon" style={{ background: "#F0FDF4" }}>
              <Cpu size={20} color="#16a34a" />
            </div>
            <div>
              <div className="db-stat-card__value">{stats.completed}</div>
              <div className="db-stat-card__label">Completed Simulations</div>
              <div className="db-stat-card__bar"><div style={{ width: `${Math.min(stats.completed * 5, 100)}%`, background: "#16a34a" }} /></div>
            </div>
          </div>
          <div className="db-stat-card">
            <div className="db-stat-card__icon" style={{ background: "#FFF7ED" }}>
              <Clock size={20} color="#ea580c" />
            </div>
            <div>
              <div className="db-stat-card__value">{stats.hours}h</div>
              <div className="db-stat-card__label">Hours Used</div>
              <div className="db-stat-card__bar"><div style={{ width: `${Math.min(stats.hours * 2, 100)}%`, background: "#ea580c" }} /></div>
            </div>
          </div>
          <div className="db-stat-card">
            <div className="db-stat-card__icon" style={{ background: "#FDF4FF" }}>
              <CheckCircle size={20} color="#9333ea" />
            </div>
            <div>
              <div className="db-stat-card__value">{stats.available}</div>
              <div className="db-stat-card__label">Available Sessions</div>
              <div className="db-stat-card__bar"><div style={{ width: `${Math.min(stats.available * 25, 100)}%`, background: "#9333ea" }} /></div>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="db-main">
          {/* Left Column */}
          <div className="db-left">
            {/* My Projects */}
            <div className="db-section">
              <h2 className="db-section__title">My Projects</h2>
              {recentProjects.length === 0 ? (
                <div className="db-empty">No projects yet. <button onClick={() => onNavigate("booking")}>Book a session</button> to get started.</div>
              ) : (
                <div className="db-projects">
                  {recentProjects.map((b) => {
                    const robot = availableRobots[String(b.robot_id)];
                    const isActive = (() => {
                      const now = new Date();
                      return new Date(`${b.date}T${b.start_time}`) <= now && now <= new Date(`${b.date}T${b.end_time}`);
                    })();
                    const isPast = new Date(`${b.date}T${b.end_time}`) < new Date();
                    const progress = isPast ? 100 : isActive ? 50 : 0;
                    return (
                      <div className="db-project-card" key={b.id}>
                        <div className="db-project-card__img">
                          <span>{robot?.emoji || "🤖"}</span>
                        </div>
                        <div className="db-project-card__info">
                          <div className="db-project-card__name">{robot?.name || b.robot_name || b.robot_type || "Robot Session"}</div>
                          <div className="db-project-card__meta">{b.date} · {b.start_time} - {b.end_time}</div>
                          <div className="db-project-card__progress">
                            <div className="db-project-card__progress-bar">
                              <div style={{ width: `${progress}%` }} />
                            </div>
                            <span>{isPast ? "Completed" : isActive ? "Active" : "Scheduled"}</span>
                          </div>
                        </div>
                        <button
                          className="db-project-card__btn"
                          onClick={() => onBooking({
                            id: `booking_${b.id}`,
                            robotType: b.robot_type,
                            robotId: b.robot_id,
                            date: b.date,
                            startTime: b.start_time,
                            endTime: b.end_time,
                            bookingId: b.id,
                            available: false,
                            bookedBy: user.name,
                          })}
                        >
                          {isPast ? "Review" : "Resume"} <ChevronRight size={14} />
                        </button>
                        <button className="db-project-card__more"><MoreHorizontal size={16} /></button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Book a Session */}
            <div className="db-section">
              <h2 className="db-section__title">Book a <span>Session</span></h2>
              <div className="db-booking">
                {/* Calendar */}
                <div className="db-cal">
                  <div className="db-cal__header">
                    <button onClick={() => setCalDate(new Date(calYear, calMonth - 1, 1))}>‹</button>
                    <span>{MONTH_NAMES[calMonth]} {calYear}</span>
                    <button onClick={() => setCalDate(new Date(calYear, calMonth + 1, 1))}>›</button>
                  </div>
                  <div className="db-cal__days-header">
                    {DAY_NAMES.map(d => <span key={d}>{d}</span>)}
                  </div>
                  <div className="db-cal__grid">
                    {Array.from({ length: firstDay }).map((_, i) => <span key={`e${i}`} />)}
                    {Array.from({ length: daysInMonth }).map((_, i) => {
                      const day = i + 1;
                      const isToday = day === today.getDate() && calMonth === today.getMonth() && calYear === today.getFullYear();
                      const hasBooking = bookedDays.has(day);
                      const isPast = new Date(calYear, calMonth, day) < new Date(today.getFullYear(), today.getMonth(), today.getDate());
                      return (
                        <button
                          key={day}
                          className={`db-cal__day ${isToday ? "today" : ""} ${selectedDay === day ? "selected" : ""} ${hasBooking ? "has-booking" : ""} ${isPast ? "past" : ""}`}
                          onClick={() => !isPast && setSelectedDay(day)}
                          disabled={isPast}
                        >
                          {day}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Time Slots */}
                <div className="db-slots">
                  {selectedDay ? (
                    <>
                      <div className="db-slots__header">
                        {robotList.length > 0 && (
                          <select value={selectedRobotId} onChange={e => setSelectedRobotId(e.target.value)} className="db-slots__robot-select">
                            {robotList.map(r => <option key={r.id} value={String(r.id)}>{r.emoji} {r.name}</option>)}
                          </select>
                        )}
                      </div>
                      {timeSlots.length === 0 ? (
                        <p className="db-slots__empty">No slots available</p>
                      ) : (
                        <div className="db-slots__grid">
                          {timeSlots.slice(0, 4).map((slot, i) => (
                            <button key={i} className="db-slot-btn" onClick={() => handleBookSession(slot)} disabled={isBooking}>
                              {slot.start_time?.slice(0, 5)}
                            </button>
                          ))}
                        </div>
                      )}
                      <button className="db-book-btn" onClick={() => onNavigate("booking")} disabled={isBooking}>
                        <Calendar size={15} /> Book Session
                      </button>
                    </>
                  ) : (
                    <p className="db-slots__empty">Select a date to see available slots</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column — Quick Access */}
          <div className="db-right">
            <div className="db-section">
              <h2 className="db-section__title">Quick Access</h2>
              <div className="db-quick">
                <button className="db-quick__btn primary" onClick={() => onNavigate("editor")}>
                  <Rocket size={18} /> Launch Console
                </button>
                <button className="db-quick__btn">
                  <Play size={18} /> Tutorials
                </button>
                <button className="db-quick__btn">
                  <FileText size={18} /> Docs
                </button>
                <button className="db-quick__btn">
                  <Users size={18} /> Community
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
