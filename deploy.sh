#!/bin/bash
# ==============================================================================
# 🚀 AI PULSE - UNIFIED DEPLOYMENT SCRIPT (Unix/macOS/Linux)
# Workshop: Agentic AI 101 - Autonomous Newsletter & Research Agent Pipeline
# Operating System: macOS / Linux (Bash)
# ==============================================================================

# Colors for terminal styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Determine workspace root directory
WorkspaceRoot="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$WorkspaceRoot"

clear

# --- BEAUTIFUL ASCII BANNER ---
echo -e "${CYAN}================================================================================${NC}"
echo -e "${CYAN}      ___   ___    ____  __  __ _     ____  _____   ____  ____  ____  _${NC}"
echo -e "${CYAN}     / _ \ / _ \  |  _ \|  ||  | |   / ___|| ____| |  _ \|  _ \/ ___|| |${NC}"
echo -e "${CYAN}    | |_| | |_| | | |_) |  ||  | |   \___ \|  _|   | |_) | |_) \___ \| |${NC}"
echo -e "${CYAN}    |  _  |  _  | |  __/|  ||  | |___ ___  ) |___  |  __/|  _ < ___) |_|${NC}"
echo -e "${CYAN}    |_| |_|_| |_| |_|   \______/_____|____/|_____| |_|   |_| \_\____/(_)${NC}"
echo -e "${CYAN}================================================================================${NC}"
echo -e "         ${YELLOW}Autonomous Newsletter & Research Agent Pipeline Deployment${NC}"
echo -e "${CYAN}================================================================================${NC}"

# --- SYSTEM & ENVIRONMENT VALIDATION ---
echo -e "${GRAY}[*] Validating workspace structure...${NC}"
PipelineDir="$WorkspaceRoot/agent-pipeline"
if [ ! -d "$PipelineDir" ]; then
    echo -e "${RED}[!] ERROR: 'agent-pipeline' directory not found in: $WorkspaceRoot${NC}"
    echo -e "    Please run this script from the workspace root directory."
    exit 1
fi

RootEnvFile="$WorkspaceRoot/.env"
BackendEnvFile="$PipelineDir/python-backend/.env"
BackendEnvExample="$PipelineDir/python-backend/.env.example"

# Auto-resolve environment files
if [ ! -f "$BackendEnvFile" ] && [ -f "$RootEnvFile" ]; then
    echo -e "${GREEN}[+] Copying .env from workspace root to backend...${NC}"
    cp "$RootEnvFile" "$BackendEnvFile"
elif [ ! -f "$RootEnvFile" ] && [ -f "$BackendEnvFile" ]; then
    echo -e "${GREEN}[+] Copying .env from backend to workspace root...${NC}"
    cp "$BackendEnvFile" "$RootEnvFile"
elif [ ! -f "$RootEnvFile" ] && [ ! -f "$BackendEnvFile" ]; then
    echo -e "${YELLOW}[!] No .env file found. Initializing from .env.example...${NC}"
    if [ -f "$BackendEnvExample" ]; then
        cp "$BackendEnvExample" "$RootEnvFile"
        cp "$BackendEnvExample" "$BackendEnvFile"
        echo -e "${GREEN}[+] Initialized .env files in root and backend.${NC}"
    else
        echo -e "${RED}[!] ERROR: Could not find .env.example to initialize environment!${NC}"
        exit 1
    fi
fi

# Inject REPO_PATH dynamically to avoid hardcoded paths
echo -e "${GRAY}[*] Configuring REPO_PATH dynamically in environment files...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS sed needs empty string parameter for in-place edit
    sed -i '' "s|^REPO_PATH=.*|REPO_PATH=$WorkspaceRoot|" "$RootEnvFile"
    sed -i '' "s|^REPO_PATH=.*|REPO_PATH=$WorkspaceRoot|" "$BackendEnvFile"
