# Google Authentication Refactor — GIS Callback Mode

## Summary

Replaced the previous **redirect-mode** Google Identity Services (GIS) implementation with **callback mode**. The old flow sent the user to `https://anybot.brainswarmrobotics.com/auth/google/callback`, causing nonce state loss and validation failures. The new flow uses a JavaScript callback directly in the browser, sends the ID token securely to the backend, and receives a JWT in the same HTTP response — no page redirects, no tokens in URLs.

---

## What Changed

### Frontend

#### `frontend/src/components/AuthPage.jsx`
- **Removed** `GOOGLE_LOGIN_URI` and `GOOGLE_NONCE_STORAGE_KEY` constants.
- **Removed** `ensureGoogleNonce()` function (used sessionStorage + cookie for redirect-state nonce).
- **Added** `googleNonceRef` (`useRef`) — nonce is now generated with `crypto.randomUUID()` and kept in memory for the lifetime of the component.
- **Added** `handleGoogleResponse(response)` — GIS callback that POSTs `{credential, nonce}` to `POST /auth/google` and calls `onAuth` on success.
- **Changed** GIS initialization:
  - Removed `ux_mode: "redirect"` and `login_uri`.
  - Added `callback: handleGoogleResponse` and in-memory `nonce`.

#### `frontend/src/api.js`
- **Removed** `googleExchangeCode` (called `POST /auth/google/exchange`).
- **Added** `googleLogin(credential, nonce)` — calls `POST /auth/google` with JSON `{ credential, nonce }`.

#### `frontend/src/App.jsx`
- **Removed** `googleExchangeCode` import.
- **Removed** `google_code` URL parameter handling (no longer produced by backend).
- **Removed** `google_error` URL parameter handling (no longer produced by backend).

### Backend

#### `backend/main.py`
- **Removed** global variables: `GOOGLE_REDIRECT_URI`, `GOOGLE_AUTH_CODE_TTL_SECONDS`, `google_auth_exchange_store`, `google_auth_exchange_lock`.
- **Removed** unused imports: `threading.Lock`, `fastapi.Form`, `fastapi.responses.RedirectResponse`.
- **Removed** Pydantic model: `GoogleExchangeRequest`.
- **Removed** endpoint `POST /auth/google/callback` (redirect-mode handler with 302 responses).
- **Removed** endpoint `POST /auth/google/exchange` (one-time code exchange).
- **Added** Pydantic model: `GoogleLogin(credential: str, nonce: str)`.
- **Added** endpoint `POST /auth/google` — receives `{credential, nonce}`, calls `auth_service.login_with_google`, returns JWT directly (`TokenResponse`).

#### `backend/services/auth_service.py`
No changes required — `login_with_google(id_token, expected_nonce)` already supports nonce validation using `hmac.compare_digest`.

---

## Authentication Flow (New)

```
Browser                         FastAPI Backend
  |                                  |
  |-- GIS initializes (callback) --> |
  |   nonce = crypto.randomUUID()    |
  |   stored in googleNonceRef       |
  |                                  |
  | <-- User clicks Google button -- |
  |   GIS shows Google sign-in UI    |
  |   (popup or One Tap)             |
  |                                  |
  | <-- GIS calls handleGoogleResponse(response) -->
  |   credential = response.credential (ID token)  |
  |   POST /auth/google {credential, nonce}         |
  |                                  |
  |     verify_oauth2_token(id_token)|
  |     compare nonce                |
  |     issue app JWT <--------------+
  |                                  |
  | store JWT, navigate to dashboard |
```

---

## Environment Variables

No new environment variables are required.

| Variable | Where used | Notes |
|---|---|---|
| `VITE_GOOGLE_CLIENT_ID` | Frontend (`AuthPage.jsx`) | GIS `client_id` |
| `GOOGLE_CLIENT_ID` | Backend (`auth_service.py`) | Token verification audience |

**`GOOGLE_CLIENT_SECRET` is NOT used** in this GIS flow (GIS callback mode does not require it).

---

## Commands the User Must Run

### Frontend
```bash
cd frontend
npm install   # no new packages required; existing deps are sufficient
npm run build
```

### Backend
```bash
# No new Python packages required.
# google-auth is already a dependency.
# Restart the backend after deploying:
sudo systemctl restart robot-console-backend
```

### Google Cloud Console
Update **Authorized JavaScript origins** for your OAuth 2.0 Client ID to include your app's domain (e.g., `https://anybot.brainswarmrobotics.com`).

You can **remove** the previously registered Authorized redirect URI:
```
https://anybot.brainswarmrobotics.com/auth/google/callback
```
It is no longer used.

---

## Backward Compatibility

- All other existing backend endpoints are **unchanged**.
- GitHub OAuth flow is **unchanged**.
- Email/password login is **unchanged**.
- Database schema is **unchanged**.
- Session/JWT creation logic in `auth_service.py` is **unchanged**.

---

## Dummy / Placeholder Data

**There is no dummy or placeholder data in this implementation.**

All Google user information (email, name, `sub`) is extracted from the verified Google ID token. No hardcoded values are used.

---

## Security Notes

- The ID token is verified server-side using `google.oauth2.id_token.verify_oauth2_token` against Google's public keys.
- The nonce is generated fresh per login attempt using `crypto.randomUUID()` and stored only in a React `useRef` (in-memory, not persisted).
- The nonce is compared inside the verified token claims (`idinfo.get("nonce")`) using `hmac.compare_digest` to prevent timing attacks.
- No `client_secret` is used or exposed.
- No tokens or sensitive data appear in URLs.
