#!/bin/bash

# Immotop Invoice Classifier - Start Script

echo "🚀 Starting Immotop Invoice Classifier..."
echo ""

# Check if Python venv exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    source backend/venv/bin/activate
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Create .env files if they don't exist
if [ ! -f "backend/.env" ]; then
    echo "⚙️  Creating backend .env file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your ANTHROPIC_API_KEY"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "⚙️  Creating frontend .env.local file..."
    cp frontend/.env.local.example frontend/.env.local
fi

echo ""
echo "Starting services..."
echo ""

# Start backend
echo "🐍 Starting Backend (http://localhost:8000)..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Start frontend
echo "⚛️  Starting Frontend (http://localhost:3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started!"
echo ""
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
