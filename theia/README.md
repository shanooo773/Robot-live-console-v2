# Eclipse Theia Docker Setup

This directory contains the Docker configuration for running Eclipse Theia IDE instances for each user.

## Files

- `Dockerfile`: Base Theia image with Python, C++, Git, and Terminal extensions
- `docker-compose.yml`: Base service configuration
- `start-user-container.sh`: Script to start per-user Theia containers

## Features

- **Pre-installed Extensions**: Python, C++, Git, Terminal, File Explorer
- **Multi-user Support**: Each user gets their own isolated container
- **Project Persistence**: User projects are mounted from `/projects/<user_id>/`
- **Security**: Containers run with limited privileges

## Usage

Containers are managed automatically by the backend API. Each user gets:
- Unique container name: `theia-user-<user_id>`
- Project folder mounted at `/home/project`
- Theia IDE accessible via iframe in frontend

## Future Enhancements

- [ ] Resource limits per container
- [ ] Git-based version history
- [ ] Extension marketplace integration
- [ ] Collaborative editing support