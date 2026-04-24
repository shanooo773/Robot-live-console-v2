# UI Update Report — Anybot Frontend Redesign

## 1. Summary of Changes

The frontend has been redesigned to match the reference images in `new_ui_images/`, replacing the previous glassmorphism/dark-card look with a clean, light "frosted glass" system using soft blue gradients, white cards, rounded corners, and consistent spacing. All new pages integrate with existing backend endpoints — no backend routes, schemas, or business logic were modified.

| Area | Before | After |
|------|--------|-------|
| Auth pages | Single centred card on blurred background | Split layout: left hero + right form card |
| Dashboard | Not implemented | Full dashboard with stats, projects list, booking widget, quick access |
| Booking | Not implemented | 4-step flow: Select Robot → Pick Date → Choose Time → Confirm |
| Project Detail | Not implemented | Session history, simulation playback panel, code versions panel |
| Dev Console | Not implemented | Theia iframe wrapper with dark topbar and status indicator |
| Authentication | Mock (no API calls) | Real JWT via `/auth/login` and `/auth/register`; token persisted in `localStorage` |
| Theme | Ad-hoc CSS variables per file | Centralised design-token CSS (`src/styles/theme.css`) |

---

## 2. File-by-File Changes

### New Files Added (Frontend)

| File | Purpose |
|------|---------|
| `src/services/api.ts` | Single API service layer — all `fetch` calls, token injection, typed responses |
| `src/styles/theme.css` | Global CSS custom properties (colours, radii, shadows, typography, utility classes) |
| `src/styles/dashboard.css` | Dashboard page styles |
| `src/styles/booking.css` | Multi-step booking page styles |
| `src/styles/project.css` | Project detail page styles |
| `src/styles/console.css` | Dev Console (Theia wrapper) styles |
| `src/components/Navbar.tsx` | Shared authenticated navbar (logo, links, avatar dropdown, logout) |
| `src/components/Navbar.css` | Navbar styles |
| `src/components/ProtectedRoute.tsx` | Auth guard — redirects unauthenticated users to `/login` |
| `src/pages/Dashboard.tsx` | Main dashboard (stats, projects, booking widget, quick access) |
| `src/pages/Booking.tsx` | Multi-step booking flow |
| `src/pages/ProjectDetail.tsx` | Per-session project detail with history table |
| `src/pages/DevConsole.tsx` | Theia IDE wrapper with dark topbar |
| `src/pages/ForgotPassword.tsx` | Forgot password form (calls `/auth/forgot-password`) |
| `.env` | `VITE_API_URL=http://172.232.105.47:8000` |

### Modified Files (Frontend)

| File | What Changed |
|------|-------------|
| `src/App.tsx` | Added routes: `/forgot`, `/dashboard`, `/booking`, `/project/:id`, `/console`; wrapped protected routes with `<ProtectedRoute>` |
| `src/context/AppContext.tsx` | Added `user: UserData \| null`, `isAuthLoading`, real `login(token, user)` that writes to `localStorage`, real `logout()` that clears storage, bootstrap `useEffect` that calls `/auth/me` on load |
| `src/pages/Login.tsx` | Rebuilt with split layout; calls real `authLogin()` API; shows inline error messages |
| `src/pages/Signup.tsx` | Rebuilt with split layout; calls real `authRegister()` API; shows success state with email-confirm message |
| `src/styles/login.css` | Completely rewritten for split-panel auth layout |
| `src/index.css` | Now imports `./styles/theme.css` |
| `vite.config.ts` | Added optional `server.proxy` entry for local development |

### Backend — No Changes

Zero backend files were modified. The backend (`/backend/`) is untouched.

---

## 3. New Routes Added

| Path | Component | Auth Required |
|------|-----------|---------------|
| `/` | `Home` | No |
| `/login` | `Login` | No |
| `/signup` | `Signup` | No |
| `/forgot` | `ForgotPassword` | No |
| `/dashboard` | `Dashboard` | **Yes** |
| `/booking` | `Booking` | **Yes** |
| `/project/:id` | `ProjectDetail` | **Yes** |
| `/console` | `DevConsole` | **Yes** |

---

## 4. API Endpoints Used (Existing — No New Endpoints)

