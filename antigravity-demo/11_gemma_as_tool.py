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

"""Demo: Local Gemma 3 (Ollama) as a custom tool inside the Antigravity SDK.

Architecture:
  Gemini (cloud, orchestrator) --calls--> ask_gemma tool --calls--> Ollama (local)

This example shows:
1. How to register a local Ollama model as a custom tool in LocalAgentConfig.
2. How Gemini decides WHEN to delegate to Gemma based on the user prompt.
3. How tool docstrings guide the orchestrator's routing decisions.
4. How to pre-warm Ollama to avoid first-call latency inside agent turns.

Prerequisites:
  - GEMINI_API_KEY set in .env (cloud orchestration requires a Gemini key)
  - Ollama running locally: ollama serve
  - gemma3 model pulled:    ollama pull gemma3

To run:
  python 11_gemma_as_tool.py

Criteria for correct script performance:
  1. Script exits with return code 0.
  2. Gemini calls the ask_gemma tool at least once.
  3. The ask_gemma tool returns a non-empty response from local Ollama.
  4. Agent produces a meaningful final response incorporating Gemma's answer.
"""

import asyncio
import json
import urllib.error
import urllib.request
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy

load_dotenv()

# ---------------------------------------------------------------------------
# Ollama / Gemma configuration
# ---------------------------------------------------------------------------

_OLLAMA_URL   = "http://localhost:11434/v1/chat/completions"
_GEMMA_MODEL  = "gemma3:latest"
_TIMEOUT_SECS = 180  # generous: local CPU inference can be slow


def _ollama_chat(messages: list[dict]) -> str:
  """Send a messages list to Ollama and return the reply text."""
  payload = json.dumps({
      "model": _GEMMA_MODEL,
      "messages": messages,
      "stream": False,
  }).encode()
  req = urllib.request.Request(
      _OLLAMA_URL, data=payload,
      headers={"Content-Type": "application/json"}, method="POST"
  )
  try:
    with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS) as r:
      return json.loads(r.read())["choices"][0]["message"]["content"]
  except urllib.error.URLError as exc:
    raise RuntimeError(
        f"Cannot reach Ollama at {_OLLAMA_URL}. "
        f"Is 'ollama serve' running?\n  {exc}"
    ) from exc
  except TimeoutError as exc:
    raise RuntimeError(
        f"Ollama timed out after {_TIMEOUT_SECS}s — "
        "the model may need more time on your hardware."
    ) from exc


def _warm_up_ollama() -> None:
  """Pre-load Gemma weights into RAM with a 1-token ping.

  Without this, the first real tool call inside an agent turn can hit the
  Antigravity WebSocket timeout while Ollama is still loading the model.
  """
  print(f"  [warm-up] Loading {_GEMMA_MODEL} into memory via Ollama...")
  payload = json.dumps({
      "model": _GEMMA_MODEL,
      "messages": [{"role": "user", "content": "hi"}],
      "stream": False,
      "options": {"num_predict": 1},
  }).encode()
  req = urllib.request.Request(
      _OLLAMA_URL, data=payload,
      headers={"Content-Type": "application/json"}, method="POST"
  )
  with urllib.request.urlopen(req, timeout=_TIMEOUT_SECS):
    pass
  print(f"  [warm-up] {_GEMMA_MODEL} is ready.\n")


# ---------------------------------------------------------------------------
# Custom tool — registered with the Antigravity SDK
# ---------------------------------------------------------------------------

def ask_gemma(question: str) -> str:
  """Ask the local Gemma 3 model (running via Ollama) a question.

  Use this tool whenever:
  - The user explicitly requests a local model or offline response.
  - You want a second opinion from a different AI model.
  - The task is AI/ML knowledge that a local model can handle well.

  Gemma 3 specs: 4.3B parameters, 128K context window, runs fully offline.

  Args:
    question: The question or instruction to send to Gemma 3.

  Returns:
    Gemma 3's response as a plain text string.
  """
  return _ollama_chat([{"role": "user", "content": question}])


