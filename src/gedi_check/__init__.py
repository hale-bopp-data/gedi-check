"""
gedi-check — GEDI guardrail cross-tool e cross-environment.

Enforces GEDI principles (fix keyword, error repeat, no-options question)
independently of which AI tool, IDE or agent is running.

Part of the EasyWay platform — https://easyway.it
GEDI: Guardian EasyWay Delle Intenzioni
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gedi-check")
except PackageNotFoundError:
    __version__ = "dev"

__all__ = ["__version__"]
