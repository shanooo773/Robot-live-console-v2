#!/bin/bash

echo "🚀 Final Video Endpoint Validation"
echo "=================================="

# Test 1: Login and get JWT token
echo ""
echo "1. Getting JWT token..."
LOGIN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"email": "demo@user.com", "password": "password"}' \
  http://localhost:8000/auth/login)

if [[ $? -eq 0 ]]; then
  JWT_TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
  
  if [[ -n "$JWT_TOKEN" ]]; then
    echo "✅ JWT token obtained: ${JWT_TOKEN:0:20}..."
  else
    echo "❌ Failed to extract JWT token"
    exit 1
  fi
else
  echo "❌ Login request failed"
  exit 1
fi

# Test 2: Create completed booking
echo ""
echo "2. Creating completed booking..."
curl -s -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"robot_type": "turtlebot", "date": "2024-01-20", "start_time": "10:00", "end_time": "11:00"}' \
  http://localhost:8000/bookings > /dev/null

# Login as admin and complete the booking
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"email": "admin@demo.com", "password": "password"}' \
  http://localhost:8000/auth/login)

ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

# Get the latest booking ID and mark it completed
BOOKINGS_RESPONSE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/bookings/all)

LATEST_BOOKING_ID=$(echo $BOOKINGS_RESPONSE | python3 -c "
import sys, json
bookings = json.load(sys.stdin)
if bookings:
    print(max(bookings, key=lambda b: b['id'])['id'])
" 2>/dev/null)

if [[ -n "$LATEST_BOOKING_ID" ]]; then
  curl -s -X PUT -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"status": "completed"}' \
    http://localhost:8000/bookings/$LATEST_BOOKING_ID > /dev/null
  echo "✅ Booking $LATEST_BOOKING_ID marked as completed"
else
  echo "⚠️  Using existing completed booking"
fi

# Test 3: Test video endpoints
echo ""
echo "3. Testing video endpoints..."

for robot_type in turtlebot arm hand; do
  echo "   Testing $robot_type..."
  
  response=$(curl -s -w "%{http_code}" -o /dev/null \
    -H "Authorization: Bearer $JWT_TOKEN" \
    http://localhost:8000/videos/$robot_type)
  
  if [[ "$response" == "200" ]]; then
    echo "   ✅ $robot_type: HTTP 200 (accessible)"
  elif [[ "$response" == "403" ]]; then
    echo "   🔒 $robot_type: HTTP 403 (access denied - expected for arm/hand)"
  else
    echo "   ⚠️  $robot_type: HTTP $response"
  fi
done

# Test 4: Test CORS preflight
echo ""
echo "4. Testing CORS preflight..."
cors_response=$(curl -s -w "%{http_code}" -o /dev/null \
  -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  http://localhost:8000/videos/turtlebot)

if [[ "$cors_response" == "200" ]]; then
  echo "✅ CORS preflight: HTTP 200"
else
  echo "❌ CORS preflight: HTTP $cors_response"
fi

# Test 5: Test without authentication
echo ""
echo "5. Testing without authentication (should fail)..."
no_auth_response=$(curl -s -w "%{http_code}" -o /dev/null \
  http://localhost:8000/videos/turtlebot)

if [[ "$no_auth_response" == "403" ]]; then
  echo "✅ No auth: HTTP 403 (correctly denied)"
elif [[ "$no_auth_response" == "401" ]]; then
  echo "✅ No auth: HTTP 401 (correctly denied)"
else
  echo "⚠️  No auth: HTTP $no_auth_response (unexpected)"
fi

# Test 6: Verify file exists and is readable
echo ""
echo "6. Verifying video files..."
cd /home/runner/work/Robot-live-console-v2/Robot-live-console-v2/backend

for video in turtlebot_simulation.mp4 arm_simulation.mp4 hand_simulation.mp4; do
  if [[ -f "videos/$video" ]]; then
    size=$(stat -c%s "videos/$video")
    echo "✅ $video: exists ($size bytes)"
  else
    echo "❌ $video: missing"
  fi
done

echo ""
echo "=================================="
echo "🎯 Final validation completed!"
echo "=================================="