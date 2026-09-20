"""
agent/steps/report.py
Render the HTML report from AgentState using Jinja2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

if TYPE_CHECKING:
    from agent.models import AgentState

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "report"
_TEMPLATE_NAME = "template.html"


def render_report(state: "AgentState") -> str:
    """Render report.html from state and return the HTML string."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(_TEMPLATE_NAME)

    # Read provenance log if it exists
    prov_entries = _read_provenance()

    html = template.render(
        firmware_path=state.firmware_path,
        requirements=state.requirements,
        timelines=state.timelines,
        verdicts=state.verdicts,
        explanations=state.explanations,
        prov_entries=prov_entries,
        has_fails=any(
            v.result.value in ("FAIL", "INCONCLUSIVE") for v in state.verdicts
        ),
    )
    return html


def _read_provenance() -> list[dict]:
    prov_path = Path("llm_provenance.jsonl")
    if not prov_path.exists():
        return []
    entries = []
    for line in prov_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries
