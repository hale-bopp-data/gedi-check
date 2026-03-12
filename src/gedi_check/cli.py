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

from gedi_check import __version__
from gedi_check import triggers, n8n_notify


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_fix(args: argparse.Namespace) -> int:
    """Trigger 1 — Fix Keyword. Advisory, never blocks."""
    text = " ".join(filter(None, [args.message or "", args.diff or ""]))
    found, keyword = triggers.check_fix_keyword(text)
    if found:
        _stderr(triggers.OODA_MESSAGE.format(keyword=keyword))
        n8n_notify.notify_async(
            "fix_keyword",
            {"keyword": keyword, "message_snippet": (args.message or "")[:300]},
        )
    return 0


def handle_commit(args: argparse.Namespace) -> int:
    return handle_fix(args)


def handle_error(args: argparse.Namespace) -> int:
    """Trigger 2 — Error Repeat. Blocks (exit 1) at 3rd repetition."""
    code = args.code or 1
    should_block, count = triggers.record_error(code, args.stderr or "")
    if should_block:
        _stderr(
            triggers.ERROR_BLOCK_MESSAGE.format(
                code=code,
                count=count,
                session=os.environ.get("GEDI_SESSION", str(os.getpid())),
                log_file=str(triggers.ERROR_FILE),
            )
        )
        n8n_notify.notify_async("error_repeat", {"exit_code": code, "count": count})
        time.sleep(0.1)
        return 1
    return 0


def handle_stop(args: argparse.Namespace) -> int:
    """Trigger for Claude Code Stop hook."""
    text = args.message or ""
    fix_found, keyword = triggers.check_fix_keyword(text)
    no_opts = triggers.check_no_options_question(text)
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
    parser.add_argument("--trigger", choices=list(HANDLERS), required=True)
    parser.add_argument("--message", help="Commit message or AI output")
    parser.add_argument("--diff", help="git diff --cached output")
    parser.add_argument("--code", type=int, help="Exit code (for --trigger error)")
    parser.add_argument("--stderr", help="Stderr snippet (for --trigger error)")

    args = parser.parse_args()
    try:
        return HANDLERS[args.trigger](args)
    except Exception:
        return 0  # graceful degradation


if __name__ == "__main__":
    sys.exit(main())
