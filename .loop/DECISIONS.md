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
- [2026-09-20T10:35:56Z] spec Gemini (gemini-2.5-pro) failed (langchain-google-genai not installed: No module named 'langchain_google_genai'); falling back to Ollama
- [2026-09-20T10:35:56Z] spec Gemini (gemini-2.5-pro) failed (langchain-google-genai not installed: No module named 'langchain_google_genai'); falling back to Ollama
- [2026-09-20T10:35:56Z] spec extraction failed closed after 2 attempts: langchain-ollama not installed: No module named 'langchain_ollama'
- [2026-09-20T10:46:12Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T10:47:31Z] spec extraction failed closed after 2 attempts: 'id' is a required property

Failed validating 'required' in schema:
    {'$schema': 'http://json-schema.org/draft-07/schema#',
     '$id': 'requirement.schema.json',
     'title': 'Requirement',
     'type': 'object',
     'required': ['id', 'description', 'source', 'source_line'],
     'additionalProperties': False,
     'properties': {'id': {'type': 'string'},
                    'description': {'type': 'string'},
                    'source': {'type': 'string'},
                    'source_line': {'type': 'integer', 'minimum': 1},
                    'threshold': {'type': ['number', 'null']},
                    'time_value_ms': {'type': ['integer', 'null']},
                    'ambiguous': {'type': 'boolean'}}}

On instance:
    {}
- [2026-09-20T10:50:46Z] spec extraction failed closed after 2 attempts: 'id' is a required property

Failed validating 'required' in schema:
    {'$schema': 'http://json-schema.org/draft-07/schema#',
     '$id': 'requirement.schema.json',
     'title': 'Requirement',
     'type': 'object',
     'required': ['id', 'description', 'source', 'source_line'],
     'additionalProperties': False,
     'properties': {'id': {'type': 'string'},
                    'description': {'type': 'string'},
                    'source': {'type': 'string'},
                    'source_line': {'type': 'integer', 'minimum': 1},
                    'threshold': {'type': ['number', 'null']},
                    'time_value_ms': {'type': ['integer', 'null']},
                    'ambiguous': {'type': 'boolean'}}}

On instance:
    {}
- [2026-09-20T10:52:29Z] spec extraction failed closed after 2 attempts: 'id' is a required property

Failed validating 'required' in schema:
    {'$schema': 'http://json-schema.org/draft-07/schema#',
     '$id': 'requirement.schema.json',
     'title': 'Requirement',
     'type': 'object',
     'required': ['id', 'description', 'source', 'source_line'],
     'additionalProperties': False,
     'properties': {'id': {'type': 'string'},
                    'description': {'type': 'string'},
                    'source': {'type': 'string'},
                    'source_line': {'type': 'integer', 'minimum': 1},
                    'threshold': {'type': ['number', 'null']},
                    'time_value_ms': {'type': ['integer', 'null']},
                    'ambiguous': {'type': 'boolean'}}}

On instance:
    {}
- [2026-09-20T10:53:11Z] spec extraction failed closed after 2 attempts: 'id' is a required property

Failed validating 'required' in schema:
    {'$schema': 'http://json-schema.org/draft-07/schema#',
     '$id': 'requirement.schema.json',
     'title': 'Requirement',
     'type': 'object',
     'required': ['id', 'description', 'source', 'source_line'],
     'additionalProperties': False,
     'properties': {'id': {'type': 'string'},
                    'description': {'type': 'string'},
                    'source': {'type': 'string'},
                    'source_line': {'type': 'integer', 'minimum': 1},
                    'threshold': {'type': ['number', 'null']},
                    'time_value_ms': {'type': ['integer', 'null']},
                    'ambiguous': {'type': 'boolean'}}}

On instance:
    {}
- [2026-09-20T10:56:39Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T10:58:04Z] spec extraction failed closed after 2 attempts: 'id' is a required property

Failed validating 'required' in schema:
    {'$schema': 'http://json-schema.org/draft-07/schema#',
     '$id': 'requirement.schema.json',
     'title': 'Requirement',
     'type': 'object',
     'required': ['id', 'description', 'source', 'source_line'],
     'additionalProperties': False,
     'properties': {'id': {'type': 'string'},
                    'description': {'type': 'string'},
                    'source': {'type': 'string'},
                    'source_line': {'type': 'integer', 'minimum': 1},
                    'threshold': {'type': ['number', 'null']},
                    'time_value_ms': {'type': ['integer', 'null']},
                    'ambiguous': {'type': 'boolean'}}}

On instance:
    {}
