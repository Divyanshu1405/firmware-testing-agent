"""
agent/steps/timelines.py
Stand-in lint pass for generated timelines.
Rules:
  - at_ms values must be within [0, duration_ms]
  - events must be in chronological order
  - at least one event per timeline
  - action values must be from the allowed enum
If Person A's lint is available at sim.lint, delegate to it.
"""

from __future__ import annotations

from typing import List

from agent.models import Timeline, TimelineAction
from agent.llm.router import _log_decision


ALLOWED_ACTIONS = {a.value for a in TimelineAction}


def lint_timelines(timelines: List[Timeline]) -> List[Timeline]:
    """
    Run stand-in lint on each timeline.
    Timelines that fail are dropped and logged to DECISIONS.md.
    Returns only lint-clean timelines.
    """
    # Try to delegate to Person A's lint if available
    try:
        from sim.lint import validate_timeline  # type: ignore
        _use_sim_lint = True
    except ImportError:
        _use_sim_lint = False

    clean: List[Timeline] = []
    for tl in timelines:
        if _use_sim_lint:
            try:
                validate_timeline(tl.model_dump())
                clean.append(tl)
            except Exception as exc:
                _log_decision(
                    f"timeline {tl.test_id} rejected by sim.lint: {exc}"
                )
        else:
            errors = _standin_lint(tl)
            if errors:
                _log_decision(
                    f"timeline {tl.test_id} rejected by stand-in lint: {'; '.join(errors)}"
                )
            else:
                clean.append(tl)

    return clean


def _standin_lint(tl: Timeline) -> list[str]:
    """Return a list of lint error strings, empty if clean."""
    errors: list[str] = []

    if not tl.events:
        errors.append("no events defined")
        return errors

    prev_ms = -1
    for ev in tl.events:
        if ev.at_ms > tl.duration_ms:
            errors.append(
                f"event at {ev.at_ms} ms exceeds duration_ms {tl.duration_ms}"
            )
        if ev.at_ms < prev_ms:
            errors.append(
                f"events not chronological: {ev.at_ms} after {prev_ms}"
            )
        if ev.action.value not in ALLOWED_ACTIONS:
            errors.append(f"unknown action '{ev.action}'")
        prev_ms = ev.at_ms

    return errors
