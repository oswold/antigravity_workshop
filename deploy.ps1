# ==============================================================================
# 🚀 AI PULSE - UNIFIED DEPLOYMENT SCRIPT
# Workshop: Agentic AI 101 - Autonomous Newsletter & Research Agent Pipeline
# Operating System: Windows (PowerShell)
# ==============================================================================

# Ensure execution in the script's directory
$WorkspaceRoot = $PSScriptRoot
if ([string]::IsNullOrEmpty($WorkspaceRoot)) {
    $WorkspaceRoot = Get-Location
}
Set-Location $WorkspaceRoot

Clear-Host

# --- BEAUTIFUL ASCII BANNER ---
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "      ___   ___    ____  __  __ _     ____  _____   ____  ____  ____  _" -ForegroundColor Cyan
Write-Host "     / _ \ / _ \  |  _ \|  ||  | |   / ___|| ____| |  _ \|  _ \/ ___|| |" -ForegroundColor Cyan
Write-Host "    | |_| | |_| | | |_) |  ||  | |   \___ \|  _|   | |_) | |_) \___ \| |" -ForegroundColor Cyan
Write-Host "    |  _  |  _  | |  __/|  ||  | |___ ___  ) |___  |  __/|  _ < ___) |_|" -ForegroundColor Cyan
Write-Host "    |_| |_|_| |_| |_|   \______/_____|____/|_____| |_|   |_| \_\____/(_)" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "         Autonomous Newsletter & Research Agent Pipeline Deployment" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

# --- SYSTEM & ENVIRONMENT VALIDATION ---
Write-Host "[*] Validating workspace structure..." -ForegroundColor Gray
$PipelineDir = Join-Path $WorkspaceRoot "agent-pipeline"
if (-not (Test-Path $PipelineDir)) {
    Write-Host "[!] ERROR: 'agent-pipeline' directory not found in: $WorkspaceRoot" -ForegroundColor Red
    Write-Host "    Please ensure you run this script from the workspace root directory." -ForegroundColor Red
    Exit
}

# Env file location resolution
$RootEnvFile = Join-Path $WorkspaceRoot ".env"
$BackendEnvFile = Join-Path $PipelineDir "python-backend\.env"
$BackendEnvExample = Join-Path $PipelineDir "python-backend\.env.example"

# Auto-resolve environment files
if (-not (Test-Path $BackendEnvFile) -and (Test-Path $RootEnvFile)) {
    Write-Host "[+] Copying .env from workspace root to backend..." -ForegroundColor Green
    Copy-Item $RootEnvFile $BackendEnvFile -Force
}
elseif (-not (Test-Path $RootEnvFile) -and (Test-Path $BackendEnvFile)) {
    Write-Host "[+] Copying .env from backend to workspace root..." -ForegroundColor Green
    Copy-Item $BackendEnvFile $RootEnvFile -Force
}
elseif (-not (Test-Path $RootEnvFile) -and -not (Test-Path $BackendEnvFile)) {
    Write-Host "[!] No .env file found. Initializing from .env.example..." -ForegroundColor Yellow
    if (Test-Path $BackendEnvExample) {
        Copy-Item $BackendEnvExample $RootEnvFile -Force
        Copy-Item $BackendEnvExample $BackendEnvFile -Force
        Write-Host "[+] Initialized .env files in root and backend." -ForegroundColor Green
    } else {
        Write-Host "[!] ERROR: Could not find .env.example to initialize environment!" -ForegroundColor Red
        Exit
    }
}

# Inject REPO_PATH dynamically to avoid hardcoded paths!
Write-Host "[*] Configuring REPO_PATH dynamically in environment files..." -ForegroundColor Gray
$EscapedWorkspaceRoot = $WorkspaceRoot -replace '\\', '\\' # Escape for windows path formats if needed
$EnvContents = Get-Content $RootEnvFile
$NewEnvContents = @()
$PathUpdated = $false

foreach ($Line in $EnvContents) {
    if ($Line -like "REPO_PATH=*") {
        $NewEnvContents += "REPO_PATH=$WorkspaceRoot"
        $PathUpdated = $true
    } else {
        $NewEnvContents += $Line
    }
}
if (-not $PathUpdated) {
    $NewEnvContents += "REPO_PATH=$WorkspaceRoot"
}
$NewEnvContents | Set-Content $RootEnvFile -Force
$NewEnvContents | Set-Content $BackendEnvFile -Force
Write-Host "[+] Set REPO_PATH to: $WorkspaceRoot" -ForegroundColor Green

