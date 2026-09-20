# Build prompt: Person C — Agent, LLM and Report (10h build)

Give this whole file to your AI coding agent as its system/task prompt. It builds **only Person C's folders** — `contracts/` (draft + validate, not final sign-off), `agent/`, `report/`, `demo_cache/`, `.env.example`, `requirements.txt`. It does not touch Person A's (`sim/`) or Person B's (`judge/`, `calib/`, `faults/`, `eval/`) folders except to read the frozen contracts and call their mocks.

This is **Loop Engineering**, not a long instruction to follow once: the agent works in short bounded loops, keeps state on disk, and checks its own work with pass/fail commands after every step. It never marks a step done from its own judgment — only a command exit code does that.

---

## 0. Ground rules (read first, obey for the whole session)

1. **Bounded goal only.** At any moment the agent works on exactly one item from `.loop/STATE.md`. It does not jump ahead to later checkpoints "while it's at it."
2. **State lives on disk, not in the chat.** `.loop/STATE.md` (current step + status), `.loop/DECISIONS.md` (every judgment call, one line each, timestamped), `.loop/LOG.md` (what ran, what the command printed, pass/fail), `.loop/evidence/` (raw command output, saved as files). If the agent's context resets, it re-reads these three files before doing anything else.
3. **Every step ends with a command, not a claim.** "I've implemented the router" is not done. `pytest agent/llm/test_router.py -q` exiting 0 is done. If there is no command yet for a step, the agent's first job in that step is to write that command.
4. **LLM output is data, never code.** Nothing the LLM returns is `eval`'d, `exec`'d, imported, or run as a script. Timelines, requirements, monitors, explanations — all JSON, validated against the schema in `contracts/`, then handed to plain Python. If a schema validation fails twice in a row, the step fails closed (logged in `DECISIONS.md`) rather than the agent hand-patching the JSON itself.
5. **The LLM never decides pass/fail.** That's Person B's `judge.evaluate()`. Person C's code only ever *produces* things for the judge to evaluate, or *reports* what the judge already decided.
6. **The seeded-bug/mutant manifest (`calib/manifest.json`) is never read, printed, logged, or sent to the LLM.** If the agent's file search surfaces it, skip it.
7. **Don't skip the boring steps.** Demo script, README section, and the report's provenance footer are not optional polish — they're checkpoints with their own pass/fail check below.

---

## 1. Git setup — fork first, nothing lands on main directly

The repo is already cloned at `C:\Users\lenovo\Desktop\New folder\50LPA\Blackbox`, with `origin` pointing at the shared team repo. Before writing any code:

```powershell
cd "C:\Users\lenovo\Desktop\New folder\50LPA\Blackbox"
git remote -v                      # confirm origin = the shared team repo
gh repo fork --remote --remote-name personc-fork   # requires GitHub CLI, see §2
git checkout -b c/agent-llm-report
git push -u personc-fork c/agent-llm-report
```

If `gh` isn't available, fork manually on github.com, then:
```powershell
git remote add personc-fork https://github.com/<your-username>/<repo-name>.git
git checkout -b c/agent-llm-report
git push -u personc-fork c/agent-llm-report
```

Rules for the rest of the build:
- Every commit goes to `personc-fork`, branch `c/agent-llm-report`. **Never `git push origin`.**
- Commit at the end of every checkpoint in §4 below, only if that checkpoint's check passes.
- When the 10h build is done, the agent stops — it does **not** open the PR. You review and open the PR from your fork to the team repo yourself.
- If `contracts/` needs a change, the agent writes the proposed change plus a one-line reason in `.loop/DECISIONS.md` and does **not** push it — that folder needs A and B's sign-off first, which happens outside this agent session.

---

## 2. Install before the agent starts (do this yourself, ahead of time)

| Tool | Install | Check |
|---|---|---|
| Git | already have it | `git --version` |
| GitHub CLI (optional, makes forking one command) | `winget install GitHub.cli` | `gh --version` |
| Python 3.11 or 3.12 | python.org | `python --version` |
| Ollama (local fallback model) | ollama.com | `ollama --version`, then `ollama pull <model>` — pick one that supports JSON-mode output, e.g. a recent Llama or Qwen instruct model |
| A Gemini API key | Google AI Studio, free tier | put in `.env`, never commit it |

