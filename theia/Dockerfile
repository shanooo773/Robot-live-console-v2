FROM node:18-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create theia user (non-root)
RUN groupadd -g 1001 theia && \
    useradd -u 1001 -g theia -s /bin/bash -m theia

WORKDIR /home/theia
USER theia

# Copy package.json
COPY --chown=theia:theia package.json ./

# Use Yarn instead of npm (Theia recommends yarn)
RUN npm install -g yarn

# Install dependencies with yarn (ignore engines to avoid strict checks)
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN yarn install --ignore-engines

# Build Theia app (clean + build + plugins)
RUN yarn run clean && yarn run build && yarn run download:plugins

# Workspace directory
RUN mkdir -p /home/project

EXPOSE 3000

# Start Theia
CMD ["yarn", "start", "--hostname=0.0.0.0"]
