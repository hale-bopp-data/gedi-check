---
title: "Agents Master"
tags: []
---

# AGENTS.md — easyway-gedi-check

> Package Python per enforcement guardrail GEDI: profili, trigger, proxy, notifiche n8n.
> Guardrails e regole: vedi `.cursorrules` nello stesso repo.

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

## ADO Workflow
```bash
# Tool UNICO — MAI curl inline, MAI az login
bash /c/old/easyway/ado/scripts/ado-remote.sh wi-create "titolo" "PBI" "tag1;tag2"
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-create easyway-gedi-check <src> main "AB#NNN titolo" NNN
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-autolink-wi <pr_id> easyway-gedi-check
bash /c/old/easyway/ado/scripts/ado-remote.sh pat-health-check
```
Repo ADO: `easyway-portal`, `easyway-wiki`, `easyway-agents`, `easyway-infra`, `easyway-ado`, `easyway-n8n`

## PR — Flusso standard
```bash
cd /c/old/easyway/gedi-check && git push -u origin feat/nome-descrittivo
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-create easyway-gedi-check feat/nome-descrittivo main "AB#NNN titolo" NNN
```


## Connessioni
- **PAT/secrets**: SOLO su server `/opt/easyway/.env.secrets` — MAI in locale
- **Guida**: `easyway-wiki/guides/connection-registry.md`
- **`.env.local`**: solo OPENROUTER_API_KEY e QDRANT

---
> Context Sync Engine | Master: `easyway-wiki/templates/agents-master.md`
> Override: `easyway-wiki/templates/repo-overrides.yml` | Sync: 2026-03-15T06:00:06Z
