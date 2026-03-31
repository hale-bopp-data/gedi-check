"""
gedi-proxy — Transparent HTTP proxy with GEDI trigger detection.

Intercepts AI streaming responses (SSE/chunked) BEFORE they reach the tool.
Detects trigger words in real-time, notifies desktop + n8n async.
Never blocks the response — pure pass-through.

Usage:
  gedi-proxy [--port 8765] [--upstream https://api.anthropic.com]

Tool configuration (set once):
  ANTHROPIC_BASE_URL=http://localhost:8765   (Claude Code, Claude SDK)
  OPENAI_API_BASE=http://localhost:8765      (Cursor, Codex, Windsurf)

Principle G19 (Invisible Shield): when it works, nobody notices.
"""

from __future__ import annotations

import argparse
import http.server
import os
import subprocess
import threading
import urllib.error
import urllib.request

from gedi_check.triggers import FIX_KEYWORDS

_seen_triggers: set[str] = set()
_seen_lock = threading.Lock()


def _notify(keyword: str, snippet: str) -> None:
    """Desktop toast (Windows) + gedi-check async."""
    try:
        msg = f"GEDI: trigger '{keyword}' — Hai chiesto consiglio a GEDI?"
        subprocess.Popen(
            [
                "powershell", "-WindowStyle", "Hidden", "-Command",
                "[System.Reflection.Assembly]::LoadWithPartialName"
                "('System.Windows.Forms') | Out-Null; "
                f"[System.Windows.Forms.MessageBox]::Show('{msg}','GEDI Guardrail',"
                f"[System.Windows.Forms.MessageBoxButtons]::OK,"
                f"[System.Windows.Forms.MessageBoxIcon]::Warning)",
            ],
            creationflags=0x00000008,
        )
    except Exception:
        pass


def _scan_chunk(chunk: bytes) -> None:
    text = chunk.decode("utf-8", errors="replace")
    m = FIX_KEYWORDS.search(text)
    if not m:
        return
    keyword = m.group(0).lower()
    with _seen_lock:
        if keyword in _seen_triggers:
            return
        _seen_triggers.add(keyword)
    threading.Thread(target=_notify, args=(keyword, text[:300]), daemon=True).start()


class GEDIProxyHandler(http.server.BaseHTTPRequestHandler):
    upstream: str = "https://api.anthropic.com"

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        pass  # Invisible Shield

    def do_POST(self) -> None:
        self._forward()

    def do_GET(self) -> None:
        self._forward()

    def do_OPTIONS(self) -> None:
        self._forward()

    def _forward(self) -> None:
        url = self.upstream.rstrip("/") + self.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else None
        skip = {"host", "transfer-encoding", "connection"}
        headers = {k: v for k, v in self.headers.items() if k.lower() not in skip}

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=self.command)
            resp = urllib.request.urlopen(req, timeout=120)
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                if k.lower() not in {"transfer-encoding", "connection"}:
                    self.send_header(k, v)
            self.end_headers()
            while chunk := resp.read(4096):
                _scan_chunk(chunk)
                self.wfile.write(chunk)
                self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in {"transfer-encoding", "connection"}:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as ex:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"gedi-proxy error: {ex}".encode())


def main() -> None:
    parser = argparse.ArgumentParser(description="gedi-proxy — GEDI streaming interceptor")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--upstream",
        default=os.environ.get("GEDI_UPSTREAM", "https://api.anthropic.com"),
    )
    args = parser.parse_args()

    GEDIProxyHandler.upstream = args.upstream
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), GEDIProxyHandler)

    print(f"gedi-proxy {_version()} listening on http://127.0.0.1:{args.port}")
    print(f"  upstream : {args.upstream}")
    print(f"  Claude   : ANTHROPIC_BASE_URL=http://127.0.0.1:{args.port}")
    print(f"  OpenAI   : OPENAI_API_BASE=http://127.0.0.1:{args.port}")
    print("Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\ngedi-proxy stopped.")


def _version() -> str:
    try:
        from gedi_check import __version__
        return __version__
    except Exception:
        return "dev"


if __name__ == "__main__":
    main()
