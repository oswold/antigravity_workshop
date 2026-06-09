# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Demo: Local Gemma 3 model via Ollama (OpenAI-compatible API).

This example shows:
- How to call a local Gemma 3 model (4.3B, 128K context) running via Ollama.
- Uses Ollama's OpenAI-compatible REST endpoint — NO Gemini API key required.
- Demonstrates single-turn Q&A and multi-turn stateful conversation.
- Shows how to inspect model metadata (version, parameters, context length).

Gemma 3 specs (gemma3:latest):
  - Architecture : Gemma 3
  - Parameters   : 4.3B
  - Context      : 131,072 tokens (128K)
  - Quantization : Q4_K_M
  - Capabilities : completion + vision

Prerequisites:
  ollama serve        # Ollama must be running (usually auto-starts)
  ollama pull gemma3  # Pull the model once if not already present

To run:
  python 10_local_gemma.py
"""

import json
import time
import urllib.error
import urllib.request

OLLAMA_BASE   = "http://localhost:11434"
OLLAMA_CHAT   = f"{OLLAMA_BASE}/v1/chat/completions"
OLLAMA_MODELS = f"{OLLAMA_BASE}/api/tags"
GEMMA_MODEL   = "gemma3:latest"
TIMEOUT_SECS  = 180  # generous: local inference on CPU can be slow


def safe_print(text: str) -> None:
    """Print text to the Windows terminal, replacing unencodable characters
    (e.g. emoji from Gemma responses) with '?' so cp1252 never crashes."""
    encoded = text.encode("cp1252", errors="replace").decode("cp1252")
    print(encoded)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post(url: str, body: dict) -> dict:
    """POST JSON to Ollama and return the parsed response."""
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_BASE}. "
            f"Is 'ollama serve' running?\n  {exc}"
        ) from exc


def _get(url: str) -> dict:
    """GET JSON from Ollama."""
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama unreachable: {exc}") from exc


# ---------------------------------------------------------------------------
# Gemma client
# ---------------------------------------------------------------------------

class GemmaChat:
    """Minimal stateful chat client backed by local Ollama Gemma 3."""

    def __init__(self, model: str = GEMMA_MODEL, system: str | None = None):
        self.model = model
        self.history: list[dict] = []
        if system:
            self.history.append({"role": "system", "content": system})

    def ask(self, prompt: str) -> str:
        """Send a user message and return Gemma's reply (stateful)."""
        self.history.append({"role": "user", "content": prompt})
        data = _post(OLLAMA_CHAT, {
            "model": self.model,
            "messages": self.history,
            "stream": False,
        })
        reply = data["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": reply})
        return reply


def warm_up(model: str = GEMMA_MODEL) -> None:
    """Load model weights into memory with a 1-token ping."""
    print(f"  [warm-up] Loading {model} into memory...")
    _post(OLLAMA_CHAT, {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False,
        "options": {"num_predict": 1},
    })
    print(f"  [warm-up] {model} ready.\n")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def show_model_info() -> None:
    """Print installed Gemma model details from Ollama."""
    models = _get(OLLAMA_MODELS).get("models", [])
    gemma_models = [m for m in models if "gemma" in m["name"].lower()]
    print("  Installed Gemma models:")
    for m in gemma_models:
        size_gb = m["size"] / 1e9
        print(f"    - {m['name']}  ({size_gb:.1f} GB)  "
              f"digest={m['digest'][:12]}")
    print()


def demo_single_turn(chat: GemmaChat) -> None:
    """Single-turn Q&A — each question is independent."""
    print("--- Single-turn Q&A ---\n")
    questions = [
        "What is LangGraph? Answer in exactly 2 sentences.",
        "What is the difference between an AI agent and a chatbot?",
    ]
    for q in questions:
        print(f"  User   : {q}")
        t0 = time.time()
        # Use a fresh chat instance so history doesn't carry over
        reply = GemmaChat(model=chat.model).ask(q)
        elapsed = time.time() - t0
        safe_print(f"  Gemma  : {reply}")
        print(f"  (took {elapsed:.1f}s)\n")


def demo_multi_turn(chat: GemmaChat) -> None:
    """Multi-turn conversation — Gemma remembers prior context."""
    print("--- Multi-turn Conversation ---\n")
    turns = [
        "My name is Siva. Remember that.",
        "What is my name?",
        "Now explain what a stateful AI agent is, in the context of our chat.",
    ]
    for turn in turns:
        print(f"  User   : {turn}")
        t0 = time.time()
        reply = chat.ask(turn)
        elapsed = time.time() - t0
        safe_print(f"  Gemma  : {reply}")
        print(f"  (took {elapsed:.1f}s)\n")


def main() -> None:
    print("=== Local Gemma 3 Demo via Ollama (no API key required) ===\n")

    # 1. Show what's installed
    show_model_info()

    # 2. Warm up to avoid cold-start latency on first real call
    warm_up(GEMMA_MODEL)

    # 3. Single-turn demo
    single_chat = GemmaChat(
        model=GEMMA_MODEL,
        system="You are a concise technical assistant. Keep answers brief.",
    )
    demo_single_turn(single_chat)

    # 4. Multi-turn demo (stateful — history is maintained)
    multi_chat = GemmaChat(
        model=GEMMA_MODEL,
        system="You are a helpful assistant. Remember everything the user tells you.",
    )
    demo_multi_turn(multi_chat)

    print("=== Demo complete ===")


if __name__ == "__main__":
    main()