# Verify Gemini API Key configuration
$ApiKeyCheck = Get-Content $RootEnvFile | Select-String "GEMINI_API_KEY"
if ($ApiKeyCheck -match "gemini_api_key_from_ai_studio" -or [string]::IsNullOrEmpty($ApiKeyCheck)) {
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "[⚠️ WARNING] GEMINI_API_KEY is not configured in your .env file!" -ForegroundColor Yellow
    Write-Host "  Please open '.env' and set your real Gemini API key before running the pipeline." -ForegroundColor Yellow
    Write-Host "  You can get a free API key at: https://aistudio.google.com/" -ForegroundColor Yellow
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Yellow
}

# --- FUNCTIONS ---

function Show-Ports {
    Write-Host "[*] Checking port status for stack services..." -ForegroundColor Gray
    $Ports = @{ "8000" = "FastAPI Backend"; "5173" = "Vite React Frontend"; "3002" = "WhatsApp Bridge" }
    $ActiveConnections = Get-NetTCPConnection -ErrorAction SilentlyContinue

    Write-Host "Port`| Service`t`t`t`| Status`t`t`| PID" -ForegroundColor Cyan
    Write-Host "----|-----------------------|------------------|-----" -ForegroundColor Cyan
    foreach ($Port in $Ports.Keys) {
        $Conn = $ActiveConnections | Where-Object { $_.LocalPort -eq $Port } | Select-Object -First 1
        if ($Conn) {
            Write-Host "$Port`| $($Ports[$Port].PadRight(21)) `| Active (Listening)`| $($Conn.OwningProcess)" -ForegroundColor Yellow
        } else {
            Write-Host "$Port`| $($Ports[$Port].PadRight(21)) `| Free             `| -" -ForegroundColor Green
        }
    }
    Write-Host ""
}

function Stop-AllServices {
    Write-Host "[*] Stopping all Docker containers associated with the stack..." -ForegroundColor Yellow
    docker-compose down -v 2>$null
    
    Write-Host "[*] Terminating any local instances of Backend (8000), Frontend (5173), or WhatsApp Bridge (3002)..." -ForegroundColor Yellow
    $Ports = @(8000, 5173, 3002)
    $ActiveConnections = Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $Ports -contains $_.LocalPort }
    
    if ($ActiveConnections) {
        foreach ($Conn in $ActiveConnections) {
            $PID = $Conn.OwningProcess
            $Proc = Get-Process -Id $PID -ErrorAction SilentlyContinue
            if ($Proc) {
                Write-Host "[-] Killing process '$($Proc.Name)' (PID: $PID) listening on port $($Conn.LocalPort)..." -ForegroundColor Red
                Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue
            }
        }
        Write-Host "[+] Local processes terminated." -ForegroundColor Green
    } else {
        Write-Host "[+] No active local processes found on stack ports." -ForegroundColor Green
    }
}

function Deploy-Docker {
    Write-Host "[*] Deploying using Docker Compose..." -ForegroundColor Cyan
    
    # Check if Docker is installed
    if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
        Write-Host "[!] ERROR: Docker is not installed or not in System PATH!" -ForegroundColor Red
        Write-Host "    Please install Docker Desktop or run in Local Native mode." -ForegroundColor Yellow
        return
    }

    # Ensure no port collisions
    Stop-AllServices

    Write-Host "[*] Starting containers via Docker Compose..." -ForegroundColor Gray
    docker-compose up -d --build

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "🎉 DOCKER CONTAINERS SUCCESSFULLY STARTED" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "  🌐 React Dashboard:  http://localhost:5173" -ForegroundColor Green
        Write-Host "  🔌 FastAPI Backend:  http://localhost:8000" -ForegroundColor Green
        Write-Host "  📲 WhatsApp Bridge:  http://localhost:3002" -ForegroundColor Green
        Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
        Write-Host "👉 IMPORTANT: First-time WhatsApp bridge setup requires scanning a QR code." -ForegroundColor Yellow
        Write-Host "   Run this command in a new terminal window to scan the QR code:" -ForegroundColor Yellow
        Write-Host "   " -NoNewline
        Write-Host "docker attach whatsapp_bridge" -ForegroundColor Cyan
        Write-Host "   Once scanned, press " -NoNewline
        Write-Host "Ctrl+P, Ctrl+Q" -ForegroundColor Cyan -NoNewline
        Write-Host " to safely detach from the container terminal." -ForegroundColor Yellow
        Write-Host "================================================================================" -ForegroundColor Green
    } else {
        Write-Host "[!] Docker deployment failed. See logs above." -ForegroundColor Red
    }
}

