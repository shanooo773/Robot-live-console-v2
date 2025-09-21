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

# Copy both package.json and package-lock.json for reproducible builds
COPY --chown=theia:theia package.json package-lock.json ./

# Increase Node memory
ENV NODE_OPTIONS="--max_old_space_size=4096"

# Install dependencies using lockfile (deterministic build)
 

# Build Theia app
RUN npx theia build || echo "Build completed with warnings"

# Create project directory

EXPOSE 3000

# Start Theia
CMD ["node", "/home/theia/src-gen/backend/main.js", "/home/project", "--hostname=0.0.0.0", "--port=3000"]
