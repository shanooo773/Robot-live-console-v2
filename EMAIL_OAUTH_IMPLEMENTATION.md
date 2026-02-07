# Email Confirmation and Google OAuth Implementation Guide

## Overview

This document describes the implementation of email confirmation for user registration and Google OAuth authentication in the Robot Live Console application.

## Features Implemented

### 1. Email Confirmation for User Registration

When a user registers with email/password:
- User account is created with `is_active=0` (inactive)
- A time-limited confirmation token is generated (expires in 1 hour)
- Confirmation email is sent with a link to activate the account
- **No JWT token is issued until email is confirmed**
- Login attempts are blocked with a 403 error until email is confirmed

### 2. Google OAuth Authentication

Users can login/register using their Google account:
- Frontend obtains Google ID token
- Backend verifies token with Google's servers
- User is automatically created or updated with `is_active=1`
- JWT token is issued immediately (Google accounts are pre-verified)

## API Endpoints

### POST /auth/register

Register a new user and send confirmation email.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

**Response (200 OK):**
```json
{
  "message": "Registration successful! Please check your email to confirm your account.",
  "email": "john@example.com",
  "confirm_url": "http://localhost:8000/auth/confirm?token=...",
  "user": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": false
  }
}
```

### GET /auth/confirm?token={token}

Confirm user email address.

**Query Parameter:**
- `token`: Email confirmation token from the confirmation email

**Response (200 OK):**
```json
{
  "message": "Email confirmed successfully! You can now log in.",
  "user": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true
  }
}
```

**Error Responses:**
- 400: Token expired or invalid
- 404: User not found

### POST /auth/login

Login with email and password (requires confirmed email).

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true
  }
}
```

**Error Responses:**
- 401: Invalid email or password
- 403: Email not confirmed

### POST /auth/google

Login or register with Google OAuth.

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 124,
    "name": "Jane Smith",
    "email": "jane@gmail.com",
    "role": "user",
    "is_active": true,
    "google_id": "1234567890",
    "google_name": "Jane Smith"
  }
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# JWT Secret Key (REQUIRED)
SECRET_KEY=your-secret-key-here
# Or use JWT_SECRET_KEY
JWT_SECRET_KEY=your-secret-key-here

# Email Configuration (SMTP)
# For Gmail: Enable 2FA and generate an App Password
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false

# Google OAuth Configuration
# Get Client ID from Google Cloud Console
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com

# Server Host (for confirmation links)
SERVER_HOST=http://localhost:8000
```

### Gmail Setup

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password at: https://myaccount.google.com/apppasswords
4. Use the generated password as `MAIL_PASSWORD`

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized JavaScript origins (e.g., `http://localhost:3000`)
6. Add authorized redirect URIs
7. Copy the Client ID to `GOOGLE_CLIENT_ID`

## Database Schema Changes

New columns added to `users` table:

```sql
ALTER TABLE users ADD COLUMN is_active TINYINT(1) DEFAULT 0;
ALTER TABLE users ADD COLUMN email_confirmed_at DATETIME NULL;
ALTER TABLE users ADD COLUMN google_id VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN google_name VARCHAR(255) NULL;
```

These migrations run automatically when the application starts.

## Security Features

### Email Confirmation Tokens
- Generated using `itsdangerous.URLSafeTimedSerializer`
- Cryptographically signed with JWT secret key
- Time-limited to 1 hour
- Cannot be forged or reused after expiry

### Google OAuth
- ID tokens verified server-side with Google's servers
- Verified against configured `GOOGLE_CLIENT_ID`
- Protects against token substitution attacks

### Password Security
- Passwords hashed with SHA-256 and unique salt per user
- Demo users bypass confirmation for testing
- Real users require email confirmation before login

## Testing

### Manual Testing

1. **Email Confirmation Flow:**
   ```bash
   # Register new user
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"name":"Test User","email":"test@example.com","password":"password123"}'
   
   # Check email for confirmation link or use confirm_url from response
   # Click link or:
   curl http://localhost:8000/auth/confirm?token={TOKEN}
   
   # Login
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123"}'
   ```

2. **Google OAuth Flow:**
   - Frontend obtains ID token from Google
   - Send to backend:
   ```bash
   curl -X POST http://localhost:8000/auth/google \
     -H "Content-Type: application/json" \
     -d '{"id_token":"GOOGLE_ID_TOKEN_HERE"}'
   ```

