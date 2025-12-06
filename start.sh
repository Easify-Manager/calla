#!/bin/bash

# Calla Platform Startup Script

set -e

echo "🚀 Starting Calla Platform..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/"
    echo ""
    read -p "Press Enter after you've updated .env with your API key..."
fi

# Check if GEMINI_API_KEY is set
source .env
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY is not set in .env"
    echo "   Get your API key from: https://aistudio.google.com/"
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Start services
echo "📦 Starting Docker containers..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Calla Platform is running!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
echo ""
