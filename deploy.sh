#!/bin/bash

echo "🚀 Deploying clipsmith..."

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

echo "📦 Building and starting containers..."
docker-compose up --build -d

echo "✅ Deployment complete!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
