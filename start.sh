#!/bin/bash

# MedSync Application Startup Script

echo "🏥 Starting MedSync Hospital Management System..."

# Start Backend
echo "📡 Starting Backend Server..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "🌐 Starting Frontend Server..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo "✅ MedSync is now running!"
echo "📡 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID