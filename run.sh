#!/bin/bash

# Set working directory to project root
cd "$(dirname "$0")"

# Start FastAPI in the background and store its process ID (PID)
(cd src/orchestrator && uvicorn main:app --reload --host 0.0.0.0 --port 8000) & 
UVICORN_PID=$!

# Start the React frontend
(cd src/web && npm run dev) & 
REACT_PID=$!

# Trap SIGINT (CTRL + C) and kill background processes
cleanup() {
    echo "Stopping Uvicorn (PID: $UVICORN_PID) and React (PID: $REACT_PID)..."
    kill $UVICORN_PID
    kill $REACT_PID
    exit 0
}

# Catch CTRL + C and run cleanup function
trap cleanup SIGINT

# Wait for background processes to finish (so script doesn’t exit immediately)
wait
