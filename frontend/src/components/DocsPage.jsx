import { useState } from "react";
import { BookOpen, Code2, BarChart3, ChevronRight, ChevronDown, Upload, FolderPlus, Key, Database, Cpu, Network, Users, Zap, Search, ArrowLeft } from "lucide-react";
import Navbar from "./Navbar";
import "../styles/docs.css";

// ─── Content data ─────────────────────────────────────────────────────────────

const SECTIONS = [
  {
    id: "user",
    label: "User Documentation",
    icon: BookOpen,
    color: "#2563EB",
    bg: "#EFF6FF",
    emoji: "👤",
    topics: [
      { id: "upload-data",      label: "How to Upload Data" },
      { id: "create-project",   label: "How to Create a Project" },
      { id: "book-session",     label: "How to Book a Session" },
      { id: "use-ide",          label: "Using the IDE" },
      { id: "run-code",         label: "Running Code on a Robot" },
      { id: "view-video",       label: "Viewing Live Robot Feed" },
    ],
  },
  {
    id: "developer",
    label: "Developer Documentation",
    icon: Code2,
    color: "#7C3AED",
    bg: "#F5F3FF",
    emoji: "🧑‍💻",
    topics: [
      { id: "api-overview",     label: "API Overview" },
      { id: "authentication",   label: "Authentication" },
      { id: "bookings-api",     label: "Bookings API" },
      { id: "robots-api",       label: "Robots API" },
      { id: "community-api",    label: "Community API" },
      { id: "json-structure",   label: "JSON Structure Reference" },
    ],
  },
  {
    id: "product",
    label: "Product Documentation",
    icon: BarChart3,
    color: "#059669",
    bg: "#ECFDF5",
    emoji: "📊",
    topics: [
      { id: "features",         label: "Features Overview" },
      { id: "use-cases",        label: "Use Cases" },
      { id: "architecture",     label: "System Architecture" },
      { id: "roles",            label: "Roles & Permissions" },
    ],
  },
];

// ─── Topic content map ─────────────────────────────────────────────────────────