else
    # Linux sed
    sed -i "s|^REPO_PATH=.*|REPO_PATH=$WorkspaceRoot|" "$RootEnvFile"
    sed -i "s|^REPO_PATH=.*|REPO_PATH=$WorkspaceRoot|" "$BackendEnvFile"
fi
echo -e "${GREEN}[+] Set REPO_PATH to: $WorkspaceRoot${NC}"

# Verify Gemini API Key configuration
if grep -q "gemini_api_key_from_ai_studio" "$RootEnvFile"; then
    echo -e "${YELLOW}--------------------------------------------------------------------------------${NC}"
    echo -e "${YELLOW}[⚠️ WARNING] GEMINI_API_KEY is not configured in your .env file!${NC}"
    echo -e "  Please open '.env' and set your real Gemini API key before running the pipeline."
    echo -e "  You can get a free API key at: https://aistudio.google.com/"
    echo -e "${YELLOW}--------------------------------------------------------------------------------${NC}"
fi

# --- FUNCTIONS ---

ensure_local_gemma() {
    echo ""
    echo -e "${GRAY}--------------------------------------------------------------------------------${NC}"
    echo -e "🦙 ${CYAN}LOCAL GEMMA (OLLAMA) VERIFICATION${NC}"
    echo -e "${GRAY}--------------------------------------------------------------------------------${NC}"

    # 1. Check if ollama command is available
    if ! command -v ollama &> /dev/null; then
        echo -e "${YELLOW}[!] Ollama is not installed or not in PATH.${NC}"
        echo -e "    If you plan to use local models, please download Ollama from: https://ollama.com/"
        return
    fi

    # 2. Check if Ollama service is listening
    if ! lsof -i :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
        read -p "[?] Ollama server is NOT running. Would you like to start it now? (y/n): " response
        if [[ "$response" =~ ^[yY]$ ]]; then
            echo -e "${GRAY}[*] Starting Ollama server in background...${NC}"
            ollama serve > /dev/null 2>&1 &
            # Wait a few seconds for it to start
            for i in {1..5}; do
                sleep 1
                if lsof -i :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
                    break
                fi
            done
        fi
    fi

    # Re-check connection
    if lsof -i :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}[+] Ollama server is running.${NC}"
        
        # 3. Check for gemma/gemma3 model
        models=$(ollama list)
        if [[ ! "$models" =~ "gemma" ]]; then
            read -p "[?] Gemma model is not found in Ollama. Would you like to pull 'gemma' (5GB) now? (y/n): " response
            if [[ "$response" =~ ^[yY]$ ]]; then
                echo -e "${YELLOW}[*] Pulling gemma model (this may take a few minutes)...${NC}"
                ollama pull gemma
            fi
        else
            echo -e "${GREEN}[+] Local Gemma model is installed.${NC}"
        fi
    else
        echo -e "${YELLOW}[!] Ollama server could not be started or is not running.${NC}"
    fi
    echo -e "${GRAY}--------------------------------------------------------------------------------${NC}"
}

show_ports() {
    echo -e "${GRAY}[*] Checking port status for stack services...${NC}"
    echo -e "${CYAN}Port | Service                | Status${NC}"
    echo -e "${CYAN}-----|------------------------|-----------------${NC}"
    
    ports=(8000 5173 3002)
    names=("FastAPI Backend" "Vite React Frontend" "WhatsApp Bridge")
    
    for i in "${!ports[@]}"; do
        port="${ports[$i]}"
        name="${names[$i]}"
        
        # Check if port is in use
        if lsof -i :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            pid=$(lsof -i :"$port" -sTCP:LISTEN -t)
            printf "${YELLOW}%-5s | %-22s | Active (Listening, PID: %s)${NC}\n" "$port" "$name" "$pid"
        else
            printf "${GREEN}%-5s | %-22s | Free${NC}\n" "$port" "$name"
        fi
    done
    echo ""
}