function Deploy-Local {
    Write-Host "[*] Deploying in Local Native Process mode (Separate Terminals)..." -ForegroundColor Cyan

    # Verify Node.js and NPM
    if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
        Write-Host "[!] ERROR: Node.js/NPM is not installed! It is required for Frontend and WhatsApp Bridge." -ForegroundColor Red
        return
    }

    # Verify Python
    if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
        Write-Host "[!] ERROR: Python is not installed! It is required for the backend." -ForegroundColor Red
        return
    }

    # Clean up prior instances
    Stop-AllServices
    Write-Host ""

    # 1. SETUP WHATSAPP BRIDGE
    Write-Host "[*] Setting up WhatsApp Bridge..." -ForegroundColor Gray
    $BridgeDir = Join-Path $PipelineDir "whatsapp-bridge-js"
    if (-not (Test-Path (Join-Path $BridgeDir "node_modules"))) {
        Write-Host "[-] Installing WhatsApp Bridge dependencies (first run)..." -ForegroundColor Yellow
        Push-Location $BridgeDir
        npm install
        Pop-Location
    }

    # 2. SETUP PYTHON BACKEND VENV & DEPENDENCIES
    Write-Host "[*] Setting up Python Backend..." -ForegroundColor Gray
    $BackendDir = Join-Path $PipelineDir "python-backend"
    $VenvDir = Join-Path $BackendDir "venv"
    if (-not (Test-Path $VenvDir)) {
        Write-Host "[-] Creating Python virtual environment (first run)..." -ForegroundColor Yellow
        python -m venv $VenvDir
    }
    
    # Install dependencies inside venv
    Write-Host "[-] Installing/updating backend pip dependencies..." -ForegroundColor Yellow
    $VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
    $Requirements = Join-Path $BackendDir "requirements.txt"
    & $VenvPip install -r $Requirements

    # 3. SETUP FRONTEND
    Write-Host "[*] Setting up React Frontend..." -ForegroundColor Gray
    $FrontendDir = Join-Path $PipelineDir "frontend"
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Host "[-] Installing React Frontend dependencies (first run)..." -ForegroundColor Yellow
        Push-Location $FrontendDir
        npm install
        Pop-Location
    }

    # 4. LAUNCH SERVICES IN NEW CONSOLE WINDOWS FOR MAXIMUM VISIBILITY
    Write-Host "[*] Spinning up the stack..." -ForegroundColor Green

    # Launch WhatsApp Bridge
    Write-Host "[+] Launching WhatsApp Bridge in separate window..." -ForegroundColor Green
    Start-Process cmd -ArgumentList "/k cd /d `"$BridgeDir`" && title WhatsApp Bridge (Port 3002) && npm start"
    Start-Sleep -Seconds 2

    # Launch FastAPI Backend
    Write-Host "[+] Launching FastAPI Backend in separate window..." -ForegroundColor Green
    $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
    Start-Process cmd -ArgumentList "/k cd /d `"$BackendDir`" && title FastAPI Backend (Port 8000) && `"$VenvPython`" -m uvicorn main:app --reload --port 8000"
    Start-Sleep -Seconds 2

    # Launch React Frontend Dashboard
    Write-Host "[+] Launching React Frontend Dashboard in separate window..." -ForegroundColor Green
    Start-Process cmd -ArgumentList "/k cd /d `"$FrontendDir`" && title React Dashboard (Port 5173) && npm run dev"

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "🎉 LOCAL PROCESS STACK DEPLOYED" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "  🟢 React Dashboard:  http://localhost:5173" -ForegroundColor Green
    Write-Host "  🟢 FastAPI Backend:  http://localhost:8000" -ForegroundColor Green
    Write-Host "  🟢 WhatsApp Bridge:  http://localhost:3002" -ForegroundColor Green
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
    Write-Host "👉 CHECK THE OPEN TERMINAL WINDOWS:" -ForegroundColor Yellow
    Write-Host "   1. Scan the QR code shown in the 'WhatsApp Bridge' console to authenticate." -ForegroundColor Yellow
    Write-Host "   2. Monitor the 'FastAPI Backend' console for LangGraph pipeline execution logs." -ForegroundColor Yellow
    Write-Host "   3. Keep the windows open. To stop everything, select Option 3 in this menu." -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Green
}

# --- INTERACTIVE MENU LOOP ---
do {
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
    Write-Host "  [1] Deploy Stack via Docker Compose (Recommended)" -ForegroundColor Cyan
    Write-Host "  [2] Deploy Stack via Local Native Processes (Separate Terminals)" -ForegroundColor Cyan
    Write-Host "  [3] Stop All Running Services (Docker + Local Ports)" -ForegroundColor Yellow
    Write-Host "  [4] Check Port & Service Status" -ForegroundColor White
    Write-Host "  [5] Exit" -ForegroundColor Red
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor Gray
    $Selection = Read-Host "Choose an option [1-5]"

    switch ($Selection) {
        "1" { Deploy-Docker }
        "2" { Deploy-Local }
        "3" { Stop-AllServices }
        "4" { Show-Ports }
        "5" { Write-Host "Goodbye!" -ForegroundColor Green; break }
        default { Write-Host "[!] Invalid option, please enter 1 to 5." -ForegroundColor Red }
    }
    Write-Host ""
} while ($Selection -ne "5")
