# rag-backend

A mixed data/AI repository: a FastAPI Python backend with a **mocked** LLM
provider, a Postgres dependency via `docker-compose.yml`, and AWS infrastructure
under `infra/`.

```bash
uv sync
uv run pytest
docker compose up        # api + db
```

The LLM provider is mocked (`src/backend/llm.py`) — no real credentials or
network calls are required.
