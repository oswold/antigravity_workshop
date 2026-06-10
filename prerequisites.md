# 📋 Workshop Prerequisites Guide — Agentic AI 101

Welcome to **Agentic AI 101: Build Your Automated Newsletter & Research Agent Pipeline**! This guide details all dependencies, account setups, and configuration settings required for the workshop.

---

## 📦 Repositories to Fork & Clone
Please fork and clone the following repositories before the workshop begins:

1.  **Workshop Project Repo** (FastAPI backend, React frontend, WhatsApp bridge, deployment scripts, and SDK demos):
    *   **Repository URL**: [github.com/oswold/antigravity_workshop](https://github.com/oswold/antigravity_workshop)
    *   **Clone command**:
        ```bash
        git clone https://github.com/oswold/antigravity_workshop
        ```
2.  **Newsletter Output Template Repo** (The target repository where the agent will publish your compiled HTML and markdown newsletters):
    *   **Repository URL**: [github.com/oswold/ai-pulse-newsletter](https://github.com/oswold/ai-pulse-newsletter)
    *   *(Note: You must fork this repository to your own GitHub account first so that your PAT has permission to publish to it).*

---

## ⚡ 1. Antigravity CLI (Gemini CLI)
The **Gemini CLI** (also referred to as the Antigravity CLI) is a command-line interface used to run agent sessions, execute reusable prompt-driven skills, and test Model Context Protocol (MCP) tools directly. More information can be found at [antigravity.google/product/antigravity-cli](https://antigravity.google/product/antigravity-cli).

### 📦 System Requirements & Software
*   **Node.js & npm**: Version `18.0.0` or higher ([nodejs.org](https://nodejs.org))
*   **Git**: Required for worktree isolation and version control ([git-scm.com](https://git-scm.com))

### 🛠️ Installation & Setup
1.  **Install the CLI globally**:
    ```bash
    npm install -g @google/gemini-cli
    ```
2.  **Configure your API Key**:
    *   **PowerShell (Windows):**
        ```powershell
        $env:GEMINI_API_KEY="your-gemini-api-key"
        ```
    *   **bash/zsh (Mac/Linux):**
        ```bash
        export GEMINI_API_KEY="your-gemini-api-key"
        ```
3.  **Context Ingestion (`GEMINI.md`)**:
    Ensure the `GEMINI.md` file is present in your project root. When you run `gemini` from the terminal, the CLI automatically loads this file to define the agent's role, safety guidelines, PII hooks, and available tools.

---

## 🖥️ 2. Antigravity IDE (Newsletter Generator Application)
The **Newsletter Generator Application** is the core workshop project. It runs inside the **Antigravity IDE** alongside a local React frontend, a FastAPI backend orchestrating a LangGraph state graph, and a Node.js Baileys-based WhatsApp bridge. 

You can download the **Antigravity IDE and Agent Manager** at [antigravity.google/download](https://antigravity.google/download).

### 🔐 Accounts & Credentials
To run the full end-to-end pipeline with publishing, you must prepare:

*   **Google AI Studio Account**: Generate a API Key at [aistudio.google.com](https://aistudio.google.com).
*   **GitHub Personal Access Token (PAT)**: Generate a Fine-grained PAT at [GitHub Settings](https://github.com/settings/tokens?type=beta) with **Repository Permissions -> Contents: Read & Write** enabled.
*   **Gmail Account & App Password**: Set up a [Gmail App Password](https://myaccount.google.com/apppasswords) (for sending SMTP newsletter dispatches).

### 🐳 Option A: Containerized Mode (Docker - Recommended)
If you run via containers, Docker handles all runtime dependencies (Node.js, Python, npm).

*   **Requirements**: Docker Desktop installed and running ([docker.com](https://www.docker.com/products/docker-desktop/)).
*   **Setup Commands**:
    1.  Create the external named volume to store WhatsApp credentials:
        ```powershell
        docker volume create podcasts_whatsapp_auth
        ```
    2.  Start the containers:
        ```powershell
        docker-compose up -d --build
        ```
    3.  Scan WhatsApp QR Code (first-time login):
        ```powershell
        docker attach --detach-keys="ctrl-x" whatsapp_bridge
        ```
        *(Scan the QR code in the terminal, then press **`Ctrl+X`** to detach safely without terminating the container).*

### 🐍 Option B: Local Native Process Mode
If you prefer running services directly on your host machine:

*   **Requirements**:
    *   **Python**: Version `3.10` or higher ([python.org](https://www.python.org/downloads/))
    *   **Node.js**: Version `18.0.0` or higher
*   **Setup Commands**:
    1.  **WhatsApp Bridge Setup**:
        ```bash
        cd agent-pipeline/whatsapp-bridge-js
        npm install
        ```
    2.  **Python Backend Setup**:
        ```bash
        cd ../python-backend
        python -m venv venv
        # Activate Virtualenv:
        # Windows: .\venv\Scripts\activate  |  Mac/Linux: source venv/bin/activate
        pip install -r requirements.txt
        ```
    3.  **Frontend Dashboard Setup**:
        ```bash
        cd ../frontend
        npm install
        ```

---

## 🦙 3. Antigravity SDK
The **Antigravity SDK** (`google-antigravity`) is a Python library used to build custom agentic workflows, memory systems, parallel subagents, and local model integrations. The open-source repository is hosted at [github.com/google-antigravity/antigravity-sdk-python](https://github.com/google-antigravity/antigravity-sdk-python).

### 📦 Installation
In your Python environment, install the SDK and dependencies:
```bash
pip install google-antigravity python-dotenv --upgrade protobuf
```

### 🗝️ Environment Configuration
The SDK looks up the `GEMINI_API_KEY` automatically. Ensure it is set in your current session (via terminal export) or via a `.env` file:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

### 🦙 Local Gemma 3 Orchestration (Optional)
To run local offline model agents (e.g. demos `10_local_gemma.py` and `11_gemma_as_tool.py`), you need Ollama:

1.  Download and install Ollama from [ollama.com](https://ollama.com).
2.  Start the Ollama serve daemon:
    ```bash
    ollama serve
    ```
3.  Pull the **Gemma 3** weights (approx. 3.3 GB):
    ```bash
    ollama pull gemma3
    ```
4.  Verify the model is loaded:
    ```bash
    ollama list
    ```

---

## 📋 Prerequisites Configuration Checklist
Ensure your `.env` file in the project root has the following variables filled out before running the pipeline:

```ini
# Gemini API Key (Required)
GEMINI_API_KEY=AQ.Ab8RN6...

# Repository absolute path
REPO_PATH=e:\antigravity_workshop

# GitHub Publishing settings (Optional)
GITHUB_OWNER=your-github-username
GITHUB_REPO=ai-pulse-newsletter
GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...

# Email settings (Optional)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Docker MCP Gateway Authentication (Optional)
MCP_GATEWAY_AUTH_TOKEN=5rzfkug01zyeg...
```

---

## 🌐 Useful Reference URLs
*   **Antigravity IDE & Agent Manager Download**: [antigravity.google/download](https://antigravity.google/download)
*   **Antigravity CLI Product Page**: [antigravity.google/product/antigravity-cli](https://antigravity.google/product/antigravity-cli)
*   **Antigravity SDK Repository**: [github.com/google-antigravity/antigravity-sdk-python](https://github.com/google-antigravity/antigravity-sdk-python)
*   **Antigravity Docs**: [antigravity.google/docs/home](https://antigravity.google/docs/home)
*   **Antigravity CLI Code README**: [github.com/google-antigravity/antigravity-cli/blob/main/README.md](https://github.com/google-antigravity/antigravity-cli/blob/main/README.md)
*   **Antigravity SDK Python Examples**: [github.com/google-antigravity/antigravity-sdk-python/tree/main/examples](https://github.com/google-antigravity/antigravity-sdk-python/tree/main/examples)
*   **Google AI Studio (API Keys)**: [aistudio.google.com](https://aistudio.google.com)
*   **Ollama (Local Models)**: [ollama.com](https://ollama.com)
*   **Model Context Protocol (MCP) Introduction**: [modelcontextprotocol.io/docs/getting-started/intro](https://modelcontextprotocol.io/docs/getting-started/intro)
*   **Docker AI MCP Gateway Guide**: [docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
*   **Antigravity MCP Documentation**: [antigravity.google/docs/mcp](https://antigravity.google/docs/mcp)