const CONTENT = {

  /* ── User docs ───────────────────────────────────────────────── */

  "upload-data": {
    title: "How to Upload Data",
    icon: Upload,
    body: [
      {
        type: "intro",
        text: "You can upload your robot code and data files directly into your personal workspace through the built-in IDE (Eclipse Theia). Every user has a private, persistent workspace that survives across sessions.",
      },
      {
        type: "steps",
        title: "Uploading via the IDE",
        items: [
          "Log in and click <strong>Projects</strong> in the navbar to open the booking page.",
          "Click <strong>Open IDE</strong> under the \"Development Environment\" card — this is always available, no booking required.",
          "In the IDE file tree on the left, right-click the folder where you want to upload.",
          "Select <strong>Upload Files…</strong> from the context menu.",
          "Choose your files from your computer. They are saved immediately to your workspace.",
        ],
      },
      {
        type: "steps",
        title: "Uploading via drag-and-drop",
        items: [
          "Open the IDE panel.",
          "Drag any file from your desktop and drop it into the IDE file tree.",
          "The file appears in your workspace and persists across sessions.",
        ],
      },
      {
        type: "note",
        text: "Supported file types: .py, .cpp, .h, .launch, .yaml, .json, .txt, .md. Maximum file size: 50 MB.",
      },
    ],
  },

  "create-project": {
    title: "How to Create a Project",
    icon: FolderPlus,
    body: [
      {
        type: "intro",
        text: "Projects in Anybot are folders inside your personal workspace. You create and manage them directly in the IDE — no separate project-creation step is needed.",
      },
      {
        type: "steps",
        title: "Creating a new project folder",
        items: [
          "Open the IDE from the Projects page.",
          "In the file tree, right-click any empty area and select <strong>New Folder</strong>.",
          "Give the folder a meaningful name, e.g. <code>turtlebot_slam</code>.",
          "Inside the folder, create your source files (<strong>New File</strong>) or upload existing ones.",
          "Your project is saved automatically and available every time you open the IDE.",
        ],
      },
      {
        type: "steps",
        title: "Recommended project structure",
        items: [
          "<code>my_project/src/</code> — Python or C++ source files",
          "<code>my_project/launch/</code> — ROS 2 launch files",
          "<code>my_project/config/</code> — YAML parameter files",
          "<code>my_project/README.md</code> — notes and instructions",
        ],
      },
      {
        type: "note",
        text: "Each booking session mounts the same workspace, so code written in preview mode is immediately available when a booked session starts.",
      },
    ],
  },

  "book-session": {
    title: "How to Book a Session",
    icon: null,
    body: [
      {
        type: "intro",
        text: "Booking a session gives you real-time access to a physical or simulated robot. During a session you can execute code and view the live video feed.",
      },
      {
        type: "steps",
        title: "Step-by-step booking",
        items: [
          "Click <strong>Projects</strong> in the navbar.",
          "In the <strong>Book a Session</strong> wizard, choose a robot type (TurtleBot, Robot Arm, etc.).",
          "Pick a date on the calendar — past dates are disabled.",
          "Select an available time slot.",
          "Review the session summary, then click <strong>Confirm & Launch Console</strong>.",
          "The console opens automatically with your booking IDE active.",
        ],
      },
      {
        type: "note",
        text: "Sessions are 1 hour by default. Credits are deducted on confirmation. You can view upcoming and past sessions in the \"My Sessions\" section below the booking wizard.",
      },
    ],
  },

  "use-ide": {
    title: "Using the IDE",
    icon: null,
    body: [
      {
        type: "intro",
        text: "Anybot embeds Eclipse Theia — a full VS Code-compatible browser IDE — directly in the console. It is available 24/7 regardless of whether you have an active booking.",
      },
      {
        type: "steps",
        title: "Key IDE features",
        items: [
          "<strong>File tree</strong> — create, rename, delete, and upload files via right-click.",
          "<strong>Code editor</strong> — syntax highlighting for Python, C++, YAML, and more.",
          "<strong>Integrated terminal</strong> — run shell commands inside your container.",
          "<strong>Extension support</strong> — install VS Code-compatible extensions from the marketplace.",
          "<strong>Preview vs Booking mode</strong> — preview uses a lightweight image; booking uses the full ROS 2 image set by the admin.",
        ],
      },
      {
        type: "note",
        text: "Your workspace at /home/project is persisted. Even if the container restarts, your files remain.",
      },
    ],
  },

  "run-code": {
    title: "Running Code on a Robot",
    icon: null,
    body: [
      {
        type: "intro",
        text: "Code execution on a real or simulated robot requires an active booking. In preview mode, the Run button is visible but disabled as a reminder.",
      },
      {
        type: "steps",
        title: "Running your code",
        items: [
          "Book a session and wait for it to start.",
          "Open the console — the IDE will automatically switch to the booking (ROS 2) image.",
          "Write or open your code in the IDE.",
          "Use the file picker in the top bar to select a <code>.py</code> or <code>.cpp</code> file.",
          "Click <strong>🚀 Run Code on Robot</strong>.",
          "The backend reads the file from your workspace and pushes it to the robot endpoint.",
          "Monitor execution results via the live video feed on the right panel.",
        ],
      },
      {
        type: "note",
        text: "Currently supported languages: Python 3 and C++. The robot type is auto-detected from your active booking.",
      },
    ],
  },

  "view-video": {
    title: "Viewing Live Robot Feed",
    icon: null,
    body: [
      {
        type: "intro",
        text: "Live video is streamed via WebRTC directly from the robot's camera to your browser. This is only available during an active booking session.",
      },
      {
        type: "steps",
        title: "Accessing the feed",
        items: [
          "Start a booked session and enter the console.",
          "The right panel shows the live video player automatically.",
          "If the stream doesn't start, click <strong>Get Real Result</strong> below the video panel.",
          "Drag the center divider to resize the IDE and video panels.",
          "Use the toolbar buttons to expand either panel to full width.",
        ],
      },
      {
        type: "note",
        text: "WebRTC requires a stable internet connection. If you experience buffering, check your network and try reloading the page.",
      },
    ],
  },

  /* ── Developer docs ──────────────────────────────────────────── */

  "api-overview": {
    title: "API Overview",
    icon: Network,
    body: [
      {
        type: "intro",
        text: "The Anybot REST API is built with FastAPI and follows standard HTTP conventions. All endpoints are prefixed with the server base URL (e.g. https://anybot.brainswarmrobotics.com).",
      },
      {
        type: "table",
        title: "Base URL",
        rows: [
          ["Environment", "Base URL"],
          ["Production", "https://anybot.brainswarmrobotics.com"],
          ["Local dev", "http://localhost:8000"],
        ],
      },
      {
        type: "table",
        title: "Core endpoint groups",
        rows: [
          ["Prefix", "Description"],
          ["/auth/*", "Registration, login, Google/GitHub OAuth, password reset"],
          ["/bookings/*", "Create, list, manage time-slot bookings"],
          ["/robots/*", "Robot registry — list and details"],
          ["/theia/*", "IDE container management (start, stop, status, logs)"],
          ["/community/*", "Public posts and replies"],
          ["/admin/*", "Admin-only endpoints"],
          ["/health/*", "System health and feature flags"],
        ],
      },
      {
        type: "note",
        text: "All responses are JSON. Errors follow the format: { \"detail\": \"Error message\" } with appropriate HTTP status codes.",
      },
    ],
  },

  "authentication": {
    title: "Authentication",
    icon: Key,
    body: [
      {
        type: "intro",
        text: "Anybot uses JWT (JSON Web Token) Bearer authentication. Every protected endpoint requires an Authorization header.",
      },
      {
        type: "code",
        title: "Login request",
        lang: "http",
        code: `POST /auth/login
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "yourpassword"
}`,
      },
      {
        type: "code",
        title: "Login response",
        lang: "json",
        code: `{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 42,
    "name": "Jane Smith",
    "email": "you@example.com",
    "role": "user"
  }
}`,
      },
      {
        type: "code",
        title: "Using the token in subsequent requests",
        lang: "http",
        code: `GET /bookings
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`,
      },
      {
        type: "steps",
        title: "OAuth flows",
        items: [
          "<strong>Google (GIS redirect mode)</strong> — Browser posts credential to /auth/google/callback, then frontend exchanges one-time code via POST /auth/google/exchange",
          "<strong>GitHub</strong> — redirect user to GitHub, receive ?code=xxx, POST /auth/github with { \"code\": \"xxx\" }",
          "Both return the same response shape as /auth/login.",
        ],
      },
      {
        type: "note",
        text: "Tokens do not expire by default in development. In production, configure JWT_EXPIRE_HOURS in the backend .env.",
      },
    ],
  },

  "bookings-api": {
    title: "Bookings API",
    icon: null,
    body: [
      {
        type: "intro",
        text: "The bookings API lets users reserve time slots on specific robots.",
      },
      {
        type: "table",
        title: "Endpoints",
        rows: [
          ["Method", "Path", "Description"],
          ["GET",    "/bookings", "List your bookings"],
          ["POST",   "/bookings", "Create a new booking"],
          ["GET",    "/bookings/available-slots?date=&robot_id=", "Available time slots for a date + robot"],
          ["GET",    "/bookings/all", "All bookings (admin only)"],
          ["PUT",    "/bookings/{id}", "Update booking status (admin)"],
          ["DELETE", "/bookings/{id}", "Delete a booking (admin)"],
        ],
      },
      {
        type: "code",
        title: "Create booking — request body",
        lang: "json",
        code: `{
  "robot_id": 3,
  "robot_type": "turtlebot",
  "date": "2026-05-10",
  "start_time": "10:00",
  "end_time": "11:00"
}`,
      },
      {
        type: "code",
        title: "Booking object",
        lang: "json",
        code: `{
  "id": 17,
  "user_id": 42,
  "robot_id": 3,
  "robot_type": "turtlebot",
  "date": "2026-05-10",
  "start_time": "10:00:00",
  "end_time": "11:00:00",
  "status": "active",
  "created_at": "2026-04-24T08:12:00"
}`,
      },
    ],
  },

  "robots-api": {
    title: "Robots API",
    icon: Cpu,
    body: [
      {
        type: "intro",
        text: "The robots registry stores every robot's metadata including the Docker image used for its booking IDE.",
      },
      {
        type: "table",
        title: "Endpoints",
        rows: [
          ["Method", "Path", "Description"],
          ["GET",    "/robots", "List all active robots (public)"],
          ["GET",    "/admin/robots", "Full robot list (admin)"],
          ["POST",   "/admin/robots", "Create a robot (admin)"],
          ["PUT",    "/admin/robots/{id}", "Update a robot (admin)"],
          ["DELETE", "/admin/robots/{id}", "Delete a robot (admin)"],
        ],
      },
      {
        type: "code",
        title: "Robot object",
        lang: "json",
        code: `{
  "id": 3,
  "name": "TurtleBot Alpha",
  "type": "turtlebot",
  "webrtc_url": "https://rtc.example.com/turtlebot",
  "rtsp_url": "rtsp://192.168.1.10:8554/stream",
  "upload_endpoint": "https://robot.example.com/upload",
  "container_image": "muneeb/theia-ros-humble:v2",
  "status": "active"
}`,
      },
      {
        type: "note",
        text: "container_image controls which Docker image the booking IDE uses for this robot. Set it in the Admin → Robot Registry panel.",
      },
    ],
  },

  "community-api": {
    title: "Community API",
    icon: Users,
    body: [
      {
        type: "intro",
        text: "The community API powers the public discussion board.",
      },
      {
        type: "table",
        title: "Endpoints",
        rows: [
          ["Method", "Path", "Description"],
          ["GET",    "/community/posts?page=1&limit=20", "Paginated posts"],
          ["POST",   "/community/posts", "Create a post"],
          ["GET",    "/community/posts/{id}/replies", "Get replies for a post"],
          ["POST",   "/community/posts/{id}/reply", "Reply to a post"],
          ["DELETE", "/community/posts/{id}", "Delete post (own or admin)"],
          ["DELETE", "/community/replies/{id}", "Delete reply (own or admin)"],
          ["GET",    "/community/leaderboard", "Top 10 users by message count"],
          ["GET",    "/admin/community/users", "All users with block status (admin)"],
          ["PATCH",  "/admin/community/users/{id}/block", "Block / unblock user (admin)"],
        ],
      },
      {
        type: "code",
        title: "Post object",
        lang: "json",
        code: `{
  "id": 1,
  "user_id": 42,
  "user_name": "Jane Smith",
  "content": "Hello community!",
  "reply_count": 3,
  "total_messages": 27,
  "rank_info": {
    "rank": "Member",
    "emoji": "🔵",
    "color": "#2563EB"
  },
  "created_at": "2026-04-24T09:00:00"
}`,
      },
    ],
  },

  "json-structure": {
    title: "JSON Structure Reference",
    icon: Database,
    body: [
      {
        type: "intro",
        text: "All API requests and responses use JSON. Here are the key object shapes used across the API.",
      },
      {
        type: "code",
        title: "User object",
        lang: "json",
        code: `{
  "id": 42,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "role": "user",           // "user" | "admin"
  "is_active": true,
  "community_blocked": false,
  "created_at": "2026-01-01T00:00:00"
}`,
      },
      {
        type: "code",
        title: "Error response",
        lang: "json",
        code: `{
  "detail": "Human-readable error message"
}`,
      },
      {
        type: "code",
        title: "Paginated list response",
        lang: "json",
        code: `{
  "posts": [ /* array of objects */ ],
  "total": 142,
  "page": 1,
  "limit": 20
}`,
      },
      {
        type: "table",
        title: "Common HTTP status codes",
        rows: [
          ["Code", "Meaning"],
          ["200", "OK — request succeeded"],
          ["201", "Created — resource was created"],
          ["400", "Bad Request — invalid input"],
          ["401", "Unauthorized — missing or invalid token"],
          ["403", "Forbidden — insufficient permissions"],
          ["404", "Not Found — resource does not exist"],
          ["500", "Server Error — something unexpected happened"],
        ],
      },
    ],
  },

  /* ── Product docs ────────────────────────────────────────────── */

  "features": {
    title: "Features Overview",
    icon: Zap,
    body: [
      {
        type: "intro",
        text: "Anybot is a cloud robotics education platform that gives STEM students hands-on access to real ROS 2 environments through a browser.",
      },
      {
        type: "feature-grid",
        items: [
          { emoji: "🤖", title: "Robot Booking", desc: "Reserve time slots on TurtleBots, robot arms, and humanoid robots through a step-by-step wizard." },
          { emoji: "💻", title: "Browser IDE", desc: "Eclipse Theia IDE embedded in the browser — write, edit, and run robot code without installing anything." },
          { emoji: "📹", title: "Live Video Feed", desc: "WebRTC streaming delivers real-time camera feed from the robot directly to your browser." },
          { emoji: "🐳", title: "Per-User Containers", desc: "Each user gets an isolated Docker container with their own persistent workspace." },
          { emoji: "💬", title: "Community", desc: "Public discussion board with a ranking system based on contributions." },
          { emoji: "🔐", title: "OAuth Login", desc: "Sign in with email, Google, or GitHub. Email confirmation and password reset included." },
          { emoji: "🛡️", title: "Admin Dashboard", desc: "Manage users, robots, bookings, containers, announcements, and community moderation." },
          { emoji: "📊", title: "Real-Time Logs", desc: "View live Docker container logs for both preview and booking IDE containers." },
        ],
      },
    ],
  },

  "use-cases": {
    title: "Use Cases",
    icon: null,
    body: [
      {
        type: "intro",
        text: "Anybot is designed for STEM education environments where students need access to robotics hardware and simulation without complex local setup.",
      },
      {
        type: "steps",
        title: "🏫 University courses",
        items: [
          "Students book time slots on shared TurtleBots for ROS 2 labs.",
          "Instructors use the admin dashboard to manage bookings and view student containers.",
          "All code is saved in each student's private workspace — no USB drives needed.",
        ],
      },
      {
        type: "steps",
        title: "🏠 Remote learners",
        items: [
          "Learners access real robots from home over a browser — no local ROS installation required.",
          "The preview IDE lets students write and test code any time, even without a booking.",
          "Live video feed makes it possible to observe the robot's behavior in real time.",
        ],
      },
      {
        type: "steps",
        title: "🧪 Research labs",
        items: [
          "Researchers book sessions on specific robot configurations set up by the admin.",
          "Custom Docker images per robot mean each robot can have its own ROS stack.",
          "Admin can watch any user's container in real time for support or assessment.",
        ],
      },
    ],
  },

  "architecture": {
    title: "System Architecture",
    icon: Network,
    body: [
      {
        type: "intro",
        text: "Anybot follows a three-tier architecture: a React frontend, a FastAPI backend, and a Docker-based container layer — all deployed on a single VPS.",
      },
      {
        type: "table",
        title: "Components",
        rows: [
          ["Layer", "Technology", "Role"],
          ["Frontend", "React 18 + Chakra UI + Vite", "Browser-based UI — booking, IDE, community, admin"],
          ["Backend", "FastAPI (Python 3.10)", "REST API, auth, booking logic, container orchestration"],
          ["Database", "MySQL", "Users, bookings, robots, community posts, settings"],
          ["IDE Containers", "Docker (elswork/theia, ROS 2 images)", "Per-user isolated workspaces"],
          ["Video", "WebRTC / RTSP bridge", "Real-time robot camera streaming"],
          ["Email", "Resend", "Confirmation, password reset, notifications"],
          ["Reverse Proxy", "Nginx", "Routes /theia/<port>/ and /api/ to backend services"],
        ],
      },
      {
        type: "steps",
        title: "Container lifecycle",
        items: [
          "On login, the backend pre-warms the user's <strong>preview container</strong> (elswork/theia) in the background.",
          "On booking confirmation, the backend starts a <strong>booking container</strong> using the admin-configured Docker image for that robot.",
          "Both containers mount the same user workspace directory (<code>/projects/{user_id}/</code>) so code is shared.",
          "Containers are cleaned up after a configurable idle timeout (default 2 hours).",
        ],
      },
      {
        type: "note",
        text: "All container names follow the pattern theia-preview-{user_id} and theia-booking-{user_id}, ensuring strict per-user isolation.",
      },
    ],
  },

  "roles": {
    title: "Roles & Permissions",
    icon: Users,
    body: [
      {
        type: "intro",
        text: "Anybot has two roles: user and admin. Role is stored in the users table and encoded in the JWT.",
      },
      {
        type: "table",
        title: "Permission matrix",
        rows: [
          ["Action", "User", "Admin"],
          ["Browse and book robots", "✅", "✅"],
          ["Open IDE (preview)", "✅", "✅"],
          ["Run code during booking", "✅", "✅"],
          ["View own container logs", "✅", "✅"],
          ["Post in community", "✅ (if not blocked)", "✅"],
          ["Delete own posts/replies", "✅", "✅"],
          ["Delete any post/reply", "❌", "✅"],
          ["View all users", "❌", "✅"],
          ["Manage robots", "❌", "✅"],
          ["Manage bookings", "❌", "✅"],
          ["Watch user containers", "❌", "✅"],
          ["Block community users", "❌", "✅"],
          ["Change admin settings", "❌", "✅"],
        ],
      },
      {
        type: "note",
        text: "Admin role is assigned via the Admin Dashboard → Users section. There must always be at least one admin account.",
      },
    ],
  },
};

