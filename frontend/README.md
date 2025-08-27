# Frontend Configuration for Separated Architecture

The frontend has been updated to work with the separated backend architecture:

## API Configuration

### Dual Backend Setup
The frontend now communicates with two separate services:

```javascript
// Admin backend API (authentication and booking)
const ADMIN_API = axios.create({
  baseURL: "http://localhost:8000",
});

// Simulation service API (robot simulation)
const SIMULATION_API = axios.create({
  baseURL: "http://localhost:8001",
});
```

### API Routing

**Admin Backend Endpoints (Port 8000):**
- Authentication: `/auth/*`
- Booking: `/bookings/*`
- Admin: `/admin/*`
- Health: `/health`

**Simulation Service Endpoints (Port 8001):**
- Code execution: `/run-code`
- Robot information: `/robots`
- Video files: `/videos/*`
- Health: `/health`

## Component Updates

### No UI/UX Changes Required
All React components remain exactly the same:
- `LandingPage.jsx` - Unchanged
- `AuthPage.jsx` - Unchanged
- `BookingPage.jsx` - Unchanged  
- `CodeEditor.jsx` - Unchanged
- `RobotSelector.jsx` - Unchanged
- `VideoPlayer.jsx` - Unchanged

### Automatic Service Detection
The frontend will automatically:
1. Route authentication/booking requests to admin backend
2. Route simulation requests to simulation service
3. Show appropriate error messages if services are unavailable
4. Maintain all existing functionality

## Development Mode

Start all services for development:

```bash
# Terminal 1 - Admin Backend
cd admin-backend
source venv/bin/activate
python main.py

# Terminal 2 - Simulation Service  
cd simulation-service
source venv/bin/activate
python main.py

# Terminal 3 - Frontend
cd frontend
npm run dev
```

## Production Deployment

### Environment Variables
Set different URLs for production:

```javascript
const ADMIN_API = axios.create({
  baseURL: process.env.REACT_APP_ADMIN_API || "http://localhost:8000",
});

const SIMULATION_API = axios.create({
  baseURL: process.env.REACT_APP_SIMULATION_API || "http://localhost:8001",
});
```

### Environment Files
```bash
# .env.production
REACT_APP_ADMIN_API=https://admin.robotconsole.com
REACT_APP_SIMULATION_API=https://simulation.robotconsole.com
```

## Error Handling

The frontend gracefully handles service unavailability:

- **Admin Backend Down**: User sees authentication/booking errors
- **Simulation Service Down**: Code execution shows "service unavailable" message
- **Both Services Running**: Full functionality available

## Testing

Test the frontend configuration:
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The frontend will work correctly as long as at least the admin backend is running. Simulation features will be disabled gracefully if the simulation service is unavailable.