stop_all_services() {
    echo -e "${YELLOW}[*] Stopping all Docker containers associated with the stack...${NC}"
    docker-compose down -v >/dev/null 2>&1
    
    echo -e "${YELLOW}[*] Terminating any local instances of Backend (8000), Frontend (5173), or WhatsApp Bridge (3002)...${NC}"
    ports=(8000 5173 3002)
    for port in "${ports[@]}"; do
        if lsof -i :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            pid=$(lsof -i :"$port" -sTCP:LISTEN -t)
            echo -e "${RED}[-] Killing process $pid listening on port $port...${NC}"
            kill -9 "$pid" >/dev/null 2>&1
        fi
    done
    echo -e "${GREEN}[+] Services stopped.${NC}"
}

deploy_docker() {
    echo -e "${CYAN}[*] Deploying using Docker Compose...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[!] ERROR: Docker is not installed or not in PATH!${NC}"
        echo -e "    Please install Docker Desktop or run in Local Native mode."
        return
    fi

    stop_all_services

    echo -e "${GRAY}[*] Starting containers via Docker Compose...${NC}"
    docker-compose up -d --build

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}================================================================================${NC}"
        echo -e "${GREEN}🎉 DOCKER CONTAINERS SUCCESSFULLY STARTED${NC}"
        echo -e "${GREEN}================================================================================${NC}"
        echo -e "  🌐 React Dashboard:  http://localhost:5173"
        echo -e "  🔌 FastAPI Backend:  http://localhost:8000"
        echo -e "  📲 WhatsApp Bridge:  http://localhost:3002"
        echo -e "--------------------------------------------------------------------------------"
        echo -e "${YELLOW}👉 IMPORTANT: First-time WhatsApp bridge setup requires scanning a QR code.${NC}"
        echo -e "   Run this command in a new terminal window to scan the QR code:"
        echo -e "   ${CYAN}docker attach whatsapp_bridge${NC}"
        echo -e "   Once scanned, press ${CYAN}Ctrl+P, Ctrl+Q${NC} to safely detach from the container."
        echo -e "${GREEN}================================================================================${NC}"

        read -p "Would you like to verify/start local Gemma via Ollama? (y/n): " ollama_check
        if [[ "$ollama_check" =~ ^[yY]$ ]]; then
            ensure_local_gemma
        fi
    else
        echo -e "${RED}[!] Docker deployment failed.${NC}"
    fi
}

