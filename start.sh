#!/bin/bash

# Macro Builder - Quick Start Script

echo "🚀 Starting Macro Builder services..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Start services
echo "📦 Starting PostgreSQL, Redis, API, and Celery..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check health
echo "🔍 Checking API health..."
response=$(curl -s http://localhost:8000/health)

if echo "$response" | grep -q "healthy"; then
    echo "✅ All services are running!"
    echo ""
    echo "📋 Available endpoints:"
    echo "   API:          http://localhost:8000"
    echo "   API Docs:     http://localhost:8000/docs"
    echo "   PostgreSQL:   localhost:5432"
    echo "   Redis:        localhost:6379"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Visit http://localhost:8000/docs for interactive API documentation"
    echo "   2. Create an account via POST /api/v1/auth/register"
    echo "   3. Login to get your JWT token"
    echo "   4. Start creating workflows!"
    echo ""
    echo "🛑 To stop services: docker-compose down"
else
    echo "❌ Services failed to start. Check logs with: docker-compose logs"
    exit 1
fi
