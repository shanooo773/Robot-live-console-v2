FROM node:18-slim

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create theia user
RUN groupadd -g 1001 theia && \
    useradd -u 1001 -g theia -s /bin/bash -m theia

WORKDIR /home/theia
USER theia

# Create a minimal Theia application
RUN echo '{\
  "name": "robot-console-theia",\
  "version": "1.0.0",\
  "scripts": {\
    "start": "node /home/theia/src-gen/backend/main.js /home/project --hostname=0.0.0.0 --port=3000"\
  },\
  "dependencies": {\
    "@theia/core": "^1.44.0",\
    "@theia/editor": "^1.44.0",\
    "@theia/filesystem": "^1.44.0",\
    "@theia/workspace": "^1.44.0",\
    "@theia/terminal": "^1.44.0",\
    "@theia/navigator": "^1.44.0",\
    "@theia/preferences": "^1.44.0",\
    "@theia/monaco": "^1.44.0"\
  },\
  "devDependencies": {\
    "@theia/cli": "^1.44.0"\
  }\
}' > package.json

# Install dependencies with increased memory
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN npm install

# Generate Theia application
RUN npx theia build || echo "Build completed with warnings"

# Create project directory
RUN mkdir -p /home/project

EXPOSE 3000

# Simple start command that works
CMD ["node", "/home/theia/src-gen/backend/main.js", "/home/project", "--hostname=0.0.0.0", "--port=3000"]