| Endpoint | Method | Used by |
|----------|--------|---------|
| `/auth/login` | POST | Login page |
| `/auth/register` | POST | Signup page |
| `/auth/me` | GET | AppContext bootstrap, ProtectedRoute |
| `/auth/forgot-password` | POST | ForgotPassword page |
| `/robots` | GET | Dashboard, Booking |
| `/bookings` | GET | Dashboard, ProjectDetail |
| `/my-bookings` | GET | Dashboard (active session indicator) |
| `/bookings` | POST | Dashboard widget, Booking page |
| `/bookings/available-slots` | GET | Dashboard widget, Booking page |
| `/theia/status` | GET | DevConsole |
| `/theia/start` | POST | DevConsole (fallback/demo) |
| `/theia/booking/start` | POST | DevConsole, ProjectDetail |
| `/theia/booking/stop` | POST | DevConsole, ProjectDetail |

---

## 5. Environment Variables

| Variable | Value | Required |
|----------|-------|---------|
| `VITE_API_URL` | `http://172.232.105.47:8000` | Yes — set in `.env` |

To change the backend URL, edit `Anybot_Frontend/anybot/.env`:
```
VITE_API_URL=https://your-backend-host:8000
```

---

## 6. Commands to Run

### Development
```bash
cd Anybot_Frontend/anybot
npm install          # only if node_modules missing
npm run dev          # starts Vite dev server on http://localhost:5173
```

### Production Build
```bash
cd Anybot_Frontend/anybot
npm run build        # TypeScript check + Vite bundle → dist/
npm run preview      # Preview the production build locally
```

### No database migrations required.

---

## 7. Backend Compatibility Confirmation

- **No backend files were modified.**
- All existing routes, models, services, and DB schema are 100% intact.
- The frontend calls existing endpoints only (`/auth/*`, `/robots`, `/bookings`, `/my-bookings`, `/bookings/available-slots`, `/theia/*`).
- No new backend endpoints were added.
- Existing admin dashboard and admin API routes continue to function unchanged.
- The Theia iframe integration is preserved: `DevConsole.tsx` iframes the URL returned by `/theia/booking/start` or `/theia/start`, identical to any prior Theia integration.

---

## 8. Dummy / Placeholder Data Statement

**No hardcoded dummy data was added.** The strict policy was followed throughout:

| Location | What is shown | Data source |
|----------|--------------|-------------|
| Dashboard stats | Real counts from `/bookings` response | Live API |
| Dashboard projects | Real bookings sorted by `created_at` | Live API |
| Dashboard booking widget | Real available slots from `/bookings/available-slots` | Live API |
| Booking page robots | Real robots from `/robots` | Live API |
| Booking time slots | Real slots from `/bookings/available-slots` | Live API |
| Project detail — session history | Real bookings filtered by robot type | Live API |
| Project detail — simulation playback | **Empty state** (no fake video) — message: "Recording available after a completed session" | N/A |
| Project detail — code versions | **Empty state** — message: "Version history is stored inside the Theia workspace" | N/A |
| Dev Console | Real Theia URL from `/theia/status` or `/theia/booking/start` | Live API |

### Empty States (not placeholders)

Two panels show empty/informational states because the backend does not expose that data:

1. **Simulation Playback panel** (`ProjectDetail.tsx`): Shows a "No recording available" placeholder with an icon. This is a real empty state — no fake video URL or progress data. The panel is ready to display a `<video>` element once a stream URL is available.

2. **Code Versions panel** (`ProjectDetail.tsx`): Shows "Version history is stored inside the Theia workspace" with a link to open the console. Code versioning lives inside the Theia container file system and is not exposed via a backend API. No fake version entries are shown.

Neither of these is behind a feature flag — they are permanent empty states, not development placeholders.

---

## 9. Design Tokens Reference

Defined in `src/styles/theme.css`:

```css
--primary:       #2563EB   /* Tailwind blue-600 */
--primary-dark:  #1D4ED8
--primary-light: #DBEAFE
--primary-bg:    #EFF6FF
--bg:            #F0F4FF   /* page background */
--radius-lg:     16px      /* card radius */
--shadow-md:     0 4px 16px rgba(0,0,0,0.08)
--font-sans:     'Inter', system-ui
```
