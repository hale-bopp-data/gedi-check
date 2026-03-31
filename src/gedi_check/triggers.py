"""
GEDI trigger logic — 3 trigger, zero dipendenze esterne.
Importato da gedi-check.py.
"""

import json
import os
import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Exclusion taxonomy — caricata da exclusions.json, arricchita nel tempo
# ---------------------------------------------------------------------------

_EXCLUSIONS_FILE = Path(__file__).parent / "exclusions.json"


def _load_exclusions() -> list[str]:
    """Carica tutte le frasi di esclusione da exclusions.json."""
    try:
        data = json.loads(_EXCLUSIONS_FILE.read_text(encoding="utf-8"))
        phrases: list[str] = []
        for key, section in data.items():
            if key.startswith("_"):
                continue
            if isinstance(section, dict) and "phrases" in section:
                phrases.extend(section["phrases"])
        return [p.lower() for p in phrases]
    except Exception:
        return []  # graceful degradation


_EXCLUSIONS: list[str] = _load_exclusions()


def _is_excluded(text: str) -> bool:
    """True se il testo contiene una frase di esclusione nota."""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in _EXCLUSIONS)


# ---------------------------------------------------------------------------
# Trigger 1 — Fix Keyword
# ---------------------------------------------------------------------------

FIX_KEYWORDS = re.compile(
    r"\b(fix|workaround|patch|hotfix|cerotto|quick.?fix|hardcoded|hardcode|"
    r"delete|drop|rm\s+-rf|banda\s+straccia|temp|hack|kludge|hotpatch|"
    r"bypass|duct.?tape|#\s*TODO|#\s*HACK|#\s*FIXME)\b",
    re.IGNORECASE,
)

OODA_MESSAGE = """
┌─────────────────────────────────────────────────────────────────┐
│  🐢  GEDI OODA — Hai chiesto consiglio a GEDI?                  │
├─────────────────────────────────────────────────────────────────┤
│  Parola trigger rilevata: {keyword}                              │
│                                                                   │
│  OBSERVE  → Qual è il sintomo esatto?                            │
│  ORIENT   → È un fix strutturale o un cerotto?                  │
│  DECIDE   → Esiste un guardrail che impedisce la recidiva?       │
│  ACT      → Dopo il fix il sistema è più robusto di prima?      │
│                                                                   │
│  (Principio G8 Antifragile — REGOLA GEDI FIX S118)              │
└─────────────────────────────────────────────────────────────────┘
"""


def check_fix_keyword(text: str) -> tuple[bool, str]:
    """Ritorna (triggered, keyword). Non blocca — advisory."""
    if _is_excluded(text):
        return False, ""
    m = FIX_KEYWORDS.search(text)
    if m:
        return True, m.group(0)
    return False, ""


# ---------------------------------------------------------------------------
# Trigger 2 — Error Repeat (Regola dei 3 Errori)
# ---------------------------------------------------------------------------

SESSION_ID = os.environ.get("GEDI_SESSION", str(os.getpid()))
ERROR_FILE = Path(f"/tmp/gedi-errors-{SESSION_ID}.json")


def _load_error_log() -> dict:
    if ERROR_FILE.exists():
        try:
            return json.loads(ERROR_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_error_log(log: dict) -> None:
    try:
        ERROR_FILE.write_text(json.dumps(log, indent=2))
    except OSError:
        pass


def record_error(exit_code: int, stderr_snippet: str = "", threshold: int = 3) -> tuple[bool, int]:
    """
    Registra un errore. Ritorna (should_block, count).
    Blocca se lo stesso exit_code appare threshold+ volte.
    Threshold configurabile dal profilo attivo (dev=5, ams=3, prod=2).
    """
    log = _load_error_log()
    key = str(exit_code)
    entry = log.get(key, {"count": 0, "first_seen": time.time(), "stderr": []})
    entry["count"] += 1
    entry["last_seen"] = time.time()
    if stderr_snippet and len(entry["stderr"]) < 5:
        entry["stderr"].append(stderr_snippet[:200])
    log[key] = entry
    _save_error_log(log)
    return entry["count"] >= threshold, entry["count"]


ERROR_BLOCK_MESSAGE = """
┌─────────────────────────────────────────────────────────────────┐
│  🛑  GEDI — REGOLA DEI 3 ERRORI                                 │
├─────────────────────────────────────────────────────────────────┤
│  Exit code {code} è apparso {count} volte in questa sessione.   │
│                                                                   │
│  "Se capita più di tre sei uno che non dà da lavorare."          │
│                        — Regola Antifragile (gbelviso)           │
│                                                                   │
│  STOP. Identifica la causa root strutturale prima di             │
│  continuare. Ripetere lo stesso errore non è debugging.          │
│                                                                   │
│  Sessione: {session}                                             │
│  Log:      {log_file}                                            │
└─────────────────────────────────────────────────────────────────┘
"""


# ---------------------------------------------------------------------------
# Trigger 3 — No-Options Question (solo per contesti che leggono output AI)
# ---------------------------------------------------------------------------

HAS_OPTIONS = re.compile(
    r"(\n\s*\d+[\.\)]\s|\n\s*[a-zA-Z][\.\)]\s|"        # 1. / A. / a)
    r"\n\s*[-*]\s|\bopzione\b|\bscelta\b|\balternativa\b)",
    re.IGNORECASE,
)


def check_no_options_question(text: str) -> bool:
    """True se il testo contiene '?' ma nessuna lista di opzioni."""
    if "?" not in text:
        return False
    if HAS_OPTIONS.search(text):
        return False
    return True


NO_OPTIONS_MESSAGE = """
┌─────────────────────────────────────────────────────────────────┐
│  💡  GEDI — Domanda senza opzioni rilevata                      │
├─────────────────────────────────────────────────────────────────┤
│  L'AI ha fatto una domanda senza offrire scelte concrete.        │
│  Una buona domanda ha sempre alternative pre-calcolate.          │
│                                                                   │
│  Aggiungi opzioni numerate prima di rispondere.                  │
│  (Principio G9 — Options First)                                  │
└─────────────────────────────────────────────────────────────────┘
"""
