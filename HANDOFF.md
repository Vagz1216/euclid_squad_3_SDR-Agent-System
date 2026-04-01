# Handoff for the next agent

## Personal remote (your fork)

- **GitHub:** https://github.com/Vagz1216/sdr-project  
- Local `origin` should point there (empty on GitHub until you push `main` once).

## Environment file (do not commit)

**Source** (secrets / keys already used in `agenttic_ai`):

`/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/agenttic_ai/.env`

**Target** (this SDR project):

`/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/euclid_squad_3_sales_rep/.env`

Commands (run in terminal; adjust if paths differ):

```bash
SRC="/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/agenttic_ai/.env"
DST="/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/euclid_squad_3_sales_rep/.env"
# If .env does not exist in SDR folder yet:
cp "$SRC" "$DST"
```

Then open `euclid_squad_3_sales_rep/.env.example` and add any variables that exist only in the example (SDR-specific names) into `.env` with sensible values.

- **Never** `git add .env` — this repo’s `.gitignore` already ignores `.env` (see `.gitignore`).

## Virtualenv: using `agenttic_ai` from outside that folder

### Option A (recommended): separate venv for SDR

Keeps dependencies aligned with `euclid_squad_3_sales_rep/pyproject.toml` and avoids version clashes.

```bash
cd "/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/euclid_squad_3_sales_rep"
uv sync
# then either:
uv run python scripts/seed_contacts.py
# or activate this project’s venv:
source .venv/bin/activate
```

### Option B: reuse `agenttic_ai`’s `.venv` from the SDR folder

Only if you accept that one environment must satisfy both projects’ dependencies (often fragile).

```bash
source "/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/agenttic_ai/.venv/bin/activate"
cd "/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/euclid_squad_3_sales_rep"
# Install SDR project deps into that same venv:
uv pip install -e .
# or: pip install -e .
```

After `activate`, `python` and `pip` / `uv pip` use `agenttic_ai`’s `.venv` even though your cwd is SDR.

### Option C: point `uv` at another Python (advanced)

You can run with a specific interpreter, but that environment still needs the SDR packages installed:

```bash
cd "/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/euclid_squad_3_sales_rep"
UV_PYTHON="/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/agenttic_ai/.venv/bin/python" uv sync
```

Behavior depends on `uv` version; Option A is simpler.

## If `sdr-project` is still empty on GitHub

Push once from the local squad clone (with `origin` = `sdr-project`):

```bash
cd "/media/haqs/DATA/04_Innovation_Lab/Learning/Andela AI Engineering/projects/euclid_squad_3_sales_rep"
git remote -v   # origin -> github.com/Vagz1216/sdr-project.git
git push -u origin main
```

## Short summary

- Copy `agenttic_ai/.env` → `euclid_squad_3_sales_rep/.env`, then merge any SDR-only keys from `.env.example`.
- Prefer `uv sync` + `.venv` inside SDR; only reuse `agenttic_ai`’s venv if you deliberately `source` that `.venv` and install SDR as editable.
- Personal repo: **Vagz1216/sdr-project** (https://github.com/Vagz1216/sdr-project).
