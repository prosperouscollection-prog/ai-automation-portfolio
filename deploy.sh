#!/bin/bash
# Claude API Phone Access - Quick Deployment
# Run this to deploy everything in one command

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Claude API Phone Access - Quick Deployment       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR/claude-api-phone-access"
BACKEND_DIR="$PROJECT_DIR/backend"

echo -e "\n${BLUE}📁 Project directory:${NC} $PROJECT_DIR"

# Check if project exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Error: claude-api-phone-access folder not found!${NC}"
    echo -e "   Expected at: $PROJECT_DIR"
    exit 1
fi

# Check Python
echo -e "\n${BLUE}Step 1: Checking Python${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    echo "Install from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"

# Setup venv
echo -e "\n${BLUE}Step 2: Setting up virtual environment${NC}"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⏳ Creating venv...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}ℹ️  Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo -e "\n${BLUE}Step 3: Installing dependencies${NC}"
echo -e "${YELLOW}⏳ Installing packages...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Get API key
echo -e "\n${BLUE}Step 4: Configure Claude API Key${NC}"
echo -e "\nYou need a Claude API key to continue."
echo "Get one at: ${BLUE}https://console.anthropic.com/account/keys${NC}"
echo ""

if [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}ℹ️  .env file already exists${NC}"
    read -p "Use existing key? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        chmod 600 "$PROJECT_DIR/.env"
        echo -e "${GREEN}✅ Using existing configuration${NC}"
    else
        # Remove existing
        rm "$PROJECT_DIR/.env"
    fi
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    read -sp "Enter your Claude API key: " API_KEY
    echo ""
    
    if [ -z "$API_KEY" ]; then
        echo -e "${RED}❌ API key cannot be empty${NC}"
        exit 1
    fi
    
    # Create .env file
    cat > "$PROJECT_DIR/.env" << EOF
# Claude API Configuration
CLAUDE_API_KEY=$API_KEY

# Server Configuration
PORT=5000
DEBUG=False

# Optional: For remote access via ngrok
NGROK_AUTH_TOKEN=your_ngrok_token_here
EOF
    
    chmod 600 "$PROJECT_DIR/.env"
    echo -e "${GREEN}✅ API key saved to .env${NC}"
fi

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Setup Complete! 🎉                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"

echo -e "\n${BLUE}Next steps:${NC}"
echo -e "  1. Keep this terminal open"
echo -e "  2. Run: python app.py"
echo -e "  3. Find your Mac IP: ifconfig | grep 'inet '"
echo -e "  4. On phone, visit: http://YOUR_MAC_IP:5000"

read -p "Start the server now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}🚀 Starting server...${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    python app.py
else
    echo -e "\n${YELLOW}To start later:${NC}"
    echo "  cd $BACKEND_DIR"
    echo "  source venv/bin/activate"
    echo "  python app.py"
fi
