# Spark AI Coding Agent — IDE Documentation

> Reference guide for debugging, enhancing, and maintaining the Spark IDE.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (IDE)                        │
│  ide.html — 3-panel: Left (Chats/Files) | Chat | Right  │
│  Connects via SSE to /api/orchestrator/code/stream      │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/SSE
┌──────────────────────▼──────────────────────────────────┐
│                 FastAPI Gateway (main.py)                │
│  Routes: /api/orchestrator/code/*, /api/ide/*            │
│  Middleware: CORS, rate limit, API key auth              │
└──────┬───────────────┬───────────────┬──────────────────┘
       │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│ coding_     │ │ coding_     │ │ llm_client  │
│ agent.py    │ │ tools.py    │ │ .py         │
│ (484 lines) │ │ (543 lines) │ │ (127 lines) │
│ Agent loop  │ │ 14 tools    │ │ Ollama/vLLM │
│ SSE stream  │ │ Dispatcher  │ │ Retry+retry │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
┌──────▼───────────────▼───────────────▼──────────────────┐
│                  workspace.py (20 lines)                 │
│  WORKSPACE_ROOT, is_safe_path, get_absolute_path        │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Docker (spark-gateway container)            │
│  Volume: .:/workspace/project                           │
│  Env: WORKSPACE_ROOT=/workspace/project                 │
└─────────────────────────────────────────────────────────┘
```

---

## File Reference

### Backend Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/backends/workspace.py` | 20 | **Shared config** — `WORKSPACE_ROOT`, `is_safe_path()`, `get_absolute_path()`, `ALLOWED_COMMANDS` |
| `app/backends/llm_client.py` | 127 | **LLM client** — `LLMClient.chat()` with Ollama/vLLM routing, 3× retry, streaming, JSON mode |
| `app/backends/coding_tools.py` | 543 | **14 tools** — read/create/write/edit/delete/list/search/run_command/git_status/diff/log/diagnostics/tests/done |
| `app/backends/coding_agent.py` | 484 | **Agent loop** — `run_agentic_loop()` SSE streaming, approval flow, context management, stuck-loop detection |
| `app/main.py` | 2066 | **Routes** — All API endpoints, session lifecycle, auth middleware |
| `docker-compose.yml` | 64 | **Docker** — Gateway, Whisper, F5-TTS services |

### Frontend Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/static/ide.html` | 1438 | **IDE UI** — 3-panel layout, chat, file tree, plan/tasks, terminal panel |

### Test Files

| File | Lines | Purpose |
|------|-------|---------|
| `tests/test_coding_agent.py` | 217 | **E2E tests** — 9 tests with auto-approval harness |

---

## API Endpoints

### Agent Endpoints (SSE Streaming)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/orchestrator/code/stream` | GET | **Main agent endpoint** — streams SSE events. Params: `task`, `model`, `session_id` |
| `/api/orchestrator/code/approve` | POST | Approve file write/command run. Body: `{session_id}` |
| `/api/orchestrator/code/reject` | POST | Reject with feedback. Body: `{session_id, feedback}` |

### IDE Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ide/files` | GET | List workspace file tree |
| `/api/ide/file` | GET | Read file content. Param: `path` |
| `/api/ide/file` | POST | Save file content. Body: `{path, content}` |

### System Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (pings Ollama, ComfyUI, Whisper, F5-TTS) |
| `/api/gpu/status` | GET | GPU utilization from nvidia-smi |
| `/api/text/models` | GET | List available Ollama models |

---

## SSE Event Types

The agent loop yields these SSE events:

| Event Type | Fields | When |
|------------|--------|------|
| `log` | `{content}` | Informational messages (routed to terminal, not chat) |
| `text` | `{content}` | **Actual response** — rendered in chat bubble |
| `status` | `{status, resolution}` | `completed`/`finished` — updates badge |
| `plan` | `{content}` | Plan text — updates right panel |
| `awaiting_file_write` | `{path, diff, content}` | **Approval needed** — shows diff card |
| `awaiting_command_run` | `{command}` | **Approval needed** — shows command card |
| `terminal_log` | `{stream, content}` | Terminal output — shown in terminal panel |

**Critical:** Frontend reads `evt.content` (not `evt.message`). Backend must send `content` field.

---

## Agent Flow

```
User types message
       │
       ▼
┌─────────────────────┐
│ Conversational?      │──── Yes ──→ Direct LLM call → text response
│ (hi, hello, etc.)    │
└─────────┬───────────┘
          │ No
          ▼
┌─────────────────────┐
│ Tool loop begins     │
│ (max 15 iterations)  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Call LLM             │
│ (qwen3:4b default)   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Parse response       │
│ _parse_tool_call()   │
└────┬───────────┬────┘
     │           │
  Tool call    Plain text
     │           │
     ▼           ▼
┌─────────┐  ┌─────────┐
│ Execute  │  │ Return  │
│ tool     │  │ text    │
└────┬────┘  └─────────┘
     │
     ▼
┌─────────────────────┐
│ Tool needs approval? │
│ (write/edit/delete)  │
└────┬───────────┬────┘
     │           │
    Yes          No
     │           │
     ▼           ▼
┌─────────┐  ┌─────────┐
│ Wait for │  │ Execute │
│ approve  │  │ directly│
└────┬────┘  └────┬────┘
     │            │
     ▼            │
┌─────────┐       │
│ Continue │◄──────┘
│ loop     │
└─────────┘
```

---

## Tool Suite (14 Tools)

| Tool | Parameters | Approval? | Description |
|------|-----------|-----------|-------------|
| `read_file` | `path`, `start_line?`, `end_line?` | No | Read file (max 500 lines) |
| `create_file` | `path`, `content` | Yes | Create new file |
| `write_file` | `path`, `content` | Yes | Overwrite file |
| `edit_file` | `path`, `old_text`, `new_text` | Yes | Surgical text replacement |
| `delete_file` | `path` | Yes | Delete file |
| `list_directory` | `path?` | No | List directory |
| `search_files` | `pattern`, `path?`, `include?` | No | Regex search (max 50 results) |
| `run_command` | `command`, `timeout?` | Yes | Run shell command |
| `git_status` | — | No | Git status |
| `git_diff` | `path?` | No | Git diff |
| `git_log` | `n?` | No | Git log |
| `get_diagnostics` | `path?` | No | Lint/type check |
| `run_tests` | `test_path?` | No | Run pytest |
| `done` | `summary` | No | Signal completion |

---

## Key Functions

### coding_agent.py

| Function | Purpose |
|----------|---------|
| `run_agentic_loop(session_id, task, model, max_iterations, mode)` | Main SSE generator — yields events |
| `run_coding_loop(task, ollama_url, model, max_iterations)` | Simple loop (no SSE, returns dict) |
| `_build_system_prompt(task, mode)` | Construct agent system prompt |
| `_parse_tool_call(text)` | 3-stage JSON parser: direct → code block → brace search |
| `_execute_tool(name, arguments)` | Route to coding_tools.execute_tool() |
| `_compress_messages(messages, max_tokens)` | Context window management |
| `_save_session(session_id, messages, meta)` | Persist to `.spark_coder/sessions/` |
| `_wait_approval(session, timeout)` | Pause for human-in-the-loop |
| `_sse(event_type, data)` | Format SSE event string |
| `_CONVERSATIONAL_RE` | Regex for greeting detection (fast-path) |

### coding_tools.py

| Function | Purpose |
|----------|---------|
| `execute_tool(name, arguments)` | Dispatcher — routes to correct tool function |
| `read_file(**kwargs)` | Read file with optional line range |
| `edit_file(**kwargs)` | Exact-match search/replace |
| `search_files(**kwargs)` | Regex content search |
| `run_command(**kwargs)` | Shell execution with security checks |
| `TOOLS_SCHEMA` | JSON schema list for system prompt |

### llm_client.py

| Function | Purpose |
|----------|---------|
| `LLMClient.chat(messages, model, json_mode, stream, timeout)` | Unified LLM call |
| `LLMClient._stream(messages, model, ...)` | Streaming generator |
| `LLMClient._build_payload(...)` | Ollama/vLLM payload builder |
| `LLMClient._estimate_tokens(text)` | Rough token count (4 chars ≈ 1 token) |

---

## Debugging Guide

### Agent returns "Task completed" with no content

**Cause:** LLM returned a tool call that wasn't parsed, or `done` tool wasn't called.

**Fix:** Check docker logs:
```bash
docker logs spark-gateway --tail 30
```

### Agent loops 15 times for simple "hi"

**Cause:** Conversational fast-path not matching.

**Fix:** Check `_CONVERSATIONAL_RE` regex in `coding_agent.py:221`. The task must match exactly (case-insensitive).

### IDE file tree not loading

**Cause:** `coding_agent` not imported in `main.py`.

**Fix:** Ensure `main.py:25` includes `coding_agent` in imports:
```python
from app.backends import (..., coding_agent)
```

### Chat shows "Task completed" instead of LLM response

**Cause:** Frontend SSE parser not reading `event:` lines.

**Fix:** Check `ide.html` SSE parser — must parse both `event:` and `data:` lines from SSE blocks.

### Approval cards don't show diffs

**Cause:** Wrong field name — frontend checks `evt.diff_html`, backend sends `evt.diff`.

**Fix:** Ensure `ide.html` approval handler reads `evt.diff` (not `evt.diff_html`).

### Status badge keeps spinning

**Cause:** `status` event handler only checks `evt.content`, but backend sends `evt.status` + `evt.resolution`.

**Fix:** Check `ide.html` status handler — must handle `evt.status === 'completed'` and `evt.resolution`.

### LLM returns 405 Method Not Allowed

**Cause:** `OLLAMA_URL` env var missing `/api/chat` suffix.

**Fix:** `llm_client.py` auto-appends `/api/chat` if missing. Verify env var is just `http://host.docker.internal:11434`.

### Circular import error

**Cause:** `coding_tools.py` imports from `coding_agent.py` instead of `workspace.py`.

**Fix:** Both should import from `workspace.py`:
```python
from app.backends.workspace import WORKSPACE_ROOT, is_safe_path, get_absolute_path
```

### Sessions lost on page refresh

**Cause:** localStorage not saving.

**Fix:** Check `saveSessions()` is called in: `newChat()`, `selectSession()`, `appendMsg()`, and after agent response.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `WORKSPACE_ROOT` | `/workspace/project` | Agent sandbox root |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama API base |
| `VLLM_URL` | `http://host.docker.internal:8000` | vLLM API base |
| `SPARK_API_KEY` | (empty) | API key for auth (empty = no auth) |
| `OUTPUT_DIR` | `/app/output` | Generated output directory |
| `COMFYUI_URL` | `http://host.docker.internal:8188` | ComfyUI API |
| `COMFYUI_FALLBACK_URL` | `http://10.0.0.162:8188` | Node B ComfyUI fallback |
| `WHISPER_URL` | `http://whisper-stt:8000` | Whisper STT |
| `F5_TTS_URL` | `http://f5-tts:8000` | F5-TTS |
| `ALLOWED_ORIGINS` | `http://localhost:5050,...` | CORS origins |

---

## Adding a New Tool

1. Add function to `coding_tools.py`:
```python
def my_new_tool(**kwargs) -> str:
    param = kwargs.get("param", "")
    # ... implementation
    return "result"
```

2. Add schema to `TOOLS_SCHEMA`:
```python
{
    "name": "my_new_tool",
    "description": "What it does",
    "parameters": {
        "type": "object",
        "properties": {"param": {"type": "string", "description": "..."}},
        "required": ["param"]
    }
}
```

3. Add to `execute_tool()` dispatcher:
```python
elif name == "my_new_tool":
    return my_new_tool(**arguments)
```

4. If tool needs approval, add case in `coding_agent.py` `run_agentic_loop()`.

---

## Frontend Event Handling

The `handleEvent()` function in `ide.html` processes SSE events:

```javascript
function handleEvent(evt, agentMsg, bubble, gotContent) {
  const msg = evt.content || evt.message || '';
  switch (evt.type) {
    case 'log':         // → terminal only (not chat)
    case 'terminal_log': // → terminal panel
    case 'plan':        // → right panel
    case 'status':      // → badge update
    case 'text':        // → chat bubble (actual response)
    case 'awaiting_file_write':  // → approval card with diff
    case 'awaiting_command_run': // → approval card with command
  }
}
```

**Critical field names:**
- `evt.content` — text content (NOT `evt.message`)
- `evt.diff` — HTML diff table (NOT `evt.diff_html`)
- `evt.status` — `completed`/`finished`/`running`
- `evt.resolution` — completion summary

---

## Performance Notes

| Metric | Value |
|--------|-------|
| Default model | `qwen3:4b` (2.4GB VRAM, fast) |
| Conversational response | ~1.5s (single LLM call) |
| Tool-using response | ~5-15s per iteration |
| Max iterations | 15 (configurable) |
| Context window | 32K tokens (auto-compress) |
| File read limit | 500 lines |
| Search results limit | 50 |
| Token estimation | 4 chars ≈ 1 token |

---

## Docker Commands

```bash
# Rebuild and restart
docker compose build gateway-app && docker compose up -d gateway-app

# View logs
docker logs spark-gateway -f

# Check health
curl http://localhost:5050/health

# Unload idle model from VRAM
curl http://localhost:11434/api/generate -d '{"model":"gemma4:12b-it-qat","keep_alive":0}'

# Test agent endpoint
curl -N "http://localhost:5050/api/orchestrator/code/stream?task=hello&model=qwen3:4b&session_id=test"
```
