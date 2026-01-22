#!/bin/bash

# Start All Services for Agent Security Gateway System

echo "🚀 Starting Agent Security Gateway System..."
echo ""

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set!"
    echo "   AI Agent features will not work."
    echo "   Set it with: export OPENAI_API_KEY='sk-...'"
    echo ""
fi

# Start Security Gateway (Port 8002)
echo "1️⃣  Starting Security Gateway on port 8002..."
cd agent_gateway
python app.py &
GATEWAY_PID=$!
cd ..

sleep 2

# Start AI Agent API (Port 8003)
echo "2️⃣  Starting AI Agent API on port 8003..."
cd ai_agent
python agent_api.py &
AGENT_PID=$!
cd ..

sleep 2

# Start Dashboard (Port 8080)
echo "3️⃣  Starting Dashboard on port 8080..."
cd client_ui
python -m http.server 8080 &
DASHBOARD_PID=$!
cd ..

sleep 2

echo ""
echo "✅ All services started!"
echo ""
echo "📍 URLs:"
echo "   Security Gateway: http://localhost:8002"
echo "   AI Agent API:     http://localhost:8003"
echo "   Dashboard:        http://localhost:8080/security-dashboard.html"
echo ""
echo "📚 API Docs:"
echo "   Gateway:          http://localhost:8002/docs"
echo "   Agent:            http://localhost:8003/docs"
echo ""
echo "🛑 To stop all services:"
echo "   kill $GATEWAY_PID $AGENT_PID $DASHBOARD_PID"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "kill $GATEWAY_PID $AGENT_PID $DASHBOARD_PID; exit" INT
wait
