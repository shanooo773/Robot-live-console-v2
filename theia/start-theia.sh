#!/bin/bash

# Custom Theia startup script that configures external hostname
# This script is designed to be run inside the Theia container
# It configures Theia to use the external hostname instead of localhost

# Get external host and port from environment variables
EXTERNAL_HOST=${THEIA_HOST:-localhost}
EXTERNAL_PORT=${THEIA_PORT:-3000}
PUBLIC_URL=${PUBLIC_URL:-http://$EXTERNAL_HOST:$EXTERNAL_PORT}

echo "Starting Theia with external configuration:"
echo "  External Host: $EXTERNAL_HOST"
echo "  External Port: $EXTERNAL_PORT" 
echo "  Public URL: $PUBLIC_URL"

# Set environment variables that Theia might use for URL generation
export THEIA_OPEN_HANDLER_URL="$PUBLIC_URL"
export THEIA_WEBVIEW_EXTERNAL_ENDPOINT="$PUBLIC_URL"

# Set Node.js specific environment variables that might affect URL generation
export NODE_OPTIONS="--max-old-space-size=2048"

# Start Theia with the external hostname configuration
# Use the standard Theia start command but ensure it knows about external access
exec theia start \
    --plugins=local-dir:plugins \
    --hostname=0.0.0.0 \
    --port=3000 \
    --app-project-path=/home/project