"""HTTP backend that answers questions via the (mocked) LLM provider."""

from __future__ import annotations

from fastapi import FastAPI

from .llm import LLMProvider, MockLLMProvider

app = FastAPI(title="rag-backend")
provider: LLMProvider = MockLLMProvider()


@app.post("/ask")
def ask(question: str) -> dict[str, str]:
    return {"answer": provider.complete(question)}
