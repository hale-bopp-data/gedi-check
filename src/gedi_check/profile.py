"""
GEDI Profile System — contesti di lavoro come carte Magic.

Ogni profilo definisce le "abilità" attive del guardrail:
  dev  🟢 Esploratore  — libertà di sperimentazione, guardrail leggeri
  ams  🟡 Guardiano    — tutti i trigger, soglie standard, audit trail
  prod 🔴 Sentinella   — massima protezione, soglia minima, blocchi espliciti

Lookup order (primo match vince):
  1. GEDI_PROFILE env var (override esplicito)
  2. easyway/hooks/{profile}/gedi.profile.json (config progetto)
  3. src/gedi_check/profiles/{profile}.json (default package)
  4. Auto-detect da branch git corrente
  5. Fallback: profilo "ams" (bilanciato, sicuro per default)
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

_PACKAGE_PROFILES = Path(__file__).parent / "profiles"
_DEFAULT_PROFILE = "ams"

# Mapping branch → profilo (ordine: match esatto prima, wildcard dopo)
_BRANCH_MAP = {
    "main": "prod",
    "master": "prod",
    "production": "prod",
    "develop": "ams",
    "staging": "ams",
}
_BRANCH_PREFIX_MAP = {
    "feat/": "dev",
    "feature/": "dev",
    "chore/": "dev",
    "experiment/": "dev",
    "spike/": "dev",
    "hotfix/": "ams",
    "release/": "ams",
}


def _current_branch() -> str:
    """Ritorna il branch git corrente o stringa vuota."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _detect_from_branch(branch: str) -> str | None:
    if not branch or branch == "HEAD":
        return None
    if branch in _BRANCH_MAP:
        return _BRANCH_MAP[branch]
    for prefix, profile in _BRANCH_PREFIX_MAP.items():
        if branch.startswith(prefix):
            return profile
    return None


def _find_project_profile(name: str) -> Path | None:
    """Cerca gedi.profile.json nella directory hooks/{name}/ risalendo l'albero."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / "hooks" / name / "gedi.profile.json"
        if candidate.exists():
            return candidate
        # Stop quando troviamo la root del repo
        if (parent / ".git").exists():
            break
    return None


def resolve_profile_name() -> str:
    """Determina il profilo attivo. Ritorna: dev | ams | prod."""
    # 1. Override esplicito
    explicit = os.environ.get("GEDI_PROFILE", "").strip().lower()
    if explicit in ("dev", "ams", "prod"):
        return explicit

    # 2. Auto-detect da branch
    branch = _current_branch()
    from_branch = _detect_from_branch(branch)
    if from_branch:
        return from_branch

    # 3. Fallback sicuro
    return _DEFAULT_PROFILE


def load_profile(name: str | None = None) -> dict[str, Any]:
    """
    Carica il profilo GEDI attivo.
    Lookup: project hooks/ → package profiles/ → defaults hardcoded.
    """
    if name is None:
        name = resolve_profile_name()

    # Project-level override
    project_path = _find_project_profile(name)
    if project_path:
        try:
            return json.loads(project_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Package defaults
    pkg_path = _PACKAGE_PROFILES / f"{name}.json"
    if pkg_path.exists():
        try:
            return json.loads(pkg_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Hardcoded fallback (ams bilanciato)
    return _hardcoded_ams()


def get_trigger_config(profile: dict[str, Any], trigger_name: str) -> dict[str, Any]:
    """Ritorna la config di un trigger specifico dal profilo."""
    return profile.get("triggers", {}).get(trigger_name, {
        "enabled": True,
        "mode": "advisory",
        "notify_n8n": False,
        "threshold": 3,
    })


def is_trigger_enabled(profile: dict[str, Any], trigger_name: str) -> bool:
    return get_trigger_config(profile, trigger_name).get("enabled", True)


def get_threshold(profile: dict[str, Any], trigger_name: str = "error_repeat") -> int:
    return get_trigger_config(profile, trigger_name).get("threshold", 3)


def get_mode(profile: dict[str, Any], trigger_name: str) -> str:
    """Ritorna: 'advisory' | 'block'"""
    return get_trigger_config(profile, trigger_name).get("mode", "advisory")


def profile_banner(profile: dict[str, Any]) -> str:
    meta = profile.get("_meta", {})
    name = meta.get("profile", "?").upper()
    card = meta.get("card", "")
    desc = meta.get("description", "")
    return f"[GEDI {card} {name}] {desc}"


def _hardcoded_ams() -> dict[str, Any]:
    return {
        "_meta": {"profile": "ams", "card": "🟡 Guardiano"},
        "triggers": {
            "fix_keyword": {"enabled": True, "mode": "advisory", "notify_n8n": True},
            "error_repeat": {"enabled": True, "threshold": 3, "mode": "block"},
            "no_options_question": {"enabled": True, "mode": "advisory"},
        },
    }
