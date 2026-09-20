"""
agent/llm/router.py
Gemini-primary, Ollama-fallback LLM router.

Rules enforced here:
- LLM output is data (JSON validated against a Pydantic model), never code.
- Every call is recorded in llm_provenance.jsonl with model + tier.
- Proactive per-model RPM spacer (pro=13 s, flash=6.5 s) fires BEFORE each
  call so we stay within free-tier limits without burning budget on 429s.
  Tenacity retry on 429/5xx is kept as a second defensive layer.
- Disk cache: hash(prompt+model_name) → .cache/llm/<hash>.json
- LLM_OFFLINE=1  → serve from cache only; raise if cache miss.
- Per-run call budget enforced: hard stop when exceeded.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Literal, Type, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()

# ── configuration ────────────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_STRONG: str = os.getenv("GEMINI_MODEL_STRONG", "gemini-2.5-pro")
GEMINI_MODEL_FAST: str = os.getenv("GEMINI_MODEL_FAST", "gemini-2.5-flash")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_CACHE_DIR: Path = Path(os.getenv("LLM_CACHE_DIR", ".cache/llm"))
LLM_CALL_BUDGET: int = int(os.getenv("LLM_CALL_BUDGET", "40"))
LLM_OFFLINE: bool = os.getenv("LLM_OFFLINE", "0") == "1"

PROVENANCE_LOG = Path("llm_provenance.jsonl")

# ── per-model proactive RPM spacer ───────────────────────────────────────────
# Free-tier limits: pro=5 RPM (13 s gap), flash=10 RPM (6.5 s gap).
# We sleep BEFORE each call so budget isn't wasted on avoidable 429s.
_RPM_MIN_INTERVAL: dict[str, float] = {
    "gemini-2.5-pro": 13.0,
    "gemini-2.5-flash": 6.5,
}
_last_call_time: dict[str, float] = {}  # model_name → epoch seconds


def _rpm_wait(model: str) -> None:
    """
    Sleep long enough to respect the per-model minimum call interval.
    Keyed on the full model name so overrides via env vars work correctly.
    """
    # Resolve interval: match on substring so custom model names still work
    interval = 0.0
    for key, secs in _RPM_MIN_INTERVAL.items():
        if key in model:
            interval = secs
            break
    if interval <= 0:
        return
    now = time.monotonic()
    last = _last_call_time.get(model, 0.0)
    gap = interval - (now - last)
    if gap > 0:
        time.sleep(gap)
    _last_call_time[model] = time.monotonic()


# ── per-process call counter ─────────────────────────────────────────────────
_calls_this_run: int = 0

T = TypeVar("T", bound=BaseModel)


# ── cache helpers ─────────────────────────────────────────────────────────────
def _cache_key(prompt: str, model: str) -> str:
    raw = f"{model}::{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


def is_offline() -> bool:
    """Return True if offline mode is requested via env or module config."""
    return LLM_OFFLINE or os.getenv("LLM_OFFLINE", "0") == "1"


def _cache_path(key: str) -> Path:
    LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return LLM_CACHE_DIR / f"{key}.json"


def _read_cache(key: str) -> dict | None:
    p = _cache_path(key)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    demo_p = Path("demo_cache") / f"{key}.json"
    if demo_p.exists():
        with open(demo_p, encoding="utf-8") as f:
            return json.load(f)
    return None


def _write_cache(key: str, payload: dict) -> None:
    with open(_cache_path(key), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ── provenance log ────────────────────────────────────────────────────────────
def _log_provenance(
    model: str, cached: bool, prompt_hash: str, step_tag: str = "", tier: str = "fast"
) -> None:
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": model,   # exact model string used (e.g. gemini-2.5-pro)
        "tier": tier,     # "strong" or "fast"
        "cached": cached,
        "prompt_hash": prompt_hash,
        "step": step_tag,
    }
    with open(PROVENANCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Gemini call (with retry) ──────────────────────────────────────────────────
class _GeminiError(Exception):
    """Raised on non-retryable Gemini problems (e.g. invalid key)."""


class _RateLimitError(Exception):
    """Raised by Gemini/Ollama on 429 or transient 5xx."""


@retry(
    retry=retry_if_exception_type(_RateLimitError),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    stop=stop_after_attempt(2),
    reraise=True,
)
def _call_gemini(prompt: str, model: str) -> str:
    """Return raw JSON string from Gemini. Raises _GeminiError or _RateLimitError."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
    except ImportError as exc:
        raise _GeminiError(f"langchain-google-genai not installed: {exc}") from exc

    if not GEMINI_API_KEY:
        raise _GeminiError("GEMINI_API_KEY is not set")

    # Proactive RPM spacer — fires before the network call (tenacity retries
    # are the second layer for TPM limits or burst misses)
    _rpm_wait(model)

    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=GEMINI_API_KEY,
            temperature=LLM_TEMPERATURE,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content  # type: ignore[return-value]
    except Exception as exc:
        msg = str(exc).lower()
        if "429" in msg or "quota" in msg or "rate" in msg:
            raise _RateLimitError(str(exc)) from exc
        if "api key" in msg or "invalid" in msg or "401" in msg or "403" in msg:
            raise _GeminiError(str(exc)) from exc
        raise _RateLimitError(str(exc)) from exc  # treat unknown as retryable


