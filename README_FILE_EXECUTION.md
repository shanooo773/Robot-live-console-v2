# File Execution Feature - Quick Start Guide

## Overview
This feature allows users to select and execute both Python (.py) and C++ (.cpp) files from their workspace directly on the robot.

## For Users

### How to Use
1. **Login** to the Robot Console
2. **Wait for IDE** to start (happens automatically)
3. **Create or edit files** in the Theia IDE
4. **Click the file dropdown** next to "Run Code" button
5. **Select your file** (Python or C++)
6. **Click "Run Code"** to execute on the robot

### Visual Guide

**File Selector Location:**
```
┌────────────────────────────────────────────────────────┐
│  [🐍 robot_control.py ▼] [🔄]  [🚀 Run Code]         │
│   ↑                      ↑      ↑                      │
│   File selector          Refresh  Execute button       │
└────────────────────────────────────────────────────────┘
```

**File Type Indicators:**
- 🐍 = Python file (.py)
- 🔧 = C++ file (.cpp)

**Color Badges:**
- Green = Python
- Orange = C++

### Tips
- Use the **refresh button (🔄)** after creating new files
- Files in subdirectories are supported
- First file is auto-selected when available
- Can only run code with active booking (Preview mode allows IDE editing only)

## For Developers

### Quick Reference

**New Backend Endpoints:**
```
GET  /theia/workspace/files          - List all .py and .cpp files
GET  /theia/workspace/file/{path}    - Get specific file content
```

**Updated Frontend Components:**
```
FileSelector.jsx           - NEW component for file selection
NeonRobotConsole.jsx       - Updated with file selection logic
```

**Data Flow:**
```
User → FileSelector → loadWorkspaceFiles() → Backend API
                   ↓
              Select File
                   ↓
User → Run Code → handleRunCode() → Fetch file content → Backend /robot/execute
```

### Code Example

**Send code to robot:**
```javascript
const response = await fetch('/robot/execute', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    robot_type: "turtlebot",
    code: actualFileContent,      // Real code from workspace
    language: "python",            // or "cpp"
    filename: "robot_control.py"  // Actual filename
  })
});
```

### Files Modified
- `backend/main.py` (+64 lines)
- `frontend/src/components/NeonRobotConsole.jsx` (+83 lines)
- `frontend/src/components/FileSelector.jsx` (NEW, +78 lines)

## Documentation

### Available Documents
1. **BEFORE_AFTER_COMPARISON.md** - Visual comparison of changes
2. **FILE_EXECUTION_FEATURE.md** - Technical architecture
3. **UI_CHANGES.md** - UI/UX specifications
4. **IMPLEMENTATION_SUMMARY.md** - Complete implementation details
5. **README_FILE_EXECUTION.md** - This quick start guide

## Troubleshooting

### No files showing up?
- Wait for Theia IDE to finish starting
- Click the refresh button (🔄)
- Check that you have .py or .cpp files in your workspace

### "No file selected" error?
- Select a file from the dropdown before clicking "Run Code"

### File not executing?
- Check if you have an active booking (Preview mode only allows editing)
- Verify the file still exists in your workspace

### Wrong code executing?
- Click refresh button to reload the file list
- Check that you selected the correct file in the dropdown

## Security

- All endpoints require authentication
- File access restricted to user's workspace only
- Path traversal attacks prevented
- Maximum file size: 100KB

## Testing

**Frontend Build:**
```bash
cd frontend
npm install
npm run build
```

**Backend Syntax Check:**
```bash
cd backend
python3 -m py_compile main.py
```

## Support

For issues or questions:
1. Check the documentation files listed above
2. Review the code comments in modified files
3. Check the backend logs for API errors
4. Verify network requests in browser DevTools

## Version Info

- Feature: File Execution (Python & C++)
- Version: 1.0
- Date: 2024
- Status: Production Ready ✅

---

**Quick Links:**
- [Technical Details](FILE_EXECUTION_FEATURE.md)
- [UI Changes](UI_CHANGES.md)
- [Before/After](BEFORE_AFTER_COMPARISON.md)
- [Implementation](IMPLEMENTATION_SUMMARY.md)
