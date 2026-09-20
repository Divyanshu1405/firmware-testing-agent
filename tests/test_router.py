"""
agent/llm/test_router.py
Four-case smoke test for the LLM router.

Case a: Gemini returns schema-valid JSON for a toy Pydantic model.
Case b: Ollama returns schema-valid JSON for the same model.
Case c: Bad Gemini key → router falls back to Ollama, logs which model answered.
Case d: Repeated call is served from .cache/llm/ with network disabled (LLM_OFFLINE=1).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

# Ensure project root is on path for dotenv
os.environ.setdefault("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "test-placeholder"))
os.environ.setdefault("OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct"))


# ── Toy model ─────────────────────────────────────────────────────────────────
class Greeting(BaseModel):
    message: str
    value: int


PROMPT = "Reply with a JSON object: {\"message\": \"hello\", \"value\": 42}"
EXPECTED = Greeting(message="hello", value=42)
FAKE_RESPONSE_TEXT = json.dumps({"message": "hello", "value": 42})


# ── helpers ───────────────────────────────────────────────────────────────────
def _make_mock_llm_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.content = text
    return resp


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Each test gets its own cache dir and a fresh call counter."""
    cache_dir = tmp_path / "llm_cache"
    cache_dir.mkdir()
    monkeypatch.setenv("LLM_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("LLM_OFFLINE", "0")
    monkeypatch.setenv("LLM_CALL_BUDGET", "40")

    import agent.llm.router as router
    monkeypatch.setattr(router, "LLM_CACHE_DIR", cache_dir)
    monkeypatch.setattr(router, "LLM_OFFLINE", False)
    monkeypatch.setattr(router, "LLM_CALL_BUDGET", 40)
    router.reset_call_counter()

    # Redirect provenance log to tmp
    prov = tmp_path / "llm_provenance.jsonl"
    monkeypatch.setattr(router, "PROVENANCE_LOG", prov)
    yield cache_dir


# ── Case a: Gemini returns valid JSON ─────────────────────────────────────────
def test_case_a_gemini_returns_valid_json(monkeypatch):
    """Gemini call → valid Greeting instance, cache file written."""
    import agent.llm.router as router

    mock_chat = MagicMock(return_value=_make_mock_llm_response(FAKE_RESPONSE_TEXT))

    with patch("agent.llm.router._call_gemini", return_value=FAKE_RESPONSE_TEXT):
        result = router.ask_llm(PROMPT, Greeting, step_tag="case_a")

    assert result.message == "hello"
    assert result.value == 42
    # Cache must have been written
    assert any(router.LLM_CACHE_DIR.iterdir()), "Cache file must exist after Gemini call"


# ── Case b: Ollama returns valid JSON ─────────────────────────────────────────
def test_case_b_ollama_returns_valid_json(monkeypatch):
    """Ollama call → valid Greeting instance."""
    import agent.llm.router as router

    with patch("agent.llm.router._call_ollama", return_value=FAKE_RESPONSE_TEXT) as mock_ollama, \
         patch("agent.llm.router._call_gemini", side_effect=router._GeminiError("forced")):
        result = router.ask_llm(PROMPT, Greeting, step_tag="case_b")
        mock_ollama.assert_called_once()

    assert result.message == "hello"
    assert result.value == 42


# ── Case c: Bad Gemini key → fallback to Ollama, logged ──────────────────────
def test_case_c_bad_gemini_key_falls_back_to_ollama(tmp_path, monkeypatch):
    """Wrong Gemini key causes _GeminiError; router falls back to Ollama and logs it."""
    import agent.llm.router as router

    decisions_path = tmp_path / ".loop" / "DECISIONS.md"
    decisions_path.parent.mkdir(parents=True)
    decisions_path.write_text("# Decisions\n")
    monkeypatch.chdir(tmp_path)

    # Copy the cache dir env is already isolated by fixture
    (tmp_path / ".loop").mkdir(exist_ok=True)
    decisions_path.write_text("# Decisions\n")

    with patch("agent.llm.router._call_gemini", side_effect=router._GeminiError("API key invalid")), \
         patch("agent.llm.router._call_ollama", return_value=FAKE_RESPONSE_TEXT):
        result = router.ask_llm(PROMPT, Greeting, step_tag="case_c")

    assert result.value == 42

    # Provenance log should show the ollama model was used (not gemini)
    prov_log = router.PROVENANCE_LOG
    assert prov_log.exists(), "Provenance log must exist"
    entries = [json.loads(l) for l in prov_log.read_text().strip().splitlines()]
    assert any(router.OLLAMA_MODEL in e["model"] for e in entries), \
        "Provenance log must record the fallback Ollama model"


# ── Case d: Repeated call served from cache (network disabled) ────────────────
def test_case_d_cache_replay_with_offline_mode(monkeypatch):
    """
    First call populates cache.
    Second call with LLM_OFFLINE=1 must be served from cache without any network call.
    """
    import agent.llm.router as router

    gemini_call_count = {"n": 0}

    def counting_gemini(prompt, model):
        gemini_call_count["n"] += 1
        return FAKE_RESPONSE_TEXT

    with patch("agent.llm.router._call_gemini", side_effect=counting_gemini):
        r1 = router.ask_llm(PROMPT, Greeting, step_tag="case_d_warm")

    assert gemini_call_count["n"] == 1
    assert any(router.LLM_CACHE_DIR.iterdir()), "Cache must be populated after first call"

    # Now go offline
    monkeypatch.setattr(router, "LLM_OFFLINE", True)
    router.reset_call_counter()

    with patch("agent.llm.router._call_gemini", side_effect=AssertionError("Should not be called in offline mode")), \
         patch("agent.llm.router._call_ollama", side_effect=AssertionError("Should not be called in offline mode")):
        r2 = router.ask_llm(PROMPT, Greeting, step_tag="case_d_replay")

    assert r2.message == r1.message
    assert r2.value == r1.value
    assert gemini_call_count["n"] == 1, "Gemini must not be called again — served from cache"