- [2026-09-20T11:08:39Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:16:10Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:18:10Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:20:19Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T16:50:00+05:30] Prompting bug fixed: Gemini has a bias to output a root object instead of an array. Changed prompt to request a JSON object { 'requirements': [...] } resulting in all 5 requirements successfully extracted from sample_spec.md.
- [2026-09-20T11:30:13Z] plan Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:33:41Z] Generated 8 tests in batch. T01:[R7](nominal), T02:[R8](dropout), T03:[R10](nominal), T04:[R8,R10](ramp_overshoot), T05:[R7,R8](stuck), T06:[R11](dropout), T07:[R9](nominal), T08:[R11](ramp_overshoot)
- [2026-09-20T11:34:24Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:36:43Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T11:36:44Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:37:57Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T11:37:58Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:39:14Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T11:39:16Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:40:36Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T11:40:37Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:41:51Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T11:41:52Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:42:58Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T11:42:59Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:43:59Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T11:44:00Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:45:07Z] timeline T08 rejected by stand-in lint (attempt 1): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:45:08Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:45:46Z] timeline T08 rejected by stand-in lint (attempt 2): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:45:47Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T11:46:25Z] timeline T08 rejected by stand-in lint (attempt 3): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:46:25Z] timeline T08 dropped after 3 attempts.
- [2026-09-20T11:56:19Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T11:56:19Z] timeline T08 rejected by stand-in lint (attempt 1): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:56:19Z] timeline T08 rejected by stand-in lint (attempt 2): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:56:19Z] timeline T08 rejected by stand-in lint (attempt 3): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:56:19Z] timeline T08 dropped after 3 attempts.
- [2026-09-20T11:57:59Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T11:57:59Z] timeline T08 rejected by stand-in lint (attempt 1): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:57:59Z] timeline T08 rejected by stand-in lint (attempt 2): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:57:59Z] timeline T08 rejected by stand-in lint (attempt 3): event at 3000 ms exceeds duration_ms 2500
- [2026-09-20T11:57:59Z] timeline T08 dropped after 3 attempts.
- [2026-09-20T17:35:00+05:30] Coverage Gap: Timeline T08 (Requirement R11, fault: ramp_overshoot) was dropped because LLM generated an event at 3000ms exceeding the test's duration_ms of 2500ms, failing the stand-in lint 3 times.
- [2026-09-20T12:08:18Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:11:17Z] plan Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:17:26Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:19:37Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:19:39Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:21:08Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:21:10Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:22:33Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:22:35Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:24:09Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:24:11Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:25:47Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:25:49Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:27:02Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:27:04Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:28:25Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:28:27Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:29:41Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:29:41Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:32:51Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:32:51Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:33:13Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:33:13Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:36:18Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:36:18Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:36:18Z] explain: T04 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T04; leaving explanation as stub
- [2026-09-20T12:36:18Z] explain: T04 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T04; leaving explanation as stub
- [2026-09-20T12:37:39Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:37:39Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:37:39Z] explain: T04 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T04; leaving explanation as stub
- [2026-09-20T12:37:39Z] explain: T04 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T04; leaving explanation as stub
- [2026-09-20T12:43:47Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:43:47Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:45:27Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:45:27Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:45:59Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:45:59Z] explain: T01 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T01; leaving explanation as stub
- [2026-09-20T12:48:23Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T12:48:23Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T12:48:27Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T12:48:29Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:51:22Z] plan Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:54:42Z] timeline Gemini (gemini-2.5-flash) failed (Error calling model 'gemini-2.5-flash' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:58:04Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T12:58:06Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T12:59:16Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T12:59:18Z] spec Gemini (gemini-2.5-pro) failed (Error calling model 'gemini-2.5-pro' (INVALID_ARGUMENT): 400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}); falling back to Ollama
- [2026-09-20T13:01:06Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:06Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:01:06Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:01:06Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:01:06Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:06Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:01:06Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:06Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:01:06Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:01:06Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:01:07Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T13:01:08Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:08Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:01:08Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:01:08Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:01:08Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:08Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:01:08Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:08Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:01:08Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:01:08Z] explain: T01 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T01; leaving explanation as stub
- [2026-09-20T13:01:08Z] timeline T_SMALL deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:08Z] timeline T_SMALL auto-repair: extended duration_ms from 100 to 250 to fit events
- [2026-09-20T13:01:08Z] timeline T_SMALL accepted after 1 attempts.
- [2026-09-20T13:01:08Z] timeline T_OVERSIZED deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:01:08Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 1): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:01:08Z] timeline T_OVERSIZED deterministic overwrite: test_id (was T_SMALL, forced to T_OVERSIZED)
- [2026-09-20T13:01:08Z] timeline T_OVERSIZED accepted after 2 attempts.
- [2026-09-20T13:19:37Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:19:37Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:19:37Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:19:37Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:19:37Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:19:37Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:19:37Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:19:37Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:19:37Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:19:37Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:21:27Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:21:27Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:21:27Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:21:27Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:21:27Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:21:27Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:21:27Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:21:27Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:21:27Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:21:27Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:21:39Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:21:39Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:21:39Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:21:39Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:21:39Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:21:39Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:21:39Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:21:39Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:21:39Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:21:39Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:22:53Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:22:53Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:22:53Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:22:53Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:22:53Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:22:53Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:22:53Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:22:53Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:22:53Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:22:53Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:23:54Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:23:54Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:23:54Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:23:54Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:23:54Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:23:54Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:23:54Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:23:54Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:23:54Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] explain: T01 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T01; leaving explanation as stub
- [2026-09-20T13:23:54Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:23:54Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:23:54Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:23:54Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:23:54Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:23:54Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:23:54Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:23:54Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:23:54Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:23:54Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:27:02Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T13:27:02Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:02Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:27:02Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:27:02Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:27:02Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:02Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:27:02Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:02Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:27:02Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:27:02Z] explain: T01 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T01; leaving explanation as stub
- [2026-09-20T13:27:03Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:03Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:27:03Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:27:03Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:27:03Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:03Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:27:03Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:03Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:27:03Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:27:03Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:27:03Z] timeline T_SMALL deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:03Z] timeline T_SMALL auto-repair: extended duration_ms from 100 to 250 to fit events
- [2026-09-20T13:27:03Z] timeline T_SMALL accepted after 1 attempts.
- [2026-09-20T13:27:03Z] timeline T_OVERSIZED deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:03Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 1): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:27:03Z] timeline T_OVERSIZED deterministic overwrite: test_id (was T_SMALL, forced to T_OVERSIZED)
- [2026-09-20T13:27:03Z] timeline T_OVERSIZED accepted after 2 attempts.
- [2026-09-20T13:27:19Z] timeline T_SMALL deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:19Z] timeline T_SMALL auto-repair: extended duration_ms from 100 to 250 to fit events
- [2026-09-20T13:27:19Z] timeline T_SMALL accepted after 1 attempts.
- [2026-09-20T13:27:19Z] timeline T_OVERSIZED deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:27:19Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 1): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:27:19Z] timeline T_OVERSIZED deterministic overwrite: test_id (was T_SMALL, forced to T_OVERSIZED)
- [2026-09-20T13:27:19Z] timeline T_OVERSIZED accepted after 2 attempts.
- [2026-09-20T13:28:25Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T13:28:26Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:26Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:28:26Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:28:26Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:28:26Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:26Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:28:26Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:26Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:28:26Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] explain: T01 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T01; leaving explanation as stub
- [2026-09-20T13:28:26Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:26Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:28:26Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:28:26Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:28:26Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:26Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:28:26Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:26Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:28:26Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:28:26Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:28:27Z] timeline T_SMALL deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:27Z] timeline T_SMALL auto-repair: extended duration_ms from 100 to 250 to fit events
- [2026-09-20T13:28:27Z] timeline T_SMALL accepted after 1 attempts.
- [2026-09-20T13:28:27Z] timeline T_OVERSIZED deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:28:27Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 1): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:28:27Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 2): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:28:27Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 3): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:28:27Z] timeline T_OVERSIZED dropped after 3 attempts.
- [2026-09-20T13:38:38Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:38Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:38:38Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:38:38Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:38:38Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:38Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:38:38Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:38Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:38:38Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:38:38Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:38:45Z] Gemini call failed (_GeminiError: forced); falling back to Ollama model=qwen2.5:7b-instruct
- [2026-09-20T13:38:45Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:45Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:38:45Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:38:45Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:38:45Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:45Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:38:45Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:45Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:38:45Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:38:45Z] explain: T01 failed after 2 attempts: LLM_OFFLINE=1 but no cache for explanation T01; leaving explanation as stub
- [2026-09-20T13:38:47Z] timeline T01 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:47Z] timeline T01 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T02 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:38:47Z] timeline T02 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T03 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:38:47Z] timeline T03 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T04 deterministic overwrite: fault_type (was None, forced to stuck)
- [2026-09-20T13:38:47Z] timeline T04 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T05 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:47Z] timeline T05 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T06 deterministic overwrite: fault_type (was None, forced to dropout)
- [2026-09-20T13:38:47Z] timeline T06 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T07 deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:47Z] timeline T07 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T08 deterministic overwrite: fault_type (was None, forced to ramp_overshoot)
- [2026-09-20T13:38:47Z] timeline T08 accepted after 1 attempts.
- [2026-09-20T13:38:47Z] runner: sim.runner not available — using mock sim; results are synthetic, not reflective of real firmware
- [2026-09-20T13:38:47Z] timeline T_SMALL deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:47Z] timeline T_SMALL auto-repair: extended duration_ms from 100 to 250 to fit events
- [2026-09-20T13:38:47Z] timeline T_SMALL accepted after 1 attempts.
- [2026-09-20T13:38:47Z] timeline T_OVERSIZED deterministic overwrite: fault_type (was None, forced to nominal)
- [2026-09-20T13:38:47Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 1): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:38:47Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 2): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:38:47Z] timeline T_OVERSIZED rejected by stand-in lint (attempt 3): healed duration_ms 150100 exceeds 120000 ms cap
- [2026-09-20T13:38:47Z] timeline T_OVERSIZED dropped after 3 attempts.