Python packages (the agent will also write this into `requirements.txt`, but install it once now so the first LLM smoke test isn't blocked on a download):
```
langgraph
langchain-core
langchain-google-genai
langchain-ollama
pydantic>=2
python-dotenv
jsonschema
tenacity
jinja2
matplotlib
pytest
rich
typer
```

`.env` (copy from `.env.example` once the agent creates it, then fill in your key):
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL_STRONG=<current Gemini free-tier model name — check Google AI Studio, don't assume>
GEMINI_MODEL_FAST=<a faster/cheaper Gemini model if the strong one is rate-limited>
OLLAMA_MODEL=<the model you pulled>
LLM_TEMPERATURE=0
LLM_CACHE_DIR=.cache/llm
LLM_CALL_BUDGET=<max LLM calls per run — the agent proposes a number in DECISIONS.md and asks you to confirm>
LLM_OFFLINE=0
```
`.gitignore` must include `.env`, `.venv/`, `.cache/`, `__pycache__/`.

---

## 3. Scope cut for 10h (vs. the original 20h Person-C plan)

Ten hours is roughly half the original budget, so cuts are structural, not just faster typing:

- **Contracts:** the agent drafts and validates schemas against the examples already given to it (below), but does not chase A/B for live sign-off — that's a message you send in the team chat in parallel. If A or B haven't confirmed by the wiring checkpoint (§4, H5), the agent keeps building against mocks and flags it in `DECISIONS.md` rather than blocking.
- **Spec extraction gold-set match:** target is "reasonable on inspection," not an exact match to B's gold set, since B may not have one ready in a compressed run. The agent still writes the comparison script so it's ready the moment B's gold set exists.
- **Planner cap:** 8 tests instead of 12, to keep LLM call volume and review time down.
- **Wokwi / second simulator:** out of scope entirely for this file — Person A owns that, if it exists at all in this cut.
- **Report:** requirements, verdicts, failure explanations, provenance footer. Plots are included only if A's trace format is ready in time; otherwise the report says plainly "plots pending A's backend" rather than faking data.

---

## 4. Checkpoints (10h, each with a disk-checkable pass/fail)

The agent updates `.loop/STATE.md` with the checkpoint name and status (`in_progress` / `done` / `blocked: <reason>`) as it moves through this table. It commits and pushes to `personc-fork` only when a row's check passes.

| Hour | Checkpoint | Build | Check (must pass to advance) |
|---|---|---|---|
| H0–0.5 | **Setup** | `requirements.txt`, `.env.example`, `.gitignore`, `.loop/` scaffold (`STATE.md`, `DECISIONS.md`, `LOG.md`, `evidence/`) | `pip install -r requirements.txt` exits 0. `.env.example` has no real secrets (`grep -E "=.+" .env.example` shows only placeholder values or the model names) |
| H0.5–2 | **LLM router smoke test** | `agent/llm/router.py`: (a) Gemini returns schema-valid JSON for a toy Pydantic model, (b) Ollama returns schema-valid JSON for the same model, (c) a deliberately wrong Gemini key makes the router fall back to Ollama and log which model answered, (d) a repeated call is served from `.cache/llm` with network disabled | `pytest agent/llm/test_router.py -q` — all 4 cases pass. `.cache/llm/` has at least one file. `DECISIONS.md` has the call-budget number and today's free-tier limits |
| H2–2.75 | **Contracts drafted** | `contracts/*.schema.json` for Timeline, Trace, Monitor, Verdict, IO map, each with one example from the shared spec | A script `contracts/validate_examples.py` runs `jsonschema` against every example | Script exits 0 for all 5 |
| H2.75–5 | **Router complete + graph skeleton + report skeleton** | Rate limiter, 429/5xx backoff, per-run call budget enforced (hard stop, not a warning), `llm_provenance.jsonl`, `LLM_OFFLINE=1` mode, `agent/graph.py` LangGraph nodes on Pydantic models, `agent/fake_agent.py`, report template rendering from canned mock data | `python -m agent.graph --mock` runs start to finish and writes `out/report.html` with no exceptions. Provenance log has one line per LLM call made during the mock run |
| H5–6 | **Spec extraction** | `agent/steps/spec.py` reads README + any strings B has exposed, outputs numbered requirements + ambiguity list to `out/requirements.json` | `jsonschema` validates `out/requirements.json`. Manual spot-check: every requirement has a threshold or time value traceable to a specific README sentence (agent writes the line number it used next to each) |
| H6–7 | **Planner + timeline compiler** | `agent/steps/plan.py`, `agent/steps/timelines.py`: requirements × fault matrix, capped at 8 tests, each with a one-line reason, batched LLM calls, run through A's lint (or a stand-in lint if A's isn't ready) before being accepted | At least 8 tests generated, all lint-clean, total LLM calls for this step ≤ half the run's call budget |
| H7–8 | **End-to-end wiring** | `agent/run.py` wired to real backend/judge if A and B have pushed theirs, otherwise to their mocks | `python -m agent.run <firmware> --spec README.md` produces a report with zero failures on the clean/original firmware, and reproduces identically when rerun with `LLM_OFFLINE=1` |
| H8–9 | **Failure explainer + report finalize** | `agent/steps/explain.py` (each FAIL gets a hypothesis citing a requirement + evidence, labelled as a hypothesis not a fact), report gets the provenance footer (which model answered each stage, what was replayed from cache) | Every FAIL verdict in the mock/real run has a non-empty explanation citing a requirement ID |
| H9–9.5 | **`demo_cache/` + demo script** | Record real Gemini responses from one full run, commit them, write `DEMO_SCRIPT.md` (two minutes, what you say while it runs) | Rerun with `LLM_OFFLINE=1` reproduces the same `out/report.html` byte-for-byte (or diff only in timestamps) |
| H9.5–10 | **Freeze + handoff note** | Agent stops making changes. Writes `.loop/HANDOFF.md`: what's done, what's stubbed, what still needs A/B, exact commands to rerun everything | `.loop/HANDOFF.md` exists and every command listed in it actually runs |

If a checkpoint is still failing when its hour ends, the agent does **not** silently extend it — it logs `blocked: <reason>` in `STATE.md`, moves to the next checkpoint's setup work that doesn't depend on the blocked piece, and surfaces the blocker to you directly rather than burying it in the log.

---

## 5. Do not (repeated because it's the part most likely to get skipped under time pressure)

- Do not let the LLM decide pass/fail — only `judge.evaluate()` does.
- Do not derive expected behaviour from what the firmware actually does — only from the spec text.
- Do not read, log, or send `calib/manifest.json` to any LLM.
- Do not hide when a result came from the fallback model or from cache — say so in the provenance footer.
- Do not commit the Gemini key, or push anything to `origin` — only `personc-fork`.
- Do not skip the demo script, the handoff note, or the provenance footer to save time — cut test count or plot polish first.
