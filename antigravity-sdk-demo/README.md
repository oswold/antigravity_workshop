# Advanced Google Antigravity SDK Demos

This directory ships **12 standalone demo scripts** that illustrate the core features of the `google‑antigravity` SDK – from basic model calls to hybrid cloud‑local LLM orchestration.

---

## 📦 Prerequisites

### 1️⃣ Python & SDK
```bash
pip install google-antigravity python-dotenv
pip install --upgrade protobuf
```

### 2️⃣ Gemini API Key
Create a `.env` file in the repository root (or copy `.env.example`):
```bash
GEMINI_API_KEY=your_api_key_here
```
The SDK reads `GEMINI_API_KEY` automatically via `load_dotenv()`.

### 3️⃣ Ollama (optional, for scripts 10 & 11)
```bash
# Install Ollama (https://ollama.com)
ollama serve                # Starts the Ollama server on localhost:11434
ollama pull gemma3          # Downloads Gemma‑3 (≈3.3 GB)
```
Both **10_local_gemma.py** and **11_gemma_as_tool.py** depend on this local model.

---

## 🚀 Running Individual Demo Scripts
From the `antigravity-demo/` folder you can execute any script directly:
```bash
cd antigravity-demo
python <script_name>.py
```
Each script header lists required prerequisites (Gemini API key, Ollama, etc.) and the key concepts it demonstrates.

---

## 📚 Script Summary Table
| Script | Gemini API Key | Ollama | Key Feature |
|--------|:--------------:|:------:|-------------|
| `0_model_passing.py` | ✅ | ❌ | Basic agent hello world |
| `1_single_and_multi_agent.py` | ✅ | ❌ | Parallel agents with `asyncio.gather` |
| `2_memory_types.py` | ✅ | ❌ | Conversational memory inspection |
| `3_guardrails.py` | ✅ | ❌ | Tool access policies |
| `4_hooks.py` | ✅ | ❌ | Post‑tool lifecycle hooks |
| `5_custom_tools.py` | ✅ | ❌ | Custom + stateful tools (`ToolContext`) |
| `6_triggers.py` | ✅ | ❌ | Async timer‑based triggers |
| `7_mcp_docker_gateway.py` | ✅ | ❌ | MCP via Docker streaming |
| `8_parallel_subagents.py` | ✅ | ❌ | Parallel sub‑agent orchestration |
| `9_human_in_the_loop.py` | ✅ | ❌ | HITL approval gates |
| `10_local_gemma.py` | ❌ | ✅ | Standalone local Gemma 3 (no cloud) |
| `11_gemma_as_tool.py` | ✅ | ✅ | Gemma 3 registered as a custom tool inside the Antigravity SDK |

---

## 🛠️ Additional Resources
- Official SDK examples: <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/examples>

---

*Happy working with Antigravity SDK!*
