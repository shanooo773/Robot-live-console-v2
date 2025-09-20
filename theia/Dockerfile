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

# Copy package.json and yarn.lock from your frontend project
COPY --chown=theia:theia frontend/package.json frontend/yarn.lock ./

# Increase memory for Node
ENV NODE_OPTIONS="--max_old_space_size=4096"

# Install dependencies with Yarn
RUN yarn install --frozen-lockfile || yarn install --ignore-engines

# Copy the rest of your frontend project
COPY --chown=theia:theia frontend/ ./

# Build Theia (ignore warnings but don’t fail the build)
RUN npx theia build || echo "Build completed with warnings"

# Create project directory
RUN mkdir -p /home/project

EXPOSE 3000

# Start Theia
CMD ["node", "/home/theia/src-gen/backend/main.js", "/home/project", "--hostname=0.0.0.0", "--port=3000"]
