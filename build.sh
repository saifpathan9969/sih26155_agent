#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=================================================="
echo "🚀 SIH26155 AUDITOR — RENDER DEPLOYMENT BUILD"
echo "=================================================="

# 1. Install Backend Dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r sih26155_agent/requirements.txt

# 2. Build Frontend
echo "⚛️ Building Frontend application..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Build completed successfully!"
