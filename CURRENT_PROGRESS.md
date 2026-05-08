# CURRENT PROGRESS

## New Replit-style Learning Development Console UX
- Post-login flow now lands users directly in the **Development Console**.
- The console keeps existing IDE/video behavior and adds a dedicated learning experience.

## Left Learning Panel
- Added a collapsible **left learning panel** in the development console.
- Panel includes:
  - Course title: **ROS2 Foundation**
  - Lesson list with completion status
  - Markdown lesson content viewer
  - Progress indicator (`x/8`)
  - Per-lesson complete/incomplete toggle button
- Includes loading/error handling for lesson and progress requests.

## Per-Lesson Progress Saved in Backend
- Progress is tracked **per lesson** (no per-step checkboxes).
- Progress is saved to backend storage and returned via authenticated API.
- Uses existing JWT auth to identify users.

## Post-Login Redirect to Console
- Successful login and session restore now route to the development console (editor view), not dashboard.
- Protected app pages redirect unauthenticated users to login.

## New Endpoints
- `GET /learning/courses/ros2-foundation/lessons`
  - Returns course lesson metadata list (up to 8 lessons from ROS2 Foundations files).
- `GET /learning/courses/ros2-foundation/lessons/{lesson_id}`
  - Returns lesson markdown content.
- `GET /learning/progress?course_id=ros2-foundation`
  - Returns current user completion state.
- `PUT /learning/progress` (also accepts `POST`)
  - Upserts a lesson completion state:
  - Body:
    ```json
    {
      "course_id": "ros2-foundation",
      "lesson_id": "<lesson_id>",
      "completed": true
    }
    ```

## How to Test
1. Login with a valid user.
2. Confirm app opens directly in Development Console.
3. Confirm left learning panel loads ROS2 Foundation lessons and markdown content.
4. Mark a lesson complete/incomplete and verify progress count updates.
5. Reload and log in from another device/browser session:
   - completion state should persist from backend.
