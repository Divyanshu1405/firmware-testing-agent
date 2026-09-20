"""
agent/steps/spec.py
Reads the README/spec text, calls the LLM, and returns a list of
Requirement objects validated against requirement.schema.json.

Rules:
- LLM output is treated as data, never code.
- Each requirement must include a source_line pointing to the actual
  line number in the spec text from which it was derived.
- If schema validation fails twice in a row, the step fails closed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

import jsonschema

from agent.models import Requirement
from agent.llm.router import ask_llm

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "requirement.schema.json"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


EXTRACT_PROMPT_TEMPLATE = """\
You are analysing a firmware specification document. Extract all testable requirements.

For each requirement output a JSON object with EXACTLY these fields:
- "id": string, format "R<N>" (e.g. "R1", "R2")
- "description": string, one sentence describing the requirement
- "source": string, the filename (e.g. "README.md")
- "source_line": integer, the 1-based line number in the spec where this requirement appears
- "threshold": number or null, the numeric threshold value if present (e.g. 30.0 for "30°C")
- "time_value_ms": integer or null, any time limit in milliseconds
- "ambiguous": boolean, true if the requirement is not precisely measurable

Return ONLY a JSON array of these objects. No explanations.

SPEC TEXT (filename: {filename}):
---
{spec_text}
---
"""


def _build_numbered_spec(text: str) -> tuple[str, list[str]]:
    """Return (spec_with_line_numbers, lines_list)."""
    lines = text.splitlines()
    numbered = "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines))
    return numbered, lines


class _RequirementListWrapper(Requirement):
    """Used only for single-item parsing; bulk parsing done differently."""


from pydantic import BaseModel


class _RequirementList(BaseModel):
    items: List[Requirement]


def extract_requirements(spec_text: str, filename: str = "README.md") -> List[Requirement]:
    """
    Extract requirements from spec_text using the LLM.
    Returns validated Requirement objects.
    Fails closed after 2 consecutive validation failures.
    """
    if not spec_text.strip():
        return []

    numbered_spec, lines = _build_numbered_spec(spec_text)
    prompt = EXTRACT_PROMPT_TEMPLATE.format(
        filename=filename,
        spec_text=numbered_spec,
    )
    schema = _load_schema()

    for attempt in range(1, 3):
        try:
            # LLM returns a list, so we wrap it
            from agent.llm.router import _extract_json
            from agent.llm.router import ask_llm as _ask_llm

            # Use a wrapper model so ask_llm can parse a list
            class _Wrap(BaseModel):
                requirements: List[Requirement]

            # We call LLM directly since the response is an array, not an object
            raw_text = _call_llm_raw(prompt)
            data = _extract_json(raw_text)

            # data may be a list or {"requirements": [...]}
            if isinstance(data, list):
                raw_items = data
            elif isinstance(data, dict) and "requirements" in data:
                raw_items = data["requirements"]
            else:
                raw_items = [data]

            # Validate each item against the frozen schema
            results: List[Requirement] = []
            for item in raw_items:
                jsonschema.validate(instance=item, schema=schema)
                results.append(Requirement.model_validate(item))

            return results

        except (jsonschema.ValidationError, Exception) as exc:
            if attempt == 2:
                from agent.llm.router import _log_decision
                _log_decision(
                    f"spec extraction failed closed after 2 attempts: {exc}"
                )
                raise RuntimeError(f"Spec extraction failed after 2 attempts: {exc}") from exc
            continue

    return []  # unreachable


def _call_llm_raw(prompt: str) -> str:
    """Call the LLM and return the raw text (not parsed into a model).
    Uses tier='strong' (gemini-2.5-pro) — spec extraction is the only step
    that uses Pro, since requirement extraction benefits from higher accuracy.
    """
    from agent.llm import router as _router
    import agent.llm.router as _r

    import hashlib, time, json as _json
    from pathlib import Path as _Path

    _tier = "strong"
    _model = _r.GEMINI_MODEL_STRONG   # resolved at call time from env var

    cache_key = hashlib.sha256(
        f"{_model}::{prompt}".encode()
    ).hexdigest()

    # Check cache
    cached = _r._read_cache(cache_key)
    if cached is not None:
        _r._log_provenance(cached.get("model_used", _model), True, cache_key, "spec", tier=_tier)
        return _json.dumps(cached["data"])

    if _r.LLM_OFFLINE:
        raise RuntimeError(f"LLM_OFFLINE=1 but no cache for spec extraction (key {cache_key[:8]})")

    if _r._calls_this_run >= _r.LLM_CALL_BUDGET:
        raise RuntimeError("LLM call budget exhausted during spec extraction")

    _r._calls_this_run += 1
    raw: str | None = None
    model_used = _model

    try:
        raw = _r._call_gemini(prompt, _model)
    except Exception as exc:
        _r._log_decision(f"spec Gemini ({_model}) failed ({exc}); falling back to Ollama")
        raw = _r._call_ollama(prompt, _r.OLLAMA_MODEL)
        model_used = _r.OLLAMA_MODEL

    data = _r._extract_json(raw)
    _r._write_cache(cache_key, {"model_used": model_used, "data": data})
    _r._log_provenance(model_used, False, cache_key, "spec", tier=_tier)
    return _json.dumps(data)
