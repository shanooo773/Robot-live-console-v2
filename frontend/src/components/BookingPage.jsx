import { useState, useEffect, useMemo } from "react";
import { useToast } from "@chakra-ui/react";
import { ArrowLeft, Check, ChevronLeft, ChevronRight, Code2, Clock, Calendar, Play } from "lucide-react";
import Navbar from "./Navbar";
import CountdownTimer from "./CountdownTimer";
import "../styles/navbar.css";
import "../styles/booking.css";
import { createBooking, getAvailableRobots, getAvailableSlots, getUserBookings } from "../api";

const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const DAY_NAMES = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

const ROBOT_DESCRIPTIONS = {
  turtlebot: { label: "TurtleBot",   desc: "Autonomous Navigation",  sub: "Ideal for SLAM & path planning tasks" },
  arm:        { label: "Robot Arm",   desc: "Precision Manipulation", sub: "Perfect for pick & place tasks" },
  hand:       { label: "Humanoid",    desc: "Complex Interactions",   sub: "Good for studying human-like robot behaviors" },
};

const BookingPage = ({ user, authToken, onBooking, onLogout, onNavigate, onAdminAccess }) => {
  const [step, setStep]                       = useState(1);
  const [availableRobots, setAvailableRobots] = useState([]);
  const [robotLookup, setRobotLookup]         = useState({});
  const [selectedRobot, setSelectedRobot]     = useState(null);
  const [calDate, setCalDate]                 = useState(new Date());
  const [selectedDay, setSelectedDay]         = useState(null);
  const [timeSlots, setTimeSlots]             = useState([]);
  const [selectedSlot, setSelectedSlot]       = useState(null);
  const [isLoading, setIsLoading]             = useState(false);
  const [isBooking, setIsBooking]             = useState(false);
  const [success, setSuccess]                 = useState(false);
  const [bookedBooking, setBookedBooking]     = useState(null);
  const [userBookings, setUserBookings]       = useState([]);
  const [sessionsTab, setSessionsTab]         = useState("upcoming");
  const [expiredCountdowns, setExpiredCountdowns] = useState(new Set());
  const toast = useToast();

  const calYear  = calDate.getFullYear();
  const calMonth = calDate.getMonth();
  const firstDay    = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const today = new Date();

  // ── Load data on mount ──────────────────────────────────────────
  useEffect(() => {
    loadRobots();
    loadBookings();
  }, [authToken]);

  const loadRobots = async () => {
    try {
      const data = await getAvailableRobots();
      const registry = Array.isArray(data.registry) ? data.registry : [];
      setAvailableRobots(registry);
      const lookup = {};
      registry.forEach(r => {
        lookup[String(r.id)] = {
          ...r,
          emoji: r.type?.includes("arm") ? "🦾" : r.type?.includes("hand") ? "🤲" : "🤖",
        };
      });
      setRobotLookup(lookup);
    } catch {
      setAvailableRobots([]);
    }
  };

  const loadBookings = async () => {
    if (!authToken) return;
    try {
      const bookings = await getUserBookings(authToken);
      setUserBookings(Array.isArray(bookings) ? bookings : []);
    } catch {
      setUserBookings([]);
    }
  };

  // ── Slots ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!selectedRobot || !selectedDay || !authToken) { setTimeSlots([]); return; }
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2,"0")}-${String(selectedDay).padStart(2,"0")}`;
    setIsLoading(true);
    getAvailableSlots(dateStr, String(selectedRobot.id), authToken, selectedRobot.type)
      .then(res => setTimeSlots(res.available_slots || []))
      .catch(() => setTimeSlots([]))
      .finally(() => setIsLoading(false));
  }, [selectedRobot, selectedDay, calYear, calMonth, authToken]);

  // ── Classify bookings ────────────────────────────────────────────
  const classifiedBookings = useMemo(() => {
    const now = new Date();
    const upcoming = [], past = [];
    userBookings.forEach(b => {
      const start = new Date(`${b.date}T${b.start_time}`);
      const end   = new Date(`${b.date}T${b.end_time}`);
      if (end < now) {
        past.push({ ...b, timeStatus: "completed" });
      } else if (start <= now && now <= end) {
        upcoming.push({ ...b, timeStatus: "in-progress" });
      } else {
        upcoming.push({ ...b, timeStatus: "scheduled" });
      }
    });
    upcoming.sort((a, b) => new Date(`${a.date}T${a.start_time}`) - new Date(`${b.date}T${b.start_time}`));
    past.sort((a, b) => new Date(`${b.date}T${b.start_time}`) - new Date(`${a.date}T${a.start_time}`));
    return { upcoming, past };
  }, [userBookings]);

  // ── Helpers ──────────────────────────────────────────────────────
  const selectedDateStr = selectedDay
    ? `${calYear}-${String(calMonth+1).padStart(2,"0")}-${String(selectedDay).padStart(2,"0")}`
    : null;

  const selectedDateLabel = selectedDay
    ? new Date(calYear, calMonth, selectedDay).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })
    : null;

  const robotInfo = selectedRobot
    ? { ...(ROBOT_DESCRIPTIONS[selectedRobot.type] || { desc: "", sub: "" }), label: selectedRobot.name }
    : null;

  const sessionDuration = selectedSlot
    ? Math.round((new Date(`2000-01-01T${selectedSlot.end_time}`) - new Date(`2000-01-01T${selectedSlot.start_time}`)) / 3600000)
    : null;

  const getRobotLabel = (b) => {
    const r = robotLookup[String(b.robot_id)];
    return r ? (r.name || ROBOT_DESCRIPTIONS[r.type]?.label) : (b.robot_name || b.robot_type || "Robot");
  };

  const getRobotEmoji = (b) => robotLookup[String(b.robot_id)]?.emoji || "🤖";

  const launchBooking = (b) => onBooking({
    id: `booking_${b.id}`,
    robotType: b.robot_type,
    robotId: b.robot_id,
    date: b.date,
    startTime: b.start_time,
    endTime: b.end_time,
    bookingId: b.id,
    available: false,
    bookedBy: user.name,
  });

  // ── Confirm booking ───────────────────────────────────────────────
  const handleConfirm = async () => {
    if (!authToken) {
      toast({ title: "Not logged in", description: "Please sign in to book a session.", status: "error", duration: 4000, isClosable: true });
      return;
    }
    if (!selectedRobot || !selectedDateStr || !selectedSlot) return;
    setIsBooking(true);
    try {
      const booking = await createBooking({
        robot_id: selectedRobot.id,
        robot_type: selectedRobot.type,
        date: selectedDateStr,
        start_time: selectedSlot.start_time,
        end_time: selectedSlot.end_time,
      }, authToken);
      setBookedBooking(booking);
      setSuccess(true);
      await loadBookings();
      toast({ title: "Session booked!", status: "success", duration: 3000, isClosable: true });
    } catch (e) {
      toast({ title: "Booking failed", description: e?.response?.data?.detail || e.message, status: "error", duration: 5000, isClosable: true });
    } finally {
      setIsBooking(false);
    }
  };

  const STEPS = ["Select Robot", "Pick Date", "Choose Time", "Report Finish"];

  // ── Success screen ───────────────────────────────────────────────
  if (success) {
    return (
      <div className="bk-page">
        <Navbar user={user} onNavigate={onNavigate} currentPage="booking" onLogout={onLogout} onAdminAccess={onAdminAccess} />
        <div className="bk-success">
          <div className="bk-success__icon"><Check size={40} /></div>
          <h2>Session Booked!</h2>
          <p>Your ROS2 simulation session has been confirmed.</p>
          <div className="bk-success__details">
            <div><strong>Robot:</strong> {robotInfo?.label || selectedRobot?.name}</div>
            <div><strong>Date:</strong> {selectedDateLabel}</div>
            <div><strong>Time:</strong> {selectedSlot?.start_time?.slice(0,5)} – {selectedSlot?.end_time?.slice(0,5)}</div>
          </div>
          <div className="bk-success__actions">
            <button className="bk-btn-primary" onClick={() => onBooking({
              id: `booking_${bookedBooking?.id}`,
              robotType: selectedRobot.type,
              robotId: selectedRobot.id,
              date: selectedDateStr,
              startTime: selectedSlot.start_time,
              endTime: selectedSlot.end_time,
              bookingId: bookedBooking?.id,
              available: false,
              bookedBy: user.name,
            })}>
              Launch Console
            </button>
            <button className="bk-btn-secondary" onClick={() => onNavigate("dashboard")}>
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Main page ────────────────────────────────────────────────────
  return (
    <div className="bk-page">
      <Navbar user={user} onNavigate={onNavigate} currentPage="booking" onLogout={onLogout} onAdminAccess={onAdminAccess} />

      <div className="bk-container">
        <button className="bk-back" onClick={() => onNavigate("dashboard")}>
          <ArrowLeft size={15} /> Back to Dashboard
        </button>

        <h1 className="bk-title">Book a Session</h1>
        <p className="bk-subtitle">Choose robot type, date, and time for your next ROS2 simulation session.</p>

        {/* Step Progress */}
        <div className="bk-steps">
          {STEPS.map((label, i) => {
            const num = i + 1;
            const done   = num < step;
            const active = num === step;
            return (
              <div key={num} className={`bk-step ${done ? "done" : ""} ${active ? "active" : ""}`}>
                <div className="bk-step__circle">{done ? <Check size={13} /> : num}</div>
                <span className="bk-step__label">{label}</span>
                {i < STEPS.length - 1 && <div className="bk-step__line" />}
              </div>
            );
          })}
        </div>

        {/* Wizard + Summary */}
        <div className="bk-body">
          <div className="bk-main">

            {/* STEP 1 — Select Robot */}
            {step === 1 && (
              <div className="bk-section">
                <h2 className="bk-section__title">Select Robot</h2>
                {availableRobots.length === 0 ? (
                  <p style={{ color: "#94a3b8", fontSize: 14 }}>Loading robots...</p>
                ) : (
                  <div className="bk-robots">
                    {availableRobots.map(robot => {
                      const info       = ROBOT_DESCRIPTIONS[robot.type] || { desc: robot.type, sub: "" };
                      const isSelected = selectedRobot?.id === robot.id;
                      const emoji      = robot.type?.includes("arm") ? "🦾" : robot.type?.includes("hand") ? "🤲" : "🤖";
                      return (
                        <div key={robot.id} className={`bk-robot-card ${isSelected ? "selected" : ""}`} onClick={() => setSelectedRobot(robot)}>
                          <div className="bk-robot-card__icon">{emoji}</div>
                          <div className="bk-robot-card__name">{robot.name}</div>
                          <img
                            src={`https://img.icons8.com/fluency/80/${robot.type?.includes("arm") ? "robot-arm" : "robot-2"}.png`}
                            alt={info.label}
                            className="bk-robot-card__img"
                            onError={e => e.target.style.display = "none"}
                          />
                          <div className="bk-robot-card__desc">{info.desc}</div>
                          <div className="bk-robot-card__sub">{info.sub}</div>
                          <button className={`bk-robot-card__btn ${isSelected ? "selected" : ""}`}>
                            {isSelected ? <><Check size={13} /> Selected</> : "Select"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
                <p className="bk-hint">Unsure which robot to choose? <a href="#">Check our Tutorials</a></p>
              </div>
            )}

            {/* STEP 2 — Pick Date */}
            {step === 2 && (
              <div className="bk-section">
                <h2 className="bk-section__title">Pick Date</h2>
                <div className="bk-calendar">
                  <div className="bk-cal__header">
                    <button onClick={() => setCalDate(new Date(calYear, calMonth - 1, 1))}><ChevronLeft size={16} /></button>
                    <span>{MONTH_NAMES[calMonth]} {calYear}</span>
                    <button onClick={() => setCalDate(new Date(calYear, calMonth + 1, 1))}><ChevronRight size={16} /></button>
                  </div>
                  <div className="bk-cal__days-hdr">
                    {DAY_NAMES.map(d => <span key={d}>{d}</span>)}
                  </div>
                  <div className="bk-cal__grid">
                    {Array.from({ length: firstDay }).map((_, i) => <span key={`e${i}`} />)}
                    {Array.from({ length: daysInMonth }).map((_, i) => {
                      const day    = i + 1;
                      const isToday = day === today.getDate() && calMonth === today.getMonth() && calYear === today.getFullYear();
                      const isPast  = new Date(calYear, calMonth, day) < new Date(today.getFullYear(), today.getMonth(), today.getDate());
                      return (
                        <button
                          key={day}
                          className={`bk-cal__day ${isToday ? "today" : ""} ${selectedDay === day ? "selected" : ""} ${isPast ? "past" : ""}`}
                          onClick={() => !isPast && setSelectedDay(day)}
                          disabled={isPast}
                        >
                          {day}
                        </button>
                      );
                    })}
                  </div>
                </div>
                {selectedDay && <p className="bk-selected-date">Selected: <strong>{selectedDateLabel}</strong></p>}
              </div>
            )}

            {/* STEP 3 — Choose Time */}
            {step === 3 && (
              <div className="bk-section">
                <h2 className="bk-section__title">Choose Time</h2>
                {isLoading ? (
                  <p style={{ color: "#94a3b8", fontSize: 14 }}>Loading available slots...</p>
                ) : timeSlots.length === 0 ? (
                  <p style={{ color: "#94a3b8", fontSize: 14 }}>No slots available for this date. Try another day.</p>
                ) : (
                  <div className="bk-slots">
                    {timeSlots.map((slot, i) => (
                      <button
                        key={i}
                        className={`bk-slot ${selectedSlot?.start_time === slot.start_time ? "selected" : ""}`}
                        onClick={() => setSelectedSlot(slot)}
                      >
                        {slot.start_time?.slice(0, 5)} – {slot.end_time?.slice(0, 5)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* STEP 4 — Confirm */}
            {step === 4 && (
              <div className="bk-section">
                <h2 className="bk-section__title">Confirm Your Session</h2>
                <div className="bk-confirm">
                  <div className="bk-confirm__row"><span>Robot</span><strong>{robotInfo?.label || selectedRobot?.name}</strong></div>
                  <div className="bk-confirm__row"><span>Description</span><strong>{robotInfo?.desc}</strong></div>
                  <div className="bk-confirm__row"><span>Date</span><strong>{selectedDateLabel}</strong></div>
                  <div className="bk-confirm__row"><span>Time</span><strong>{selectedSlot?.start_time?.slice(0,5)} – {selectedSlot?.end_time?.slice(0,5)}</strong></div>
                  <div className="bk-confirm__row"><span>Duration</span><strong>{sessionDuration} Hour{sessionDuration !== 1 ? "s" : ""}</strong></div>
                  <div className="bk-confirm__row"><span>Credits Required</span><strong>{sessionDuration * 2}</strong></div>
                </div>
                <button className="bk-btn-primary bk-confirm-btn" onClick={handleConfirm} disabled={isBooking}>
                  {isBooking ? "Booking..." : "Confirm & Launch Console"}
                </button>
              </div>
            )}

            {/* Nav buttons */}
            <div className="bk-nav-btns">
              {step > 1 && (
                <button className="bk-btn-secondary" onClick={() => setStep(s => s - 1)}>
                  <ChevronLeft size={15} /> Back
                </button>
              )}
              {step < 4 && (
                <button
                  className="bk-btn-primary"
                  onClick={() => setStep(s => s + 1)}
                  disabled={
                    (step === 1 && !selectedRobot) ||
                    (step === 2 && !selectedDay) ||
                    (step === 3 && !selectedSlot)
                  }
                >
                  Next <ChevronRight size={15} />
                </button>
              )}
            </div>
          </div>

          {/* Session Summary Panel */}
          <div className="bk-summary">
            <h3 className="bk-summary__title">Session Summary</h3>
            <div className="bk-summary__robot-icon">
              <span style={{ fontSize: 36 }}>
                {selectedRobot
                  ? (selectedRobot.type?.includes("arm") ? "🦾" : selectedRobot.type?.includes("hand") ? "🤲" : "🤖")
                  : <span style={{ opacity: 0.25 }}>🤖</span>}
              </span>
            </div>
            <div className="bk-summary__robot-name">
              {robotInfo?.label || (selectedRobot ? selectedRobot.name : "No robot selected")}
            </div>
            <div className="bk-summary__rows">
              <div className="bk-summary__row"><span>📅 Date</span><strong>{selectedDateLabel || "—"}</strong></div>
              <div className="bk-summary__row"><span>⏰ Time</span><strong>{selectedSlot ? `${selectedSlot.start_time?.slice(0,5)} – ${selectedSlot.end_time?.slice(0,5)}` : "—"}</strong></div>
              <div className="bk-summary__row"><span>⌛ Duration</span><strong>{sessionDuration ? `${sessionDuration} Hour` : "—"}</strong></div>
              <div className="bk-summary__row"><span>⭐ Credits</span><strong>{sessionDuration ? sessionDuration * 2 : "—"}</strong></div>
            </div>
            {step === 4 && selectedRobot && selectedDay && selectedSlot && (
              <button className="bk-summary__confirm-btn" onClick={handleConfirm} disabled={isBooking}>
                {isBooking ? "Booking..." : "Confirm & Launch Console"}
              </button>
            )}
          </div>
        </div>

        {/* ── Code Preview — always available ───────────────────── */}
        <div className="bk-preview-card">
          <div className="bk-preview-card__left">
            <div className="bk-preview-card__icon-wrap">
              <Code2 size={22} color="#2563EB" />
            </div>
            <div>
              <div className="bk-preview-card__title">
                Development Environment
                <span className="bk-preview-card__badge">Always Available</span>
              </div>
              <div className="bk-preview-card__desc">
                Access your personal IDE to write, edit, and save robot code anytime.
              </div>
              <div className="bk-preview-card__sub">
                Preview Mode: Full code editing — book a session for robot execution and live video feed.
              </div>
            </div>
          </div>
          <button
            className="bk-btn-primary"
            onClick={() => onBooking({
              id: `code_preview_${Date.now()}`,
              robotType: "turtlebot",
              date: new Date().toISOString().split("T")[0],
              startTime: new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" }),
              endTime: new Date(Date.now() + 3600000).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" }),
              bookingId: "code_preview",
              available: true,
              bookedBy: user?.name,
              isPreview: true,
            })}
          >
            <Play size={15} /> Open IDE
          </button>
        </div>

        {/* ── My Sessions ───────────────────────────────────────── */}
        {(classifiedBookings.upcoming.length > 0 || classifiedBookings.past.length > 0) && (
          <div className="bk-sessions">
            <h2 className="bk-sessions__title">My Sessions</h2>

            {/* Tabs */}
            <div className="bk-sessions__tabs">
              <button
                className={`bk-sessions__tab ${sessionsTab === "upcoming" ? "active" : ""}`}
                onClick={() => setSessionsTab("upcoming")}
              >
                Upcoming
                {classifiedBookings.upcoming.length > 0 && (
                  <span className="bk-sessions__tab-count">{classifiedBookings.upcoming.length}</span>
                )}
              </button>
              <button
                className={`bk-sessions__tab ${sessionsTab === "past" ? "active" : ""}`}
                onClick={() => setSessionsTab("past")}
              >
                Past
                {classifiedBookings.past.length > 0 && (
                  <span className="bk-sessions__tab-count bk-sessions__tab-count--gray">{classifiedBookings.past.length}</span>
                )}
              </button>
            </div>

            {/* Upcoming */}
            {sessionsTab === "upcoming" && (
              classifiedBookings.upcoming.length === 0 ? (
                <div className="bk-sessions__empty">No upcoming sessions</div>
              ) : (
                <div className="bk-sessions__grid">
                  {classifiedBookings.upcoming.map(b => (
                    <div key={b.id} className={`bk-session-card ${b.timeStatus === "in-progress" ? "active" : ""}`}>
                      <div className="bk-session-card__top">
                        <span className={`bk-session-card__badge ${b.timeStatus === "in-progress" ? "orange" : "green"}`}>
                          {b.timeStatus === "in-progress" ? "In Progress" : "Scheduled"}
                        </span>
                        <span className="bk-session-card__robot">
                          {getRobotEmoji(b)} {getRobotLabel(b)}
                        </span>
                      </div>

                      <div className="bk-session-card__date">
                        <Calendar size={13} />
                        {new Date(b.date).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                      </div>
                      <div className="bk-session-card__time">
                        <Clock size={13} />
                        {b.start_time} – {b.end_time}
                      </div>

                      {b.timeStatus === "scheduled" && (
                        <div className="bk-session-card__countdown">
                          <CountdownTimer
                            targetDate={b.date}
                            targetTime={b.start_time}
                            onExpired={() => setExpiredCountdowns(prev => new Set([...prev, b.id]))}
                          />
                        </div>
                      )}

                      <button
                        className={`bk-session-card__btn ${b.timeStatus === "in-progress" ? "orange" : "green"}`}
                        disabled={b.timeStatus === "scheduled" && !expiredCountdowns.has(b.id)}
                        onClick={() => launchBooking(b)}
                      >
                        {b.timeStatus === "in-progress"
                          ? "Enter Console"
                          : expiredCountdowns.has(b.id)
                            ? "Enter Console"
                            : "Waiting for session..."}
                      </button>
                    </div>
                  ))}
                </div>
              )
            )}

            {/* Past */}
            {sessionsTab === "past" && (
              classifiedBookings.past.length === 0 ? (
                <div className="bk-sessions__empty">No past sessions</div>
              ) : (
                <div className="bk-sessions__grid">
                  {classifiedBookings.past.map(b => (
                    <div key={b.id} className="bk-session-card past">
                      <div className="bk-session-card__top">
                        <span className="bk-session-card__badge gray">Completed</span>
                        <span className="bk-session-card__robot">
                          {getRobotEmoji(b)} {getRobotLabel(b)}
                        </span>
                      </div>
                      <div className="bk-session-card__date">
                        <Calendar size={13} />
                        {new Date(b.date).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                      </div>
                      <div className="bk-session-card__time">
                        <Clock size={13} />
                        {b.start_time} – {b.end_time}
                      </div>
                      <div className="bk-session-card__completed-text">Session completed</div>
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default BookingPage;