deploy_local() {
    echo -e "${CYAN}[*] Deploying in Local Native Process mode...${NC}"

    if ! command -v npm &> /dev/null; then
        echo -e "${RED}[!] ERROR: Node.js/NPM is not installed! Required for Frontend and WhatsApp Bridge.${NC}"
        return
    fi

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[!] ERROR: Python3 is not installed! Required for Backend.${NC}"
        return
    fi

    stop_all_services
    echo ""

    # 1. WhatsApp Bridge Setup
    echo -e "${GRAY}[*] Setting up WhatsApp Bridge...${NC}"
    BridgeDir="$PipelineDir/whatsapp-bridge-js"
    if [ ! -d "$BridgeDir/node_modules" ]; then
        echo -e "${YELLOW}[-] Installing WhatsApp Bridge dependencies...${NC}"
        cd "$BridgeDir" && npm install && cd "$WorkspaceRoot"
    fi

    # 2. Python Backend Setup
    echo -e "${GRAY}[*] Setting up Python Backend...${NC}"
    BackendDir="$PipelineDir/python-backend"
    VenvDir="$BackendDir/venv"
    if [ ! -d "$VenvDir" ]; then
        echo -e "${YELLOW}[-] Creating Python virtual environment...${NC}"
        python3 -m venv "$VenvDir"
    fi
    echo -e "${YELLOW}[-] Installing backend dependencies...${NC}"
    "$VenvDir/bin/pip" install -r "$BackendDir/requirements.txt"

    # 3. Frontend Setup
    echo -e "${GRAY}[*] Setting up React Frontend...${NC}"
    FrontendDir="$PipelineDir/frontend"
    if [ ! -d "$FrontendDir/node_modules" ]; then
        echo -e "${YELLOW}[-] Installing React Frontend dependencies...${NC}"
        cd "$FrontendDir" && npm install && cd "$WorkspaceRoot"
    fi

    # 4. Spawning Processes
    echo -e "${GREEN}[*] Launching services in background...${NC}"
    
    # Create logs directory
    mkdir -p "$WorkspaceRoot/logs"

    # Launch WhatsApp Bridge
    echo -e "[+] Starting WhatsApp Bridge..."
    cd "$BridgeDir"
    npm start > "$WorkspaceRoot/logs/whatsapp.log" 2>&1 &
    cd "$WorkspaceRoot"
    sleep 2

    # Launch FastAPI Backend
    echo -e "[+] Starting FastAPI Backend..."
    cd "$BackendDir"
    "$VenvDir/bin/python" -m uvicorn main:app --port 8000 > "$WorkspaceRoot/logs/backend.log" 2>&1 &
    cd "$WorkspaceRoot"
    sleep 2

    # Launch React Frontend
    echo -e "[+] Starting React Frontend Dashboard..."
    cd "$FrontendDir"
    npm run dev > "$WorkspaceRoot/logs/frontend.log" 2>&1 &
    cd "$WorkspaceRoot"

    echo ""
    echo -e "${GREEN}================================================================================${NC}"
    echo -e "${GREEN}🎉 LOCAL PROCESS STACK DEPLOYED (Running in Background)${NC}"
    echo -e "${GREEN}================================================================================${NC}"
    echo -e "  🌐 React Dashboard:  http://localhost:5173"
    echo -e "  🔌 FastAPI Backend:  http://localhost:8000"
    echo -e "  📲 WhatsApp Bridge:  http://localhost:3002"
    echo -e "--------------------------------------------------------------------------------"
    echo -e "📝 Logs are saved to: ${CYAN}$WorkspaceRoot/logs/${NC}"
    echo -e "   - WhatsApp Bridge Log: tail -f logs/whatsapp.log"
    echo -e "   - Python Backend Log:  tail -f logs/backend.log"
    echo -e "   - React Frontend Log:  tail -f logs/frontend.log"
    echo -e ""
    echo -e "${YELLOW}👉 SCAN WHATSAPP QR CODE:${NC}"
    echo -e "   To authenticate WhatsApp, run: ${CYAN}cat logs/whatsapp.log${NC} or tail it."
    echo -e "   The QR code will print to the log file or terminal shortly."
    echo -e ""
    echo -e "🛑 To stop everything, select Option 3 in this menu."
    echo -e "${GREEN}================================================================================${NC}"

    read -p "Would you like to verify/start local Gemma via Ollama? (y/n): " ollama_check
    if [[ "$ollama_check" =~ ^[yY]$ ]]; then
        ensure_local_gemma
    fi
}

# --- INTERACTIVE MENU LOOP ---
while true; do
    echo -e "${GRAY}--------------------------------------------------------------------------------${NC}"
    echo -e "  [1] Deploy Stack via Docker Compose (Recommended)"
    echo -e "  [2] Deploy Stack via Local Native Processes (Background)"
    echo -e "  [3] Stop All Running Services (Docker + Local Ports)"
    echo -e "  [4] Check Port & Service Status"
    echo -e "  [5] Exit"
    echo -e "${GRAY}--------------------------------------------------------------------------------${NC}"
    read -p "Choose an option [1-5]: " Selection

    case $Selection in
        1) deploy_docker ;;
        2) deploy_local ;;
        3) stop_all_services ;;
        4) show_ports ;;
        5) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}[!] Invalid option, please enter 1 to 5.${NC}" ;;
    esac
    echo ""
done
