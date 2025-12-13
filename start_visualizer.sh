#!/bin/bash

# JUMP Discovery Visualizer Launcher
echo "🧬 Starting JUMP Discovery Research Explorer..."
echo "=================================="

# Kill any existing server on port 9876
lsof -ti:9876 | xargs kill -9 2>/dev/null || true

# Start the server
python3 server.py &
SERVER_PID=$!

# Wait for server to start
sleep 2

echo "✅ Server started successfully!"
echo ""
echo "🌐 Access the visualizer:"
echo "   Main Interface: http://localhost:9876/jump_discovery_visualizer_v2.html"
echo "   Legacy Interface: http://localhost:9876/jump_discovery_visualizer.html"
echo ""
echo "📊 Features:"
echo "   • Interactive network visualization"
echo "   • Quality scoring and filtering"
echo "   • Comprehensive evidence display"
echo "   • Real-time report parsing"
echo ""
echo "🔧 Controls:"
echo "   • Click nodes for detailed analysis"
echo "   • Use quality filters in header"
echo "   • Hover for quick metrics"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Keep the server running and handle cleanup
trap "echo 'Stopping server...'; kill $SERVER_PID; exit" INT

# Open browser (optional - uncomment if desired)
# open "http://localhost:9876/jump_discovery_visualizer_v2.html"

wait $SERVER_PID