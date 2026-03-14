---
title: "Agents Master"
tags: []
---

# AGENTS.md — easyway-gedi-check

Istruzioni operative per agenti AI (Codex, Claude Code, Copilot Workspace, ecc.)
che lavorano in questo repository.

---

## Identita

**easyway-gedi-check** — GEDI Guardrail — Cross-tool AI Behaviour Enforcement
- Remote primario: Azure DevOps (`dev.azure.com/EasyWayData`). PR, branch, CI/CD: TUTTO su ADO.
- GitHub: mirror read-only — MAI creare PR, push o branch su GitHub.
- Branch strategy: `feat→main` (NO develop)
- Merge strategy: Merge (no fast-forward)
- Linguaggi: Python 3.9+
- **Package version**: v1.0.0
- **Install**: `pip install -e .` o `pipx install .`

---

## Comandi rapidi

```bash
# Commit con Iron Dome
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

## Struttura directory

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
- Profili in `src/gedi_check/profiles/` — dev.json, ams.json, prod.json
- Hook profiles in `hooks/{dev,ams,prod}/`
- MAI modificare profili senza consultare GEDI manifest
- Proxy mode NON blocca mai (`bypass_allowed: true`)
- Test con `pytest` — coverage minima 80%

---

## Connessioni & PAT

- Guida completa: `C:\old\easyway\wiki\guides\connection-registry.md`
- Gateway S88: PAT e secrets vivono SOLO su server `/opt/easyway/.env.secrets`
- `.env.local` locale: solo OPENROUTER/QDRANT, nessun PAT

### Comandi ADO — Ordine di preferenza OBBLIGATORIO (S107)

**MAI usare `az login` o `az boards`**. MAI creare PR con `curl` inline o quoting improvvisato.

```bash
bash /c/old/easyway/ado/scripts/ado-remote.sh wi-create "titolo" "PBI" "tag1;tag2"
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-create <repo> <src> <tgt> "titolo" [wi_id]
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-autolink-wi <pr_id> [repo]
bash /c/old/easyway/ado/scripts/ado-remote.sh wi-link-pr <wi_id> <pr_id> [repo]
bash /c/old/easyway/ado/scripts/ado-remote.sh pat-health-check
```

**Repo names ADO**: `easyway-portal`, `easyway-wiki`, `easyway-agents`, `easyway-infra`, `easyway-ado`, `easyway-n8n`

### PR creation — metodo canonico

```bash
git push -u origin feat/nome-descrittivo
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-create easyway-gedi-check feat/nome-descrittivo main "AB#NNN titolo" NNN
bash /c/old/easyway/ado/scripts/ado-remote.sh pr-autolink-wi <pr_id> easyway-gedi-check
```


---

## Regole assolute

- MAI hardcodare PAT o secrets
- MAI aprire PR senza Work Item ADO
- MAI pushare direttamente a `main`
- MAX 2 tentativi sulla stessa API call ADO, poi STOP
- Se il repo ha `develop`, le feature passano da li, non vanno a `main`
- In dubbio architetturale: consultare GEDI prima di procedere
- Ogni capability creata/modificata DEVE essere documentata in `easyway-wiki/guides/` con: **Cosa** (tabella path), **Come** (flusso/comandi), **Perché** (decisione architetturale), **Q&A**. Senza guida wiki il lavoro è incompleto. Ref: `wiki/standards/agent-architecture-standard.md` §10

---

> Generato automaticamente dal Context Sync Engine (n8n workflow `context-sync`).
> Master template: `easyway-wiki/templates/agents-master.md`
> Override: `easyway-wiki/templates/repo-overrides.yml`
> Ultima sincronizzazione: 2026-03-14T06:00:03Z
