FROM node:18-slim

# Install necessary build tools and libraries for native modules
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    build-essential \
    libx11-dev \
    libxkbfile-dev \
    libsecret-1-dev \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Enable Yarn v1 via Corepack (no npm -g permission issues)
RUN corepack enable && corepack prepare yarn@1.22.22 --activate

# Create theia user
RUN groupadd -g 1001 theia && \
    useradd -u 1001 -g theia -s /bin/bash -m theia

WORKDIR /home/theia
USER theia

# Copy package.json and yarn.lock
COPY --chown=theia:theia package.json yarn.lock ./

# Install dependencies with more memory + ignore engine strictness
ENV NODE_OPTIONS="--max_old_space_size=4096"
RUN yarn install --ignore-engines

# Build Theia
RUN yarn theia build

# Create project directory
RUN mkdir -p /home/project

EXPOSE 3000

CMD ["yarn", "start", "/home/project", "--hostname=0.0.0.0"]
