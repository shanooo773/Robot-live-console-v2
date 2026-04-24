import { useState, useRef, useEffect } from "react";
import { Bot, Bell, ChevronDown, LayoutDashboard, CalendarDays, BookOpen, FileText, Users, LogOut, Settings } from "lucide-react";

const Navbar = ({ user, onNavigate, currentPage, onLogout, onAdminAccess }) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const navLinks = [
    { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { key: "booking", label: "Projects", icon: CalendarDays },
    { key: "tutorials", label: "Tutorials", icon: BookOpen },
    { key: "docs", label: "Docs", icon: FileText },
    { key: "community", label: "Community", icon: Users },
  ];

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  return (
    <nav className="anybot-navbar">
      <div className="anybot-navbar__inner">
        {/* Logo */}
        <div className="anybot-navbar__logo" onClick={() => onNavigate("dashboard")}>
          <div className="anybot-navbar__logo-icon">
            <Bot size={18} color="white" />
          </div>
          <span className="anybot-navbar__logo-text">Anybot</span>
        </div>

        {/* Nav Links */}
        <div className="anybot-navbar__links">
          {navLinks.map((link) => (
            <button
              key={link.key}
              className={`anybot-navbar__link ${currentPage === link.key ? "active" : ""}`}
              onClick={() => {
                if (["dashboard", "booking", "community", "docs"].includes(link.key)) {
                  onNavigate(link.key);
                }
              }}
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* Right Side */}
        <div className="anybot-navbar__right">
          <button className="anybot-navbar__bell">
            <Bell size={18} />
          </button>

          <div className="anybot-navbar__avatar-wrap" ref={dropdownRef}>
            <button
              className="anybot-navbar__avatar"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <span>{initials}</span>
              <ChevronDown size={14} />
            </button>

            {dropdownOpen && (
              <div className="anybot-navbar__dropdown">
                <div className="anybot-navbar__dropdown-header">
                  <div className="anybot-navbar__dropdown-name">{user?.name}</div>
                  <div className="anybot-navbar__dropdown-email">{user?.email}</div>
                </div>
                <div className="anybot-navbar__dropdown-divider" />
                <button className="anybot-navbar__dropdown-item" onClick={() => { onNavigate("dashboard"); setDropdownOpen(false); }}>
                  <LayoutDashboard size={15} /> Dashboard
                </button>
                <button className="anybot-navbar__dropdown-item" onClick={() => { onNavigate("booking"); setDropdownOpen(false); }}>
                  <CalendarDays size={15} /> Projects
                </button>
                {onAdminAccess && (
                  <button className="anybot-navbar__dropdown-item" onClick={() => { onAdminAccess(); setDropdownOpen(false); }}>
                    <Settings size={15} /> Admin Panel
                  </button>
                )}
                <div className="anybot-navbar__dropdown-divider" />
                <button className="anybot-navbar__dropdown-item danger" onClick={() => { onLogout(); setDropdownOpen(false); }}>
                  <LogOut size={15} /> Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
