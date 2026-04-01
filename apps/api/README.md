# API app (FastAPI)

Run the API locally:

```bash
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r apps/api/requirements.txt
uvicorn apps.api.main:app --reload --port 8000
```

Endpoints:

- `GET /health` — health check
- `GET /openai/functions` — list OpenAI-compatible function specs
- `POST /tools/<tool>` — call a tool; body: `{ "params": { ... } }`
