#!/bin/bash

# Expense Organizer Quick Start Script

echo "🚀 Starting Expense Organizer..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "📦 Building Docker containers..."
docker-compose up --build -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if docker ps | grep -q "expense-backend" && docker ps | grep -q "expense-frontend"; then
    echo ""
    echo "✅ Application is running!"
    echo ""
    echo "📱 Web Frontend: http://localhost:13000"
    echo "🔧 API Proxy: http://localhost:13000/api"
    echo "📚 API Docs: http://localhost:13000/api/docs"
    echo "🧠 AI Assistant: http://localhost:18001"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
else
    echo ""
    echo "❌ Failed to start services. Check logs with: docker-compose logs"
    exit 1
fi
