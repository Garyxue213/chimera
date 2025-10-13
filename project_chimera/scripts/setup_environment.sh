#!/bin/bash

# Project Chimera Environment Setup Script
# This script sets up the containerized simulation environment

set -e

echo "🚀 Setting up Project Chimera simulation environment..."

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p docker/git-server
mkdir -p docker/ticket-manager  
mkdir -p docker/chat-service
mkdir -p data/raw
mkdir -p data/processed
mkdir -p logs
mkdir -p results

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Build and start the services
echo "🐳 Building Docker containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose build
    echo "🚀 Starting services..."
    docker-compose up -d
else
    docker compose build
    echo "🚀 Starting services..."
    docker compose up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Git server
if curl -f http://localhost:2222 &> /dev/null; then
    echo "✅ Git server is running"
else
    echo "⚠️  Git server may not be ready yet"
fi

# Check ticket manager
if curl -f http://localhost:8080/health &> /dev/null; then
    echo "✅ Ticket manager is running"
else
    echo "⚠️  Ticket manager may not be ready yet"
fi

# Check chat service
if curl -f http://localhost:3000/health &> /dev/null; then
    echo "✅ Chat service is running"
else
    echo "⚠️  Chat service may not be ready yet"
fi

# Check database
if nc -z localhost 5432 &> /dev/null; then
    echo "✅ Database is running"
else
    echo "⚠️  Database may not be ready yet"
fi

# Check Redis
if nc -z localhost 6379 &> /dev/null; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis may not be ready yet"
fi

echo ""
echo "🎉 Project Chimera environment setup complete!"
echo ""
echo "📊 Service endpoints:"
echo "   - Git Server: ssh://localhost:2222"
echo "   - Ticket Manager: http://localhost:8080"
echo "   - Chat Service: http://localhost:3000"
echo "   - Database: postgresql://developer:dev123@localhost:5432/chimera_project"
echo "   - Redis: redis://localhost:6379"
echo ""
echo "🛠️  To stop the environment: docker-compose down"
echo "🔄 To restart: docker-compose restart"
echo "📋 To view logs: docker-compose logs -f [service-name]"
