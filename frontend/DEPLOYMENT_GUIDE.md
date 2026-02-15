# Frontend Deployment Guide

## Prerequisites
- Node.js 18+ installed
- npm installed
- Backend API running and accessible
- Google OAuth credentials (if using Google Sign-In)

## Environment Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and configure:
```env
# API Configuration
VITE_API_URL=https://anybot.brainswarmrobotics.com

# Google OAuth Configuration (optional)
VITE_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
```

### Getting Google OAuth Client ID (Optional)

If you want to enable Google Sign-In:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure consent screen with your app details
6. Add authorized JavaScript origins:
   - `http://localhost:5173` (for development)
   - `https://your-domain.com` (for production)
7. Add authorized redirect URIs (same as origins)
8. Copy the Client ID and paste it in `.env`

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

This starts the development server at http://localhost:5173

## Production Build

```bash
npm run build
```

This creates optimized production files in the `dist/` directory.

## Deployment

### Option 1: Nginx (Recommended)

1. Build the frontend:
```bash
npm run build
```

2. Copy built files to nginx directory:
```bash
sudo cp -r dist/* /var/www/html/
```

3. Configure nginx to serve the files and proxy API requests:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/html;
    index index.html;

    # Serve static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

4. Restart nginx:
```bash
sudo systemctl restart nginx
```

### Option 2: Docker

Create a `Dockerfile` in the frontend directory:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t robot-console-frontend .
docker run -p 80:80 robot-console-frontend
```

## Post-Deployment Checklist

- [ ] Verify `.env` is configured correctly
- [ ] Test login with email/password
- [ ] Test Google Sign-In (if enabled)
- [ ] Test forgot password flow
- [ ] Test admin dashboard access
- [ ] Test user management features (admin only)
- [ ] Verify API endpoints are accessible
- [ ] Check browser console for errors
- [ ] Test on mobile devices

## Troubleshooting

### API Connection Issues

If you see CORS errors or connection issues:

1. Check `VITE_API_URL` in `.env`
2. Verify backend is running and accessible
3. Check backend CORS configuration
4. Check nginx proxy configuration

### Google Sign-In Not Working

1. Verify `VITE_GOOGLE_CLIENT_ID` is set
2. Check that Google Sign-In script loads (check browser console)
3. Verify authorized origins in Google Cloud Console
4. Check that you're using HTTPS in production (required by Google)

### Build Errors

If build fails:

1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` again
3. Check Node.js version (should be 18+)

### Console Errors in Production

Common issues:

1. **"N.map is not a function"** - Fixed in this PR (API response handling)
2. **"Token validation failed: 500"** - Fixed in this PR (error interceptor)
3. **Mixed content errors** - Ensure HTTPS is used for all resources

## Updating

To update to a new version:

```bash
cd frontend
git pull
npm install
npm run build
sudo cp -r dist/* /var/www/html/
```

## Support

For issues or questions, please open an issue on the GitHub repository.
