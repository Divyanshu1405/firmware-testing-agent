# DEMO_SCRIPT.md

## Two-minute walkthrough — Firmware Testing Agent (Person C)

### What you say / what runs

**[0:00–0:20] Setup**
> "We start with a firmware binary and a README spec. The agent reads the spec,
> extracts testable requirements, and auto-generates timed test timelines — entirely
> driven by a Gemini LLM with an Ollama fallback."

```powershell
# Show the spec
cat README.md
# Show the .env (masked) and requirements.txt
cat .env.example
```

---

**[0:20–1:00] Full offline replay**
> "The real Gemini responses are already cached in `demo_cache/`.
> Watch the agent run completely offline — no network, identical output."

```powershell
$env:LLM_OFFLINE="1"
python -m agent.run dummy_fw.bin --spec README.md
```

Point to what prints:
- `[run] LLM_OFFLINE=True`
- requirements extracted, timelines compiled, verdicts computed
- `[run] report → out/report.html`

---

**[1:00–1:30] Open the report**
> "Here's the HTML report: requirements list, verdict table (PASS/FAIL/INCONCLUSIVE),
> failure hypotheses from the LLM, and a provenance footer showing exactly which model
> answered each step — Gemini or Ollama — and whether it was a network call or cache hit."

Open `out/report.html` in browser.

---

**[1:30–2:00] Q&A cue**
> "The agent's pipeline is fully deterministic on re-run.
> All PASS/FAIL verdicts come from the Python judge — never from the LLM.
> The LLM only produces structured JSON (requirements, timelines, explanations)
> which is then validated against shared team schemas before use."

---

_Demo recording: `LLM_OFFLINE=1 python -m agent.run dummy_fw.bin --spec README.md`_
