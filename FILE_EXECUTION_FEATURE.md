# File Execution Feature: Python and C++ Support

## Overview
This update enhances the "Run Code" functionality to support both Python (.py) and C++ (.cpp) files. Users can now select files from their active workspace and execute them on the robot.

## Changes Made

### Backend Changes

#### 1. New API Endpoints (`backend/main.py`)

**List Workspace Files**
```
GET /theia/workspace/files
```
- Lists all `.py` and `.cpp` files in the user's workspace
- Returns file metadata including name, path, and language type
- Recursively searches subdirectories

**Get File Content**
```
GET /theia/workspace/file/{file_path}
```
- Retrieves the content of a specific file
- Includes security checks to prevent path traversal attacks
- Returns file content as JSON

#### 2. Enhanced Robot Execute Endpoint
The existing `/robot/execute` endpoint already supports:
- `filename`: Name of the file being executed
- `language`: Language type ("python" or "cpp")
- `code`: Actual code content
- `robot_type`: Type of robot to execute on

### Frontend Changes

#### 1. New Component: FileSelector (`frontend/src/components/FileSelector.jsx`)
- Dropdown menu to select Python or C++ files
- Visual indicators for file types (🐍 for Python, 🔧 for C++)
- Badge showing language type
- Refresh button to reload file list
- Handles loading states

#### 2. Updated NeonRobotConsole Component (`frontend/src/components/NeonRobotConsole.jsx`)

**New State Variables:**
- `workspaceFiles`: Array of available files
- `selectedFile`: Currently selected file
- `filesLoading`: Loading state for file operations

**New Functions:**
- `loadWorkspaceFiles()`: Fetches list of available files from workspace
- Updated `handleRunCode()`: 
  - Validates file selection
  - Fetches actual file content from workspace
  - Sends correct language, filename, and code to backend

**UI Updates:**
- Added FileSelector component next to "Run Code" button
- Auto-loads files when Theia IDE is running
- Displays file selection status

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface (Frontend)                    │
├─────────────────────────────────────────────────────────────────┤
│  NeonRobotConsole Component                                      │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ FileSelector   │  │ Run Code Btn │  │ Theia IDE Frame  │   │
│  │ 🐍 file.py     │  │   🚀         │  │ [Monaco Editor]  │   │
│  │ 🔧 file.cpp    │  │              │  │                  │   │
│  └────────────────┘  └──────────────┘  └──────────────────┘   │
└───────────┬──────────────┬──────────────────────────────────────┘
            │              │
            │ GET          │ POST
            │ /theia/      │ /robot/execute
            │ workspace/   │ {code, language,
            │ files        │  filename, robot_type}
            │              │
┌───────────▼──────────────▼──────────────────────────────────────┐
│                      Backend API Server                          │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Routes                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ GET /theia/workspace/files                              │   │
│  │ → Lists .py and .cpp files in user workspace           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ GET /theia/workspace/file/{path}                        │   │
│  │ → Returns file content from workspace                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ POST /robot/execute                                      │   │
│  │ → Validates booking                                      │   │
│  │ → Reads code from workspace (if filename provided)      │   │
│  │ → Uploads to robot via upload_endpoint                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────┬──────────────────────────────────────────────────────┘
            │
            │ Access filesystem
            │
┌───────────▼──────────────────────────────────────────────────────┐
│                    Theia Workspace Storage                        │
├───────────────────────────────────────────────────────────────────┤
│  /projects/{user_id}/                                             │
│  ├── robot_control.py                                             │
│  ├── robot_control.cpp                                            │
│  └── examples/                                                    │
│      └── demo.py                                                  │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Action → Frontend → Backend → Robot
    ↓           ↓          ↓         ↓
 Select      Fetch      Read      Execute
 File        Content    File      Code
  ↓           ↓          ↓         ↓
Display     Show in    Send      Return
Info        Dropdown   to API    Result
```

## Usage Flow

1. **User logs in** and accesses the Robot Console
2. **Theia IDE starts** automatically
3. **File list loads** showing all .py and .cpp files in workspace
4. **User selects a file** from the dropdown
5. **User clicks "Run Code"** button
6. **System fetches file content** from workspace
7. **Code is sent to robot** with correct:
   - Language type (python/cpp)
   - Filename
   - Actual code content
   - Robot type
8. **Backend executes code** on the assigned robot

## Security Features

- **Authentication required**: All endpoints require valid JWT token
- **Path traversal protection**: File access is restricted to user's workspace
- **Filename sanitization**: Backend sanitizes filenames before processing
- **File size limits**: Maximum 100KB code file size

## Example Files

### Python Example (`robot_control.py`)
```python
#!/usr/bin/env python3
def main():
    print("Starting robot control...")
    # Robot control logic here
    print("Moving forward...")
    print("Robot control completed!")

if __name__ == "__main__":
    main()
```

### C++ Example (`robot_control.cpp`)
```cpp
#include <iostream>

int main() {
    std::cout << "Starting robot control..." << std::endl;
    // Robot control logic here
    std::cout << "Moving forward..." << std::endl;
    return 0;
}
```

## Error Handling

The system handles various error scenarios:
- **No file selected**: Warning toast prompts user to select a file
- **File not found**: Error if file doesn't exist in workspace
- **File read error**: Error if file cannot be read
- **Booking required**: Warning if user tries to execute without booking
- **Theia not running**: Auto-starts Theia IDE if not running

## Technical Details

### File Path Encoding
- Proper URL encoding for file paths with subdirectories
- Uses split/map/join approach to handle slashes correctly

### Language Detection
- Automatic based on file extension
- `.py` → `language: "python"`
- `.cpp` → `language: "cpp"`

### Backend File Loading
The backend has two ways to get code:
1. **From request**: Direct code string in POST body
2. **From workspace**: If filename provided, attempts to load from user's workspace directory first

## Testing

To test the feature:
1. Create Python and C++ files in your workspace
2. Verify files appear in the dropdown
3. Select a file and click "Run Code"
4. Check that the correct code is sent to the robot
5. Verify language parameter matches file type

## Future Enhancements

Potential improvements:
- Support for more languages (.c, .h, .java, .js)
- File upload functionality
- Code editor preview before execution
- Execution history
- Multi-file project support