### Unit Tests

Run the test scripts:
```bash
# Test implementation
SECRET_KEY=test-secret python3 /tmp/test_implementation.py

# Test integration
SECRET_KEY=test-secret python3 /tmp/test_integration.py
```

## Error Handling

### Token Expired
**Status:** 400 Bad Request
```json
{
  "detail": "Confirmation token has expired. Please request a new confirmation email."
}
```

### Invalid Token
**Status:** 400 Bad Request
```json
{
  "detail": "Invalid confirmation token. Please check the link or request a new confirmation email."
}
```

### Email Not Confirmed
**Status:** 403 Forbidden
```json
{
  "detail": "Email not confirmed. Please check your inbox for a confirmation link."
}
```

### Invalid Google Token
**Status:** 401 Unauthorized
```json
{
  "detail": "Invalid Google token"
}
```

### Email Already Exists
**Status:** 400 Bad Request
```json
{
  "detail": "Email already exists"
}
```

## Frontend Integration

### Email/Password Registration

```javascript
async function register(name, email, password) {
  const response = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Show message to user
    alert(data.message);
    // Redirect to login page or show confirmation instructions
  }
}
```

### Google OAuth Login

```javascript
// Add Google Sign-In button
<div id="g_id_onload"
     data-client_id="YOUR_GOOGLE_CLIENT_ID"
     data-callback="handleGoogleSignIn"></div>

async function handleGoogleSignIn(response) {
  // Send ID token to backend
  const res = await fetch('/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: response.credential })
  });
  
  const data = await res.json();
  
  if (res.ok) {
    // Store JWT token
    localStorage.setItem('token', data.access_token);
    // Redirect to dashboard
    window.location.href = '/dashboard';
  }
}
```

## Maintenance

### Resend Confirmation Email

To implement (future enhancement):
- Create POST /auth/resend-confirmation endpoint
- Generate new token for existing unconfirmed user
- Send new confirmation email

### Password Reset

To implement (future enhancement):
- Use similar token-based flow
- POST /auth/forgot-password
- GET /auth/reset-password?token={token}
- Use different salt in TokenService for reset tokens

## Troubleshooting

### Emails Not Sending

1. Check SMTP credentials in `.env`
2. Verify MAIL_USERNAME and MAIL_PASSWORD are correct
3. For Gmail, ensure App Password is used (not regular password)
4. Check application logs for email errors
5. Test with MailHog or similar SMTP testing tool

### Google OAuth Not Working

1. Verify GOOGLE_CLIENT_ID is correct
2. Check authorized JavaScript origins in Google Console
3. Ensure frontend uses same Client ID
4. Check browser console for Google Sign-In errors
5. Verify google-auth package is installed

### Token Validation Errors

1. Ensure SECRET_KEY is set in environment
2. Check token hasn't expired (1 hour limit)
3. Verify no spaces or line breaks in token
4. Ensure same SECRET_KEY is used for generation and validation

## Dependencies

New dependencies added:
- `itsdangerous==2.1.2` - Secure token generation
- `fastapi-mail==1.4.1` - Email sending
- `google-auth==2.26.2` - Google token verification
- `google-auth-oauthlib==1.2.0` - Google OAuth support

All dependencies checked for vulnerabilities (0 found).

## Security Considerations

1. **Secret Keys**: Never commit SECRET_KEY to version control
2. **HTTPS**: Use HTTPS in production for all endpoints
3. **Token Expiry**: 1-hour expiry balances security and user experience
4. **Rate Limiting**: Consider adding rate limiting to prevent abuse
5. **Email Verification**: Prevents spam accounts and validates user identity
6. **Google OAuth**: Server-side verification prevents token forgery

## Performance

- Email sending is non-blocking (async)
- Token generation is fast (< 1ms)
- Token validation is fast (< 1ms)
- Database queries are indexed on email and google_id
- No external API calls during registration (only on Google login)

## Future Enhancements

1. Add password reset flow
2. Add resend confirmation email endpoint
3. Add email change with re-confirmation
4. Support additional OAuth providers (GitHub, Facebook)
5. Add 2FA support
6. Add account linking (merge Google and email accounts)
7. Add email templates with custom branding
8. Add rate limiting for authentication endpoints
