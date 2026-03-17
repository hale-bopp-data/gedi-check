---
title: "Agents Master"
tags: []
---

# AGENTS.md — easyway-gedi-check

> Package Python per enforcement guardrail GEDI: profili, trigger, proxy, notifiche n8n.
> Guardrails e regole: vedi `.cursorrules` nello stesso repo.
> Workspace map: vedi `factory.yml` nella root workspace (mappa completa repos, stack, deploy).

## Identità
| Campo | Valore |
|---|---|
| Cosa | Python package `gedi-check` — profili (dev/ams/prod), trigger, proxy, CLI |
| Linguaggio | Python 3.9+ |
| Branch | `feat→main` (NO develop) — PR target: `main` |
- **Package version**: v1.0.0
- **Install**: `pip install -e .` o `pipx install .`

## Comandi rapidi
```bash
ewctl commit
# Install in dev mode
pip install -e ".[dev]"
# Run tests
pytest tests/
# Show active profile
gedi-check --show-profile
# Run check
gedi-check check <file>
```

## Struttura
```text
src/gedi_check/
  __init__.py        # Package init
  __main__.py        # Entry point
  cli.py             # CLI interface
  triggers.py        # GEDI trigger rules
  profile.py         # Profile loader (dev/ams/prod)
  proxy.py           # GEDI proxy mode
  n8n_notify.py      # n8n webhook notifications
  exclusions.json    # File/path exclusions
  profiles/          # Profile JSON configs (dev, ams, prod)
hooks/               # Git hook profiles (dev, ams, prod)
deploy/              # Deployment configs
tests/               # Test suite
pyproject.toml       # Package metadata (hatchling)
```

## Regole specifiche gedi-check
| Regola | Dettaglio |
|---|---|
| Profili | in `src/gedi_check/profiles/` — `dev.json`, `ams.json`, `prod.json` |
| Hook | profiles in `hooks/{dev,ams,prod}/` |
| Manifest | MAI modificare profili senza consultare GEDI manifest |
| Proxy | mode NON blocca mai (`bypass_allowed: true`) |
| Test | `pytest` — coverage minima 80% |

## Workflow & Connessioni
| Cosa | Dove |
|---|---|
| ADO operations (WI, PR) | → vedi `easyway-wiki/guides/agents/agent-ado-operations.md` |
| PR flusso standard | → vedi `easyway-wiki/guides/polyrepo-git-workflow.md` |
| PAT/secrets/gateway | → vedi `easyway-wiki/guides/connection-registry.md` |
| Branch strategy | → vedi `easyway-wiki/guides/branch-strategy-config.md` |
| Tool unico | `bash /c/old/easyway/agents/scripts/connections/ado.sh` — MAI curl inline, MAI az login |


---
> Context Sync Engine | Master: `easyway-wiki/templates/agents-master.md`
> Override: `easyway-wiki/templates/repo-overrides.yml` | Sync: 2026-03-16T15:00:12Z
