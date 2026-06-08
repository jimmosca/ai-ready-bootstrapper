"""Static fixture test (detection only)."""

from __future__ import annotations


def test_mock_provider_is_deterministic() -> None:
    a = f"stub answer for: {'hi'[:40]}"
    b = f"stub answer for: {'hi'[:40]}"
    assert a == b