// ─── Renderers ──────────────────────────────────────────────────────────────

const BlockIntro = ({ text }) => <p className="docs-intro">{text}</p>;

const BlockSteps = ({ title, items }) => (
  <div className="docs-block">
    {title && <h3 className="docs-block-title">{title}</h3>}
    <ol className="docs-steps">
      {items.map((item, i) => (
        <li key={i} dangerouslySetInnerHTML={{ __html: item }} />
      ))}
    </ol>
  </div>
);

const BlockNote = ({ text }) => (
  <div className="docs-note">
    <span className="docs-note-icon">💡</span>
    <span>{text}</span>
  </div>
);

const BlockCode = ({ title, code }) => (
  <div className="docs-block">
    {title && <h3 className="docs-block-title">{title}</h3>}
    <pre className="docs-code"><code>{code}</code></pre>
  </div>
);

const BlockTable = ({ title, rows }) => (
  <div className="docs-block">
    {title && <h3 className="docs-block-title">{title}</h3>}
    <div className="docs-table-wrap">
      <table className="docs-table">
        <thead>
          <tr>{rows[0].map((h, i) => <th key={i}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(1).map((row, i) => (
            <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const BlockFeatureGrid = ({ items }) => (
  <div className="docs-feature-grid">
    {items.map((f, i) => (
      <div key={i} className="docs-feature-card">
        <div className="docs-feature-emoji">{f.emoji}</div>
        <div className="docs-feature-title">{f.title}</div>
        <div className="docs-feature-desc">{f.desc}</div>
      </div>
    ))}
  </div>
);

const renderBlock = (block, i) => {
  switch (block.type) {
    case "intro":        return <BlockIntro key={i} text={block.text} />;
    case "steps":        return <BlockSteps key={i} title={block.title} items={block.items} />;
    case "note":         return <BlockNote key={i} text={block.text} />;
    case "code":         return <BlockCode key={i} title={block.title} code={block.code} />;
    case "table":        return <BlockTable key={i} title={block.title} rows={block.rows} />;
    case "feature-grid": return <BlockFeatureGrid key={i} items={block.items} />;
    default:             return null;
  }
};

// ─── Main component ──────────────────────────────────────────────────────────

const DocsPage = ({ user, authToken, onLogout, onNavigate, onAdminAccess }) => {
  const [activeSection, setActiveSection] = useState("user");
  const [activeTopic, setActiveTopic]     = useState("upload-data");
  const [collapsed, setCollapsed]         = useState({});
  const [search, setSearch]               = useState("");

  const currentSection = SECTIONS.find((s) => s.id === activeSection);
  const content        = CONTENT[activeTopic];

  const toggleSection = (id) =>
    setCollapsed((prev) => ({ ...prev, [id]: !prev[id] }));

  const handleTopic = (sectionId, topicId) => {
    setActiveSection(sectionId);
    setActiveTopic(topicId);
  };

  // Filter topics by search
  const filtered = search.trim()
    ? SECTIONS.map((s) => ({
        ...s,
        topics: s.topics.filter((t) =>
          t.label.toLowerCase().includes(search.toLowerCase())
        ),
      })).filter((s) => s.topics.length > 0)
    : SECTIONS;

  return (
    <div className="docs-page">
      <Navbar
        user={user}
        onNavigate={onNavigate}
        currentPage="docs"
        onLogout={onLogout}
        onAdminAccess={onAdminAccess}
      />

      <div className="docs-layout">

        {/* ── Sidebar ──────────────────────────────────────────── */}
        <aside className="docs-sidebar">
          <div className="docs-search-wrap">
            <Search size={14} className="docs-search-icon" />
            <input
              className="docs-search"
              placeholder="Search docs…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {filtered.map((section) => {
            const Icon = section.icon;
            const isOpen = !collapsed[section.id];
            return (
              <div key={section.id} className="docs-nav-section">
                <button
                  className={`docs-nav-section-btn ${activeSection === section.id ? "active" : ""}`}
                  style={activeSection === section.id ? { color: section.color } : {}}
                  onClick={() => toggleSection(section.id)}
                >
                  <span className="docs-nav-section-left">
                    <Icon size={15} />
                    <span>{section.label}</span>
                  </span>
                  {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                </button>

                {isOpen && (
                  <div className="docs-nav-topics">
                    {section.topics.map((topic) => (
                      <button
                        key={topic.id}
                        className={`docs-nav-topic ${activeTopic === topic.id ? "active" : ""}`}
                        style={activeTopic === topic.id ? { color: section.color, borderColor: section.color, background: section.bg } : {}}
                        onClick={() => handleTopic(section.id, topic.id)}
                      >
                        {topic.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </aside>

        {/* ── Content ──────────────────────────────────────────── */}
        <main className="docs-content">
          {content ? (
            <>
              {/* Breadcrumb */}
              <div className="docs-breadcrumb">
                <span style={{ color: currentSection?.color }}>{currentSection?.emoji} {currentSection?.label}</span>
                <ChevronRight size={13} />
                <span>{content.title}</span>
              </div>

              {/* Title */}
              <h1 className="docs-content-title">{content.title}</h1>
              <div className="docs-content-divider" style={{ background: currentSection?.color }} />

              {/* Body blocks */}
              <div className="docs-body">
                {content.body.map((block, i) => renderBlock(block, i))}
              </div>

              {/* Nav arrows */}
              <div className="docs-content-nav">
                {(() => {
                  const allTopics = SECTIONS.flatMap((s) =>
                    s.topics.map((t) => ({ ...t, sectionId: s.id }))
                  );
                  const idx = allTopics.findIndex((t) => t.id === activeTopic);
                  const prev = allTopics[idx - 1];
                  const next = allTopics[idx + 1];
                  return (
                    <>
                      {prev ? (
                        <button className="docs-nav-arrow" onClick={() => handleTopic(prev.sectionId, prev.id)}>
                          <ArrowLeft size={14} /> {prev.label}
                        </button>
                      ) : <span />}
                      {next ? (
                        <button className="docs-nav-arrow docs-nav-arrow--right" onClick={() => handleTopic(next.sectionId, next.id)}>
                          {next.label} <ChevronRight size={14} />
                        </button>
                      ) : <span />}
                    </>
                  );
                })()}
              </div>
            </>
          ) : (
            <div className="docs-empty">Select a topic from the sidebar.</div>
          )}
        </main>

      </div>
    </div>
  );
};

export default DocsPage;
