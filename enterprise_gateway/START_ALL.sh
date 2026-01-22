#!/bin/bash

# Start All Services for Enterprise Agent Security Gateway

echo "🚀 Starting Enterprise Agent Security Gateway System..."
echo ""

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set!"
    echo "   OpenAI agents will not work. Ollama will still function."
    echo "   Set it with: export OPENAI_API_KEY='sk-...'"
    echo ""
fi

# Start Security Gateway (Port 8004)
echo "1️⃣  Starting Security Gateway on port 8004..."
cd /Users/tarang/CascadeProjects/windsurf-project/owasp-api10-security-lab/enterprise_gateway
python main.py &
GATEWAY_PID=$!

sleep 3

# Start AI Agent API (Port 8005)
echo "2️⃣  Starting AI Agent API on port 8005..."
cd agents
python agent_api.py &
AGENT_PID=$!

sleep 2

# Start Dashboard (Port 8006)
echo "3️⃣  Starting Dashboard on port 8006..."
cd ../dashboard
python -m http.server 8006 &
DASHBOARD_PID=$!

sleep 2

echo ""
echo "✅ All services started!"
echo ""
echo "📍 URLs:"
echo "   Security Gateway:  http://localhost:8004"
echo "   AI Agent API:      http://localhost:8005"
echo "   Dashboard:         http://localhost:8006/enterprise_dashboard.html"
echo ""
echo "📚 API Docs:"
echo "   Gateway:           http://localhost:8004/docs"
echo "   Agent API:         http://localhost:8005/docs"
echo ""
echo "🎭 Demo Scenarios:"
echo "   Open dashboard and click 'Demo Scenarios'"
echo ""
echo "🛑 To stop all services:"
echo "   kill $GATEWAY_PID $AGENT_PID $DASHBOARD_PID"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "kill $GATEWAY_PID $AGENT_PID $DASHBOARD_PID 2>/dev/null; echo '\n\n🛑 All services stopped'; exit" INT
wait
