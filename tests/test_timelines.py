import pytest
from agent.models import Requirement
from agent.steps.timelines import expand_plan_to_timelines

def test_duration_healing():
    # Construct a fake test plan dictionary directly
    plan = [
        {"test_id": "T_SMALL", "requirement_ids": ["R1"], "fault_type": "nominal"},
        {"test_id": "T_OVERSIZED", "requirement_ids": ["R1"], "fault_type": "nominal"},
    ]
    reqs = [Requirement(id="R1", description="desc", source="file", source_line=1)]
    
    # We monkeypatch `_extract_json` natively during `timelines.py` LLM call inside `expand_plan_to_timelines`
    # Instead of patching network, we patch _extract_json to return our malformed boundary timeline payloads natively
    import unittest.mock
    
    mock_payloads = [
        # Small heal: duration 100, but event at 150 (heals to 250)
        {
            "test_id": "T_SMALL",
            "requirement_ids": ["R1"],
            "duration_ms": 100,
            "events": [{"at_ms": 150, "action": "set", "channel": "ch1", "value": 1}]
        },
        # Oversized heal: duration 100, but event at 150000 (heals to 150100 > 120000 cap, so it must be completely dropped)
        {
            "test_id": "T_OVERSIZED",
            "requirement_ids": ["R1"],
            "duration_ms": 100,
            "events": [{"at_ms": 150000, "action": "set", "channel": "ch1", "value": 1}]
        }
    ]
    
    # Ensure offline mode bypasses network
    import os
    os.environ["LLM_OFFLINE"] = "1"
    
    def side_effect(key):
        # We can just return the payloads based on the cached read, wait, LLM is bypassed natively offline if cache fails, but we don't have cache.
        pass

    with unittest.mock.patch("agent.steps.timelines._extract_json", side_effect=[mock_payloads[0], mock_payloads[1], mock_payloads[1], mock_payloads[1]]), \
         unittest.mock.patch("agent.llm.router.LLM_OFFLINE", False), \
         unittest.mock.patch("agent.llm.router._call_gemini", side_effect=["RAW", "RAW", "RAW", "RAW", "RAW", "RAW"]), \
         unittest.mock.patch("agent.llm.router._read_cache", return_value=None):
        
        timelines = expand_plan_to_timelines(plan, reqs)
        
    # We expect T_SMALL to successfully output because logic heals it
    assert len(timelines) == 1
    assert timelines[0].test_id == "T_SMALL"
    assert timelines[0].duration_ms == 250  # 150 + 100 boundary margin
    
