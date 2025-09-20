FROM node:18-slim

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create theia user
RUN groupadd -g 1001 theia && \
    useradd -u 1001 -g theia -s /bin/bash -m theia

WORKDIR /home/theia
USER theia

# Copy npm package manifests
COPY --chown=theia:theia package.json package-lock.json ./

# Install dependencies with npm (allow larger memory usage)
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN npm install

# Build Theia app
RUN npm run clean && npm run build && npm run download:plugins

# Create project directory
RUN mkdir -p /home/project

EXPOSE 3000

# Start command with plugin support
CMD ["npm", "start"]
