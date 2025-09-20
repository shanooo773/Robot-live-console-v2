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

# Copy Theia configuration files (from the local theia directory)
COPY --chown=theia:theia package.json ./

# Increase memory for Node
ENV NODE_OPTIONS="--max_old_space_size=4096"

# Install dependencies
RUN npm install

# Download plugins before build to avoid issues
RUN npm run download:plugins

# Build Theia
RUN npm run build

# Create project directory
RUN mkdir -p /home/project

EXPOSE 3000

# Start Theia using the proper start script
CMD ["npm", "start"]