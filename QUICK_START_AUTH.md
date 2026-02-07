# Quick Start: Email Confirmation & Google OAuth

## 1. Setup Environment

Add to `.env`:
```bash
# Required
SECRET_KEY=your-secret-key-here

# Email (optional but recommended)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=your-email@gmail.com

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com

# Server
SERVER_HOST=http://localhost:8000
```

## 2. User Registration Flow

**Before:**
```
POST /auth/register → JWT token returned immediately
```

**After:**
```
POST /auth/register → Confirmation email sent, no JWT
User checks email → Clicks confirmation link
GET /auth/confirm?token=... → Account activated
POST /auth/login → JWT token returned
```

## 3. Google OAuth Flow

```
Frontend obtains Google ID token
POST /auth/google {id_token: "..."} → JWT token returned
User logged in immediately (no email confirmation needed)
```

## 4. Testing

```bash
# Start server
cd backend && uvicorn main:app --reload

# Test registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@example.com","password":"pass123"}'

# Use confirm_url from response
curl http://localhost:8000/auth/confirm?token={TOKEN}

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

## 5. Key Files Modified

- `backend/database.py` - Added columns, methods
- `backend/services/auth_service.py` - Updated auth logic
- `backend/services/token_service.py` - NEW
- `backend/services/mail_service.py` - NEW
- `backend/main.py` - Updated routes
- `backend/requirements.txt` - Added dependencies
- `.env.template` - Added config

## 6. Database Changes

Auto-migrated on startup:
- `is_active` - Account activation status
- `email_confirmed_at` - Confirmation timestamp
- `google_id` - Google user ID
- `google_name` - Google display name

## 7. Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| 403: Email not confirmed | User hasn't clicked confirmation link | Check email, resend if needed |
| 400: Token expired | Confirmation link > 1 hour old | Request new confirmation email |
| 401: Invalid Google token | Google token verification failed | Re-authenticate with Google |

## 8. Demo Users

Demo users bypass email confirmation:
- `demo@user.com` / `password`
- `admin@demo.com` / `password`

## 9. Gmail Setup (Quick)

1. Google Account → Security → 2-Step Verification (enable)
2. App Passwords → Generate new → Copy
3. Use in MAIL_PASSWORD

## 10. Google OAuth Setup (Quick)

1. [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID
4. Add origins: `http://localhost:3000`
5. Copy Client ID → GOOGLE_CLIENT_ID

## Done! 🎉

Your authentication system now has:
- ✅ Email confirmation for new users
- ✅ Secure time-limited tokens
- ✅ Google OAuth login
- ✅ Account activation tracking
- ✅ Blocking unconfirmed users
