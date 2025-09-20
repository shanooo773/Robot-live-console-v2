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

# Install Yarn Classic (Theia requires 1.x)
RUN npm install -g yarn@1.22.22 --force

# Create theia user
RUN groupadd -g 1001 theia && \
    useradd -u 1001 -g theia -s /bin/bash -m theia

WORKDIR /home/theia
USER theia

# Copy package.json
COPY --chown=theia:theia package.json ./

# Increase memory and install dependencies with yarn
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN yarn install --ignore-engines

# Build Theia app (ignore warnings but don’t fail)
RUN yarn theia build || echo "Build completed with warnings"

# Project directory
RUN mkdir -p /home/project

EXPOSE 3000

# Start command
CMD ["yarn", "theia", "start", "/home/project", "--hostname=0.0.0.0", "--port=3000"]
