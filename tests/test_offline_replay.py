import os
import json
import pytest
from pathlib import Path

def test_offline_replay_end_to_end():
    # 1. Setup offline replay environment vars
    os.environ["LLM_OFFLINE"] = "1"
    import agent.llm.router as _router
    _router.LLM_OFFLINE = True
    
    # 2. Build and invoke graph
    from agent.graph import build_graph
    from agent.models import AgentState
    
    spec_text = Path("tests/fixtures/sample_spec.md").read_text(encoding="utf-8")
    initial_state = AgentState(firmware_path="dummy_fw.bin", spec_text=spec_text)
    
    graph = build_graph()
    
    # Execute the offline replay with a monkeypatch to force a negative control FAIL
    import unittest.mock
    def mock_run_simulations(timelines, firmware_path):
        from agent.steps.runner import _run_mock
        traces, monitors, verdicts = _run_mock(timelines, firmware_path)
        # inject failure!
        if verdicts:
            # Recreate the first verdict as FAIL using dict parsing since fields aren't mutable natively
            v_dict = verdicts[0].model_dump()
            v_dict["result"] = "FAIL"
            v_dict["evidence"]["detail"] = "Mock patched FAIL."
            from agent.models import Verdict
            verdicts[0] = Verdict.model_validate(v_dict)
        return traces, monitors, verdicts

    with unittest.mock.patch("agent.steps.runner.run_simulations", side_effect=mock_run_simulations):
        final_dict = graph.invoke(initial_state)

    state = AgentState.model_validate(final_dict)
    
    # Assert there is no runtime error
    assert state.error is None
    
    # 3. Assert we have data from all nodes (requirements, plans, timelines, traces)
    assert len(state.requirements) == 5
    assert len(state.test_plan) > 0
    assert len(state.timelines) > 0
    assert len(state.traces) > 0

    # Ensure all plan requirements survive into the timeline and the verdict count natively matches
    expected_verdicts = 0
    for tl in state.timelines:
        plan_entry = next(p for p in state.test_plan if p.get("test_id") == tl.test_id)
        plan_reqs = plan_entry.get("requirement_ids", [])
        assert set(tl.requirement_ids) == set(plan_reqs), f"{tl.test_id} timeline missing requirements"
        expected_verdicts += len(plan_reqs)
        
    assert len(state.verdicts) == expected_verdicts, f"Expected {expected_verdicts} verdicts, got {len(state.verdicts)}"
    
    # 4. We introduced exactly one negative control test in the patch
    fails = [v for v in state.verdicts if v.result.value == "FAIL"]
    assert len(fails) > 0
    
    # Check explanations correctly ran for the failure
    for f in fails:
        assert f.test_id in state.explanations
        assert len(state.explanations[f.test_id]) > 5
    
    # 5. Asset timelines validate strictly against schema
    import jsonschema
    schema = json.loads(Path("contracts/timeline.schema.json").read_text())
    for tl in state.timelines:
        jsonschema.validate(instance=tl.model_dump(exclude_none=True), schema=schema)

def test_offline_file_outputs(tmp_path):
    # Execute through CLI emulation to ensure `out/` files correctly wrote out sandboxed
    from agent.run import main
    import sys
    
    os.environ["LLM_OFFLINE"] = "1"
    os.environ["OUT_DIR"] = str(tmp_path)
    import agent.llm.router as _router
    _router.LLM_OFFLINE = True
    
    sys.argv = ["agent.run", "dummy_fw.bin", "--spec", "tests/fixtures/sample_spec.md", "--out", str(tmp_path)]
    try:
        main()
    except SystemExit as e:
        assert getattr(e, 'code', 1) == 0 or e.code is None, "Run did not exit 0"
        
    plan = json.loads((tmp_path / "test_plan.json").read_text(encoding="utf-8"))
    tls = json.loads((tmp_path / "timelines.json").read_text(encoding="utf-8"))
    
    expected_verdicts = 0
    for p in plan:
        tid = p['test_id']
        tl = next((t for t in tls if t['test_id'] == tid), None)
        assert tl is not None, f"Missing timeline {tid}"
        assert set(p.get("requirement_ids", [])) == set(tl.get("requirement_ids", []))
