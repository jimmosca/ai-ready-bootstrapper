"""Static fixture test (not executed by phase0; here for detection only)."""

from __future__ import annotations


def test_health_shape() -> None:
    payload = {"status": "ok"}
    assert payload["status"] == "ok"


def test_order_shape() -> None:
    order = {"id": 1, "status": "pending"}
    assert order["id"] == 1
