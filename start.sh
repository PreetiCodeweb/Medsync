#!/bin/bash

# MedSync Professional Application Startup Script

echo "🏥 Starting MedSync Professional Hospital Management System..."
echo "🧠 RAG System: Enabled"
echo "📊 Monitoring: Enabled"
echo "🚀 Version: 2.0.0 (Professional)"
echo ""

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Start Backend
echo "📡 Starting Backend Server with RAG System..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 8

# Check backend health
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    RAG_STATUS=$(echo $HEALTH_RESPONSE | grep -o '"rag_enabled":[^,]*' | cut -d':' -f2)
    echo "🧠 RAG Status: $RAG_STATUS"
else
    echo "⚠️ Backend health check failed"
fi

# Start Frontend
echo "🌐 Starting Frontend Server..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ MedSync Professional is now running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Backend API: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo "📊 Metrics: http://localhost:8000/metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔐 Default Credentials:"
echo "  User: user@medsync.com / user123"
echo "  Hospital: hospital@medsync.com / hospital123"
echo "  Admin: admin@medsync.com / admin123"
echo ""
echo "🧠 RAG System Features:"
echo "  • Medical knowledge base with 8 specialties"
echo "  • Semantic search with vector embeddings"
echo "  • Confidence scoring for analysis"
echo "  • Source attribution for transparency"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID