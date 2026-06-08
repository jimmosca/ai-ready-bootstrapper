# orders-api

A small FastAPI service that exposes an orders endpoint.

## Develop

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
```

Container image is built from the included `Dockerfile`; CI runs in GitHub
Actions (`.github/workflows/ci.yml`).
