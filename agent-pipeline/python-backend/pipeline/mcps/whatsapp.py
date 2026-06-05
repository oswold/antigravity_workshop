"""
WhatsApp HTTP Bridge client — calls the Baileys-based Node.js bridge.

The bridge runs at http://localhost:3002 and exposes:
  GET /health             → { connected: true/false }
  GET /messages?days=N    → list of self-messages

Start the bridge first:
  cd agent-pipeline/whatsapp-bridge-js
  node bridge.js
  (Scan QR code on first run — session saved permanently after that)
"""
import re
import httpx
from datetime import datetime, timedelta, timezone

import os
BRIDGE_URL   = os.environ.get("WHATSAPP_BRIDGE_URL", "http://localhost:3002")
URL_PATTERN  = re.compile(r"https?://[^\s>\"']+")


def _check_bridge() -> bool:
    """Return True if the bridge is running and WhatsApp is connected."""
    try:
        r = httpx.get(f"{BRIDGE_URL}/health", timeout=3)
        return r.json().get("connected", False)
    except Exception:
        return False


def fetch_whatsapp_self_messages(days: int = 7) -> list[dict]:
    """
    Fetch messages you sent to yourself in the last N days.
    Raises RuntimeError with clear instructions if the bridge is not running.
    """
    # ── Check bridge health ────────────────────────────────────────────────
    try:
        health = httpx.get(f"{BRIDGE_URL}/health", timeout=5)
    except httpx.ConnectError:
        repo_path = os.environ.get("REPO_PATH", "<your-repo-path>")
        raise RuntimeError(
            "WhatsApp bridge is not running.\n"
            "Start it with:\n"
            f"  cd {repo_path}/agent-pipeline/whatsapp-bridge-js\n"
            "  node bridge.js\n"
            "Then scan the QR code with your WhatsApp mobile app."
        )

    health_data = health.json()
    if not health_data.get("connected"):
        raise RuntimeError(
            "WhatsApp bridge is running but not yet connected.\n"
            "Check the bridge terminal — scan the QR code if shown."
        )

    # ── Fetch self-messages ────────────────────────────────────────────────
    r = httpx.get(
        f"{BRIDGE_URL}/messages",
        params={"days": days, "self_only": "true"},
        timeout=15,
    )
    r.raise_for_status()
    raw_messages = r.json()

    notes = []
    for i, msg in enumerate(raw_messages):
        text  = msg.get("text", "").strip()
        if not text or len(text) < 5:
            continue

        # Convert epoch timestamp to readable date
        ts = msg.get("timestamp", 0)
        if isinstance(ts, dict):              # Baileys Long object
            ts = ts.get("low", 0)
        try:
            date_str = datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            date_str = f"message-{i+1}"

        links = URL_PATTERN.findall(text)

        notes.append({
            "id":    msg.get("id", i + 1),
            "text":  text,
            "date":  date_str,
            "links": links,
            "type":  "whatsapp",
        })

    print(f"[WhatsApp Bridge] ✅ {len(notes)} self-messages fetched (last {days} days)")
    return notes
