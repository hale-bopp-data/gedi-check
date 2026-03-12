"""
Fire & forget: notifica n8n in background.
Non blocca mai. Se il webhook non risponde entro 2s, muore silenziosamente.
"""

import json
import os
import threading
import urllib.request
from typing import Any

N8N_WEBHOOK = os.environ.get(
    "GEDI_N8N_WEBHOOK",
    "http://80.225.86.168:5678/webhook/orchestrator.gedi.validate",
)
TIMEOUT = 2  # secondi — non blocca mai oltre


def _post(payload: dict[str, Any]) -> None:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            N8N_WEBHOOK,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "gedi-check/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT):
            pass
    except Exception:
        pass  # graceful degradation — non propagare mai


def notify_async(trigger: str, context: dict[str, Any]) -> None:
    """Lancia il webhook in background. Ritorna immediatamente."""
    payload = {
        "source": "gedi-check",
        "trigger": trigger,
        "context": context,
    }
    t = threading.Thread(target=_post, args=(payload,), daemon=True)
    t.start()
    # Non aspettare: fire & forget
