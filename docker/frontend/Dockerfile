# Frontend Dockerfile for Robot Live Console
# This is an additive file - does not modify existing editor/backend Docker assets
# Runs the React dev server in Docker with hot-reload support

FROM node:18

WORKDIR /app

# Copy package files from frontend directory
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies with legacy peer deps flag for compatibility
RUN npm ci --legacy-peer-deps

# Expose development server port
EXPOSE 3000

# Default command runs the dev server
# Note: docker-compose will mount frontend source to /app/frontend for hot-reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
