"""
agent/steps/explain.py
Produce one hypothesis per FAIL verdict.
Rules:
- Each hypothesis is explicitly labelled as a hypothesis, not a fact.
- The hypothesis must cite a requirement ID and a specific evidence excerpt.
- LLM output is treated as text data — never eval'd.
- Fails closed if LLM output is empty after 2 attempts.
"""

from __future__ import annotations

from typing import List

from agent.models import Requirement, Trace, Verdict, VerdictResult
from agent.llm.router import _log_decision
import agent.llm.router as _router

EXPLAIN_PROMPT_TEMPLATE = """\
A firmware test produced a FAIL verdict. Provide a one-paragraph hypothesis
explaining the likely cause. The hypothesis must:
1. Be explicitly labelled as a hypothesis (not a fact).
2. Cite requirement {req_id}: "{req_desc}"
3. Reference the evidence: {evidence_detail} at t={evidence_t_ms} ms.
4. Consider the trace samples showing the state around this time:
{trace_samples}
5. Consider the relevant requirement source code (from {source}:{source_line}).
6. Suggest what aspect of the firmware code might be responsible.

Return ONLY plain text (no JSON, no markdown formatting).
"""


def explain_failures(
    verdicts: List[Verdict],
    requirements: List[Requirement],
    traces: List[Trace],
) -> dict[str, str]:
    """
    Return a dict mapping test_id → explanation string for each FAIL verdict.
    INCONCLUSIVE verdicts also get an explanation.
    """
    req_map = {r.id: r for r in requirements}
    explanations: dict[str, str] = {}

    fail_verdicts = [
        v for v in verdicts
        if v.result in (VerdictResult.FAIL, VerdictResult.INCONCLUSIVE)
    ]

    for verdict in fail_verdicts:
        req = req_map.get(verdict.requirement_id)
        req_desc = req.description if req else "(requirement not found)"
        
        trace = next((t for t in traces if t.test_id == verdict.test_id), None)
        trace_str = "No trace available."
        if trace:
            import json
            trace_str = json.dumps([s.model_dump() for s in trace.samples], indent=2)

        prompt = EXPLAIN_PROMPT_TEMPLATE.format(
            req_id=verdict.requirement_id,
            req_desc=req_desc,
            evidence_detail=verdict.evidence.detail,
            evidence_t_ms=verdict.evidence.t_ms,
            trace_samples=trace_str,
            source=req.source if req else "N/A",
            source_line=req.source_line if req else 0,
        )

        explanation = ""
        for attempt in range(1, 3):
            try:
                explanation = _call_explain_llm(prompt, verdict.test_id)
                if explanation.strip():
                    break
            except Exception as exc:
                if attempt == 2:
                    _log_decision(
                        f"explain: {verdict.test_id} failed after 2 attempts: {exc}; "
                        "leaving explanation as stub"
                    )
                    explanation = (
                        f"[HYPOTHESIS — automated] Could not generate explanation "
                        f"for {verdict.test_id} / {verdict.requirement_id}: {exc}"
                    )

        if not explanation.strip():
            explanation = (
                f"[HYPOTHESIS — automated] LLM returned empty explanation "
                f"for {verdict.test_id}. Evidence: {verdict.evidence.detail}"
            )

        explanations[verdict.test_id] = explanation

    return explanations


def _call_explain_llm(prompt: str, test_id: str) -> str:
    """Returns raw text explanation from LLM (not JSON). Uses tier='fast'."""
    import hashlib, json as _json

    _tier = "fast"
    _model = _router.GEMINI_MODEL_FAST

    cache_key = hashlib.sha256(
        f"{_model}::{prompt}".encode()
    ).hexdigest()

    cached = _router._read_cache(cache_key)
    if cached is not None:
        _router._log_provenance(
            cached.get("model_used", _model), True, cache_key,
            f"explain:{test_id}", tier=_tier
        )
        return cached["data"].get("text", "")

    if _router.LLM_OFFLINE:
        raise RuntimeError(f"LLM_OFFLINE=1 but no cache for explanation {test_id}")

    if _router._calls_this_run >= _router.LLM_CALL_BUDGET:
        raise RuntimeError("LLM call budget exhausted during explanation")

    _router._calls_this_run += 1
    model_used = _model
    raw: str | None = None

    try:
        raw = _router._call_gemini(prompt, _model)
    except Exception as exc:
        _log_decision(f"explain Gemini ({_model}) failed ({exc}); falling back to Ollama")
        raw = _router._call_ollama(prompt, _router.OLLAMA_MODEL)
        model_used = _router.OLLAMA_MODEL

    _router._write_cache(cache_key, {"model_used": model_used, "data": {"text": raw}})
    _router._log_provenance(model_used, False, cache_key, f"explain:{test_id}", tier=_tier)
    return raw
