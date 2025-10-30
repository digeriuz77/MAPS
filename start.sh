#!/bin/sh
# Startup script for Railway deployment
# Ensures PORT environment variable is properly handled

# Set default port if PORT is not set
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"

# Start uvicorn with the resolved port
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT