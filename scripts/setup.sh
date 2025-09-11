#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if .env files exist
if [ ! -f "backend/.env" ] || [ ! -f "frontend/.env" ]; then
    echo "❌ Environment files not found!"
    echo ""
    echo "Please copy the example environment files first:"
    echo "  cp backend/.env.example backend/.env"
    echo "  cp frontend/.env.example frontend/.env"
    echo ""
    echo "Then configure your environment variables and run this script again."
    exit 1
fi

echo "✅ Environment files found. Continuing with setup..."

# --- Docker Compose ---
echo "Starting Docker services in the background..."
docker-compose up -d

# --- Backend Setup ---
echo "Setting up backend..."
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing backend dependencies with uv..."
cd ../backend
uv sync

# --- Frontend Setup ---
echo "Setting up frontend..."
cd ../frontend

echo "Installing frontend dependencies with pnpm..."
pnpm install

cd ..

echo "Setup complete!"
echo ""
echo "🔑 IMPORTANT: Configure your environment variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Before running GAIA, you need to configure your API keys and environment variables."
echo ""
echo "📝 Configuration files created:"
echo "   • backend/.env  - Backend configuration (API keys, database settings)"
echo "   • frontend/.env - Frontend configuration (API URLs, tokens)"
echo ""
echo "📚 For detailed setup instructions, visit:"
echo "   Environment Variables: https://docs.heygaia.io/configuration/environment-variables"
echo "   Infisical Setup:      https://docs.heygaia.io/configuration/infisical-setup"
echo ""
echo "💡 Quick start: At minimum, you'll need to configure:"
echo "   • OpenAI API key (or other AI model APIs)"
echo "   • Google OAuth credentials (if using authentication)"
echo "   • Infisical credentials (recommended for production)"
echo ""
echo "After configuring your environment variables, you can start the application!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
