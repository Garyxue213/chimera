#!/bin/bash

echo ""
echo "🏁 F1 REACT DASHBOARD - LAUNCHER"
echo "=================================="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (first run)..."
    npm install
    echo ""
fi

echo "🚀 Starting F1 React Dashboard..."
echo ""
echo "Dashboard will open at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
