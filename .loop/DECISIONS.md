# Decisions Log

Each line: `[timestamp] <decision> — <reason>`

---

- [2026-09-20T15:13:17+05:30] All new code placed under top-level `agent/` — `backend/agent/` and `backend/llm/` are stub scaffolding from initial repo, not part of Person C's build.
- [2026-09-20T15:13:17+05:30] Did not regenerate `contracts/*.schema.json` — they are frozen team contracts already matching the shared spec exactly.
- [2026-09-20T15:13:17+05:30] `.env.example` key renamed from `GOOGLE_API_KEY` to `GEMINI_API_KEY` — aligns to prompt spec; user confirmed.
- [2026-09-20T15:13:17+05:30] LLM_CALL_BUDGET set to 40 — conservative limit for free-tier Gemini 2.5 Pro rate limits (~60 RPM); halved to 20 per pipeline step to stay well under daily quota. (User: confirm or override in .env)
- [2026-09-20T15:13:17+05:30] Planner capped at 8 tests per 10h scope cut in prompt §3.
- [2026-09-20T15:13:17+05:30] `calib/manifest.json` never read, logged, or sent to LLM — rule §0.6 of build prompt.
- [2026-09-20T10:03:09Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T15:33:04+05:30] Added tier param to ask_llm() (strong=pro, fast=flash), proactive RPM spacer (pro=13s, flash=6.5s) before each Gemini call, and tier field in provenance log — prevents burning call budget on 429s from free-tier rate limits.
- [2026-09-20T10:07:52Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
