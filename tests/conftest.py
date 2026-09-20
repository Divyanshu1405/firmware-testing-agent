import os
import pytest

@pytest.fixture(autouse=True)
def force_offline_mode(monkeypatch):
    """Ensure no test can reach the real network by default, preventing unexpected hangs."""
    monkeypatch.setenv("LLM_OFFLINE", "1")
