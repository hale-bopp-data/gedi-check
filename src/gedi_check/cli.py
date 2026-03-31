"""
gedi-check CLI entry point.

Usage:
  gedi-check --trigger fix    --message "fix: workaround per timeout"
  gedi-check --trigger commit --diff "$(git diff --cached)"
  gedi-check --trigger error  --code 127 --stderr "curl: not found"
  gedi-check --trigger stop   --message "<last_assistant_message>"

Exit 0 = ok / advisory shown
Exit 1 = hard block (error-repeat trigger only)
Exit 0 always on fallback — never blocks for service unavailability
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from gedi_check import __version__, n8n_notify, triggers
from gedi_check.profile import (
    get_mode,
    get_threshold,
    is_trigger_enabled,
    load_profile,
    profile_banner,
)


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_fix(args: argparse.Namespace) -> int:
    """Trigger 1 — Fix Keyword. Mode depends on active profile."""
    profile = load_profile(getattr(args, "profile", None))
    if not is_trigger_enabled(profile, "fix_keyword"):
        return 0

    text = " ".join(filter(None, [args.message or "", args.diff or ""]))
    found, keyword = triggers.check_fix_keyword(text)
    if not found:
        return 0

    mode = get_mode(profile, "fix_keyword")
    notify = profile.get("triggers", {}).get("fix_keyword", {}).get("notify_n8n", False)

    _stderr(triggers.OODA_MESSAGE.format(keyword=keyword))
    _stderr(f"  Profilo attivo: {profile_banner(profile)}")

    if notify:
        n8n_notify.notify_async(
            "fix_keyword",
            {
                "keyword": keyword,
                "profile": profile.get("_meta", {}).get("profile"),
                "message_snippet": (args.message or "")[:300],
            },
        )
    # prod: block. dev/ams: advisory
    return 1 if mode == "block" else 0


def handle_commit(args: argparse.Namespace) -> int:
    return handle_fix(args)


def handle_error(args: argparse.Namespace) -> int:
    """Trigger 2 — Error Repeat. Threshold from active profile."""
    profile = load_profile(getattr(args, "profile", None))
    if not is_trigger_enabled(profile, "error_repeat"):
        return 0

    code = args.code or 1
    threshold = get_threshold(profile, "error_repeat")
    should_block, count = triggers.record_error(code, args.stderr or "", threshold=threshold)

    if should_block:
        _stderr(
            triggers.ERROR_BLOCK_MESSAGE.format(
                code=code,
                count=count,
                session=os.environ.get("GEDI_SESSION", str(os.getpid())),
                log_file=str(triggers.ERROR_FILE),
            )
        )
        _stderr(f"  Profilo attivo: {profile_banner(profile)}")
        n8n_notify.notify_async(
            "error_repeat",
            {"exit_code": code, "count": count, "threshold": threshold},
        )
        time.sleep(0.1)
        return 1
    return 0


def handle_stop(args: argparse.Namespace) -> int:
    """Trigger for Claude Code Stop hook."""
    profile = load_profile(getattr(args, "profile", None))
    text = args.message or ""

    fix_found, keyword = (
        triggers.check_fix_keyword(text)
        if is_trigger_enabled(profile, "fix_keyword") else (False, "")
    )
    no_opts = (
        triggers.check_no_options_question(text)
        if is_trigger_enabled(profile, "no_options_question") else False
    )

    if fix_found:
        _stderr(triggers.OODA_MESSAGE.format(keyword=keyword))
        n8n_notify.notify_async("stop_fix_keyword", {"keyword": keyword})
    if no_opts:
        _stderr(triggers.NO_OPTIONS_MESSAGE)
        n8n_notify.notify_async("stop_no_options", {"snippet": text[:300]})
    return 1 if (fix_found or no_opts) else 0


HANDLERS = {
    "fix": handle_fix,
    "commit": handle_commit,
    "error": handle_error,
    "stop": handle_stop,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gedi-check",
        description="GEDI guardrail — cross-tool AI behaviour enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version=f"gedi-check {__version__}")
    parser.add_argument("--trigger", choices=list(HANDLERS))
    parser.add_argument("--message", help="Commit message or AI output")
    parser.add_argument("--diff", help="git diff --cached output")
    parser.add_argument("--code", type=int, help="Exit code (for --trigger error)")
    parser.add_argument("--stderr", help="Stderr snippet (for --trigger error)")
    parser.add_argument(
        "--profile", choices=["dev", "ams", "prod"], default=None,
        help="Profilo GEDI (default: auto-detect da branch / GEDI_PROFILE env)",
    )
    parser.add_argument(
        "--show-profile", action="store_true",
        help="Mostra profilo attivo, abilità e filosofia della carta",
    )

    args = parser.parse_args()

    if args.show_profile:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        from gedi_check.profile import load_profile, resolve_profile_name
        name = args.profile or resolve_profile_name()
        p = load_profile(name)
        meta = p.get("_meta", {})
        print(f"\n{meta.get('card', '')}  Profilo: {name.upper()}")
        print(f"  {meta.get('description', '')}")
        print(f"\n  Filosofia: {meta.get('philosophy', '')}")
        print("\n  Trigger:")
        for t, cfg in p.get("triggers", {}).items():
            stato = "✅" if cfg.get("enabled") else "❌"
            mode = cfg.get("mode", "advisory")
            thr = f" soglia:{cfg['threshold']}x" if "threshold" in cfg else ""
            notify = " 📡n8n" if cfg.get("notify_n8n") else ""
            print(f"    {stato} {t}: {mode}{thr}{notify}")
        abilities = p.get("abilities", [])
        if abilities:
            print(f"\n  Abilità: {', '.join(abilities)}")
        print()
        return 0

    if not args.trigger:
        parser.error("--trigger è obbligatorio (o usa --show-profile / --version)")

    try:
        return HANDLERS[args.trigger](args)
    except Exception:
        return 0  # graceful degradation


if __name__ == "__main__":
    sys.exit(main())
