# AGENTS.md

Guidance for agents working on `rag-backend`.

- The LLM provider is mocked; keep it that way for tests (`MockLLMProvider`).
- Backend code lives under `src/backend/`; infrastructure under `infra/`.
- Run `uv run pytest` before proposing changes. There is no CI yet.