@retry(
    retry=retry_if_exception_type(_RateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_ollama(prompt: str, model: str) -> str:
    """Return raw JSON string from Ollama."""
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage
    except ImportError as exc:
        raise RuntimeError(f"langchain-ollama not installed: {exc}") from exc

    try:
        llm = ChatOllama(
            model=model,
            base_url=OLLAMA_BASE_URL,
            temperature=LLM_TEMPERATURE,
            format="json",
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content  # type: ignore[return-value]
    except Exception as exc:
        msg = str(exc).lower()
        if "429" in msg or "rate" in msg:
            raise _RateLimitError(str(exc)) from exc
        raise


# ── public API ────────────────────────────────────────────────────────────────
def ask_llm(
    prompt: str,
    response_model: Type[T],
    model: str | None = None,
    step_tag: str = "",
    tier: Tier = "fast",
) -> T:
    """
    Send *prompt* to the LLM and parse the JSON response into *response_model*.

    Fallback order: Gemini (strong or fast) → Ollama.
    Cache is always checked first; cache hit skips network entirely.

    Args:
        prompt: Full prompt string.
        response_model: A Pydantic BaseModel subclass to parse the response into.
        model: Override the Gemini model name explicitly (ignores tier if set).
        step_tag: Logged in provenance (e.g. "spec", "plan", "explain").
        tier: "strong" → GEMINI_MODEL_STRONG (pro),
              "fast"   → GEMINI_MODEL_FAST (flash, default).

    Returns:
        An instance of response_model.

    Raises:
        RuntimeError: Budget exceeded or offline cache miss.
    """
    global _calls_this_run

    gemini_model = model or (GEMINI_MODEL_STRONG if tier == "strong" else GEMINI_MODEL_FAST)
    cache_key = _cache_key(prompt, gemini_model)

    # ── cache hit ───────────────────────────────────────────────────────────
    cached_payload = _read_cache(cache_key)
    if cached_payload is not None:
        _log_provenance(
            cached_payload.get("model_used", gemini_model),
            True, cache_key, step_tag, tier=tier
        )
        return response_model.model_validate(cached_payload["data"])

    # ── offline mode: cache miss → hard fail ────────────────────────────────
    if LLM_OFFLINE:
        raise RuntimeError(
            f"LLM_OFFLINE=1 but no cache entry for key {cache_key[:8]}…"
        )

    # ── budget check ────────────────────────────────────────────────────────
    if _calls_this_run >= LLM_CALL_BUDGET:
        msg = (
            f"LLM call budget exhausted ({LLM_CALL_BUDGET} calls). "
            "Increase LLM_CALL_BUDGET in .env or reduce test count."
        )
        _log_decision(msg)
        raise RuntimeError(msg)

    _calls_this_run += 1
    raw_text: str | None = None
    model_used = gemini_model

    # ── try Gemini ──────────────────────────────────────────────────────────
    try:
        raw_text = _call_gemini(prompt, gemini_model)
        model_used = gemini_model
    except (_GeminiError, _RateLimitError, Exception) as gemini_exc:
        _log_decision(
            f"Gemini call failed ({type(gemini_exc).__name__}: {gemini_exc}); "
            f"falling back to Ollama model={OLLAMA_MODEL}"
        )
        # ── fallback: Ollama ─────────────────────────────────────────────
        raw_text = _call_ollama(prompt, OLLAMA_MODEL)
        model_used = OLLAMA_MODEL

    # ── parse JSON ──────────────────────────────────────────────────────────
    data = _extract_json(raw_text)
    instance = response_model.model_validate(data)

    # ── write cache ─────────────────────────────────────────────────────────
    _write_cache(cache_key, {"model_used": model_used, "data": data})
    _log_provenance(model_used, False, cache_key, step_tag, tier=tier)

    return instance


def reset_call_counter() -> None:
    """Reset the per-run call counter (used in tests)."""
    global _calls_this_run
    _calls_this_run = 0


def get_call_count() -> int:
    return _calls_this_run


# ── helpers ───────────────────────────────────────────────────────────────────
def _extract_json(text: str) -> Any:
    """Extract the first JSON object or array from a string."""
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        inner = [l for l in lines if not l.startswith("```")]
        text = "\n".join(inner).strip()
    return json.loads(text)


def _log_decision(msg: str) -> None:
    """Append a one-line entry to .loop/DECISIONS.md."""
    decisions_path = Path(".loop/DECISIONS.md")
    if decisions_path.exists():
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(decisions_path, "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {msg}\n")
