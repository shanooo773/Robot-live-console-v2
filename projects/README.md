# User Project Directories

This directory contains individual project folders for each user of the Robot Console.

## Structure

```
projects/
├── -1/              # Demo user project folder (demo@user.com)
├── -2/              # Demo admin project folder (admin@demo.com)
├── user_1/          # Project folder for user ID 1
├── user_2/          # Project folder for user ID 2
├── user_123/        # Project folder for user ID 123
└── ...
```

## Demo Users

The system includes two demo users with pre-configured workspaces:

- **Demo User** (ID: -1)
  - Email: demo@user.com
  - Password: password
  - Workspace: `projects/-1/`

- **Demo Admin** (ID: -2)  
  - Email: admin@demo.com
  - Password: password
  - Workspace: `projects/-2/`

## Features

- **Isolation**: Each user has their own isolated project directory
- **Persistence**: All files and changes are preserved between sessions
- **Mount Point**: Folders are mounted into Theia containers at `/home/project`
- **Default Files**: New users get welcome examples in Python and C++

## Automatic Management

Project folders are created automatically when:
1. A user logs in and requests their Theia container
2. The backend API starts a new container for the user
3. The start-user-container.sh script is executed

## Security

- Each folder is only accessible to the respective user's container
- No cross-user access to project files
- All file operations are contained within the user's folder

## Future Enhancements

- [ ] Git repository initialization for each project
- [ ] Automated backups of project folders
- [ ] Project templates for different robot types
- [ ] Version history tracking