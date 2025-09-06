#!/bin/bash
set -e

# Detect python
PYTHON=$(command -v python3 || command -v python)

# --- Environment Setup ---
echo "🔧 Setting up environment variables..."

[ ! -f "backend/.env" ] && cp backend/.env.example backend/.env && echo "Created backend/.env" || echo "backend/.env already exists, skipping..."
[ ! -f "frontend/.env" ] && cp frontend/.env.example frontend/.env && echo "Created frontend/.env" || echo "frontend/.env already exists, skipping..."

# --- Docker ---
echo "🐳 Starting Docker services..."
if command -v docker compose &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

# --- Backend Setup ---
echo "⚙️ Setting up backend..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON -m venv .venv
fi

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
else
    echo "Could not find virtual environment activation script."
    exit 1
fi

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    $PYTHON -m pip install --upgrade pip
    $PYTHON -m pip install uv
fi

echo "Installing backend dependencies..."
uv sync
cd ..

# --- Frontend Setup ---
echo "⚙️ Setting up frontend..."
cd frontend
pnpm install
cd ..

# --- Done ---
echo ""
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
