"""LLM provider abstraction with a deterministic mock for tests.

The mock makes no network calls, so the repo is safe for static analysis and
offline testing — there are no real API keys or endpoints here.
"""

from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str: ...


class MockLLMProvider:
    """Returns a canned, deterministic response. No external calls."""

    def complete(self, prompt: str) -> str:
        return f"stub answer for: {prompt[:40]}"