def ask_gemma_with_context(context: str, question: str) -> str:
  """Ask the local Gemma 3 model a question with additional background context.

  Use this tool when the user wants Gemma's perspective on something that
  requires extra background information to answer well.

  Args:
    context: Background information or prior conversation to pass to Gemma.
    question: The specific question to ask Gemma given the context.

  Returns:
    Gemma 3's response as a plain text string.
  """
  messages = [
      {"role": "system", "content": "You are a concise, helpful AI assistant."},
      {"role": "user",   "content": f"Context: {context}\n\nQuestion: {question}"},
  ]
  return _ollama_chat(messages)


# ---------------------------------------------------------------------------
# Rate-limit helpers
# ---------------------------------------------------------------------------

# Each agent.chat() with a tool call costs ~3 Gemini requests
# (orchestrate → tool_call → synthesize). Free tier is 20 RPM.
# Waiting 65s between turns resets the 1-minute sliding window.
_TURN_COOLDOWN_SECS = 65


async def _cooldown(secs: int) -> None:
  """Wait `secs` seconds with a live countdown so the user sees progress."""
  print(f"  [rate-limit] Waiting {secs}s to reset the Gemini free-tier RPM "
        "window before next turn...")
  for remaining in range(secs, 0, -5):
    print(f"  [rate-limit] {remaining}s remaining...", end="\r")
    await asyncio.sleep(min(5, remaining))
  print()


# ---------------------------------------------------------------------------
# Agent configuration & demo
# ---------------------------------------------------------------------------

async def main() -> None:
  # Step 1: Pre-warm Ollama so the model is loaded before the agent starts.
  _warm_up_ollama()

  # Step 2: Build the LocalAgentConfig.
  # Gemini is the orchestrator; Gemma tools are explicitly allow-listed.
  config = LocalAgentConfig(
      model="gemini-2.5-flash",
      tools=[ask_gemma, ask_gemma_with_context],
      system_instructions=(
          "You are a helpful AI assistant with access to a local Gemma 3 model "
          "running via Ollama on the user's machine. "
          "When the user asks for a local model response, or wants Gemma's "
          "perspective, ALWAYS use the ask_gemma or ask_gemma_with_context tool. "
          "Do not answer those questions yourself — delegate to Gemma. "
          "After receiving Gemma's response, summarise or present it clearly."
      ),
      policies=[
          policy.deny_all(),
          policy.allow(ask_gemma.__name__),
          policy.allow(ask_gemma_with_context.__name__),
      ],
  )

  print("=== Antigravity SDK: Local Gemma 3 as a Tool Demo ===")
  print("    Orchestrator : Gemini (cloud, gemini-2.5-flash)")
  print("    Tool backend : Gemma 3 via Ollama (local, offline)")
  print("    Note: free-tier Gemini = 20 RPM; a cooldown is added between")
  print("          turns so consecutive calls do not exhaust the quota.\n")

  # Step 3: Each prompt runs in its own Agent context to avoid WebSocket
  # connection reuse across turns that hit rate-limit retries.
  prompts = [
      # Prompt 1: Simple delegation — Gemini calls ask_gemma
      "Use the local Gemma model to explain what a LangGraph StateGraph is "
      "in simple terms.",

      # Prompt 2: Context-aware delegation — Gemini calls ask_gemma_with_context
      (
          "I am building an AI newsletter agent that reads WhatsApp messages, "
          "researches topics, and publishes to GitHub Pages. "
          "Ask the local Gemma model: what are the 3 biggest risks in this "
          "architecture and how would you mitigate them?"
      ),
  ]

  for i, prompt in enumerate(prompts, 1):
    print(f"--- Turn {i} of {len(prompts)} ---")
    print(f"  User  : {prompt}\n")

    try:
      async with Agent(config) as agent:
        response = await agent.chat(prompt)
        reply = await response.text()
      # Safe-print: replace unencodable chars (emoji etc.) for Windows terminals
      safe = reply.encode("cp1252", errors="replace").decode("cp1252")
      print(f"  Agent : {safe}\n")
    except Exception as exc:  # pylint: disable=broad-except
      print(f"  [error] Turn {i} failed: {exc}\n")

    # Cooldown between turns — skip after the last prompt
    if i < len(prompts):
      await _cooldown(_TURN_COOLDOWN_SECS)

  print("=== Demo complete ===")


if __name__ == "__main__":
  asyncio.run(main())

