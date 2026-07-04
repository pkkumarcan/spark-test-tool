"""
Spark AI Coding Agent — Agentic coding loop with human-in-the-loop.
Uses llm_client for inference, coding_tools for execution.
"""
import asyncio
import difflib
import json
import logging
import os
import re
import time
from typing import AsyncGenerator

from app.backends.llm_client import LLMClient, LLMError
from app.backends.workspace import WORKSPACE_ROOT, is_safe_path, get_absolute_path, ALLOWED_COMMANDS

logger = logging.getLogger("spark.backend.coding_agent")

# ─── Config ────────────────────────────────────────────────────────────────────
MAX_CONTEXT_TOKENS = 32000
MAX_READ_LINES = 500
MAX_TOOL_OUTPUT = 4000
STUCK_LOOP_THRESHOLD = 3
SESSION_DIR = os.path.join(WORKSPACE_ROOT, ".spark_coder", "sessions")

llm = LLMClient()

# ─── Stateful Sessions ─────────────────────────────────────────────────────────
ACTIVE_SESSIONS = {}

# ─── Tool Dispatcher ───────────────────────────────────────────────────────────
def _execute_tool(name: str, arguments: dict) -> str:
    """Route tool calls to coding_tools module. Returns result string."""
    try:
        from app.backends.coding_tools import execute_tool
        return execute_tool(name, arguments)
    except Exception as e:
        return f"Error executing tool '{name}': {e}"

def _build_diff_html(old_content: str, new_content: str) -> str:
    """Generate HTML diff between old and new file content."""
    d = difflib.HtmlDiff()
    return d.make_table(
        old_content.splitlines(), new_content.splitlines(),
        context=True, numlines=3
    )


async def _auto_lint(path: str) -> str:
    """Run ruff check on a file after write/edit. Returns lint output or empty string."""
    if not path.endswith(".py"):
        return ""
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return ""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ruff", "check", "--output-format=text", abs_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE_ROOT
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace").strip()
        if output and proc.returncode != 0:
            return output
    except Exception:
        pass
    return ""


# ─── Context Management ────────────────────────────────────────────────────────
def _estimate_tokens(text: str) -> int:
    return len(text) // 4

def _compress_messages(messages: list, max_tokens: int = MAX_CONTEXT_TOKENS) -> list:
    """Truncate older messages when context grows too large. Keeps system prompt + recent messages."""
    total = sum(_estimate_tokens(m.get("content", "")) for m in messages)
    if total <= max_tokens:
        return messages

    system = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]

    system_tokens = sum(_estimate_tokens(m.get("content", "")) for m in system)
    budget = max_tokens - system_tokens - 2000

    if budget <= 0:
        return system + rest[-2:]

    kept = []
    used = 0
    for msg in reversed(rest):
        t = _estimate_tokens(msg.get("content", ""))
        if used + t > budget:
            break
        kept.insert(0, msg)
        used += t

    if kept and kept[0].get("role") == "user":
        summary_msg = {"role": "user", "content": f"[{len(rest) - len(kept)} earlier messages compressed to save context. Continuing from here.]"}
        kept = [summary_msg] + kept

    return system + kept

# ─── Conversation Persistence ──────────────────────────────────────────────────
def _save_session(session_id: str, messages: list, meta: dict = None):
    try:
        os.makedirs(SESSION_DIR, exist_ok=True)
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        data = {"messages": messages, "meta": meta or {}, "saved_at": time.time()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to save session {session_id}: {e}")

def _load_session(session_id: str) -> dict:
    try:
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

# ─── System Prompt Builder ─────────────────────────────────────────────────────
def _build_system_prompt(task: str, mode: str = "build") -> str:
    """Construct the agent system prompt with tool definitions and workspace context."""
    from app.backends.coding_tools import TOOLS_SCHEMA

    tools_desc = "\n".join(
        f"- **{t['name']}**: {t['description']}\n  Parameters: {json.dumps(t['parameters'].get('properties', {}), indent=2)}"
        for t in TOOLS_SCHEMA
    )

    prompt = (
        "You are Spark Coder, an autonomous coding agent operating in a local workstation.\n"
        "Your goal is to solve the developer task using the available tools.\n\n"
        f"=== WORKSPACE: {WORKSPACE_ROOT} ===\n\n"
        "=== AVAILABLE TOOLS ===\n"
        f"{tools_desc}\n\n"
        "To use a tool, output EXACTLY this JSON format:\n"
        '{"tool": "tool_name", "arguments": {"param": "value"}}\n\n'
        "Rules:\n"
        "- Output ONLY a JSON tool call when you need to execute a tool.\n"
        "- For conversational responses (greetings, explanations), output plain text — no JSON.\n"
        "- When the task is complete, call the `done` tool with a summary.\n"
        "- Read files before modifying them. Search before reading unknown files.\n"
        "- Use `edit_file` for surgical changes (preferred over whole-file `write_file`).\n"
        "- Never attempt destructive commands (rm -rf, etc.).\n"
    )

    if mode == "plan":
        prompt += (
            "\n=== MODE: PLAN ONLY ===\n"
            "Discuss the task, formulate a plan, write it to .spark_coder/PLAN.md via write_file.\n"
            "Do NOT execute code or run commands. When done, call `done` with your plan summary.\n"
        )
    else:
        prompt += (
            "\n=== MODE: BUILD/EXECUTE ===\n"
            "Actively write code, run tests, and verify your changes.\n"
            "When the task is complete and verified, call `done` with a summary.\n"
        )

    return prompt

# ─── Tool Call Parser ──────────────────────────────────────────────────────────
def _parse_tool_call(text: str) -> dict | None:
    """Extract JSON tool call from LLM response. Returns {tool, arguments} or None."""
    cleaned = text.strip()

    # Try direct JSON parse first
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "tool" in obj:
            return obj
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    code_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
    if code_match:
        try:
            obj = json.loads(code_match.group(1).strip())
            if isinstance(obj, dict) and "tool" in obj:
                return obj
        except json.JSONDecodeError:
            pass

    # Try finding first complete JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            obj = json.loads(cleaned[start:end])
            if isinstance(obj, dict) and "tool" in obj:
                return obj
        except json.JSONDecodeError:
            pass

    return None

# ─── Quick Loop (non-SSE, for API endpoint) ───────────────────────────────────
async def run_coding_loop(task: str, ollama_url: str, model: str = "qwen3:8b", max_iterations: int = 5):
    """Simple coding loop without SSE streaming. Returns result dict."""
    messages = [
        {"role": "system", "content": _build_system_prompt(task)},
        {"role": "user", "content": task}
    ]
    steps = []

    for i in range(max_iterations):
        messages = _compress_messages(messages)
        try:
            result = await llm.chat(messages, model=model)
            response_text = result["content"]
        except LLMError as e:
            return {"status": "error", "error": str(e), "steps": steps}

        steps.append({"iteration": i + 1, "response": response_text})

        tool_call = _parse_tool_call(response_text)
        if not tool_call:
            return {"status": "completed", "iterations": i + 1, "resolution": response_text, "steps": steps}

        tool_name = tool_call.get("tool", "")
        tool_args = tool_call.get("arguments", {})

        if tool_name == "done":
            return {"status": "completed", "iterations": i + 1, "resolution": tool_args.get("summary", response_text), "steps": steps}

        tool_result = _execute_tool(tool_name, tool_args)
        steps[-1]["tool_call"] = {"name": tool_name, "arguments": tool_args, "output": tool_result[:500]}

        messages.append({"role": "assistant", "content": response_text})
        messages.append({"role": "user", "content": f"Tool '{tool_name}' result:\n{tool_result}"})

    return {"status": "exhausted", "iterations": max_iterations, "message": "Max iterations reached.", "steps": steps}

# ─── Stateful SSE Loop (main agent) ───────────────────────────────────────────

# Simple conversational patterns that don't need tools
_CONVERSATIONAL_RE = re.compile(
    r'^(hi|hello|hey|how are you|what\'?s? up|thanks|thank you|ok|okay|'
    r'who are you|what can you do|help|bye|goodbye|see you|'
    r'what is (the )?weather|tell me a joke|how\'?s? it going)'
    r'[\s!?.]*$', re.IGNORECASE
)

async def run_agentic_loop(
    session_id: str,
    task: str,
    model: str,
    max_iterations: int = 15,
    mode: str = "build"
) -> AsyncGenerator[str, None]:
    """
    Stateful coding agent loop yielding SSE events.
    Supports human-in-the-loop pauses for file writes and command execution.
    """
    session = ACTIVE_SESSIONS.get(session_id)
    if not session:
        yield _sse("log", {"content": "Error: Session not initialized."})
        return

    yield _sse("log", {"content": "Starting coding agent session..."})

    # Fast-path: conversational messages don't need tools
    if _CONVERSATIONAL_RE.match(task.strip()):
        try:
            result = await llm.chat(
                [{"role": "system", "content": "You are Spark AI, a helpful coding assistant. Respond naturally and concisely."},
                 {"role": "user", "content": task}],
                model=model
            )
            yield _sse("text", {"content": result["content"]})
            yield _sse("status", {"status": "completed", "resolution": result["content"]})
        except LLMError as e:
            yield _sse("text", {"content": f"Hello! I'm Spark AI. How can I help you today?"})
            yield _sse("status", {"status": "completed", "resolution": "Fallback greeting"})
        return

    # Build system prompt
    system_prompt = _build_system_prompt(task, mode)

    # Load MEMORY.md if exists
    memory_path = os.path.join(WORKSPACE_ROOT, ".spark_coder", "MEMORY.md")
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                memory = f.read()
            if memory:
                system_prompt += f"\n\n=== PROJECT MEMORY ===\n{memory}\n======================"
        except Exception:
            pass

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]

    # Load previous session if exists
    saved = _load_session(session_id)
    if saved.get("messages"):
        messages = saved["messages"] + [{"role": "user", "content": task}]

    # Stuck-loop detection
    consecutive_errors = 0
    recent_tool_calls = []

    for iteration in range(max_iterations):
        yield _sse("log", {"content": f"Thinking... (Step {iteration + 1}/{max_iterations})"})

        # Compress context
        messages = _compress_messages(messages)

        # Call LLM with streaming
        try:
            stream = await llm.chat(messages, model=model, stream=True)
            response_text = ""
            async for chunk in stream:
                token = chunk.get("token", "")
                done = chunk.get("done", False)
                if token:
                    response_text += token
                    yield _sse("token", {"content": token})
                if done:
                    break
        except LLMError as e:
            yield _sse("log", {"content": f"LLM request failed: {e}"})
            break

        # Parse tool call
        tool_call = _parse_tool_call(response_text)

        if not tool_call:
            # Conversational response — already streamed via token events
            yield _sse("status", {"status": "completed", "resolution": response_text})
            _save_session(session_id, messages, {"status": "completed"})
            break

        tool_name = tool_call.get("tool", "")
        tool_args = tool_call.get("arguments", {})

        # ─── done tool ─────────────────────────────────────────────────
        if tool_name == "done":
            summary = tool_args.get("summary", "Task completed.")
            yield _sse("log", {"content": f"Task completed: {summary}"})
            yield _sse("status", {"status": "completed", "resolution": summary})
            _save_session(session_id, messages, {"status": "completed"})
            break

        # ─── Stuck-loop detection ──────────────────────────────────────
        recent_tool_calls.append(tool_name)
        if len(recent_tool_calls) > 3:
            recent_tool_calls.pop(0)
        if len(recent_tool_calls) == 3 and len(set(recent_tool_calls)) == 1:
            consecutive_errors += 1
            if consecutive_errors >= STUCK_LOOP_THRESHOLD:
                yield _sse("log", {"content": f"Agent stuck in loop repeating '{tool_name}'. Stopping."})
                yield _sse("status", {"status": "completed", "resolution": "Agent detected stuck loop and stopped."})
                break
        else:
            consecutive_errors = max(0, consecutive_errors - 1)

        yield _sse("log", {"content": f"Using tool: {tool_name}"})

        # ─── write_file — approval required ────────────────────────────
        if tool_name == "write_file":
            path = tool_args.get("path", "")
            content = tool_args.get("content", "")

            # Generate diff
            abs_path = get_absolute_path(path)
            old_content = ""
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        old_content = f.read()
                except Exception:
                    pass

            html_diff = _build_diff_html(old_content, content)
            yield _sse("awaiting_file_write", {"path": path, "diff": html_diff, "content": content})

            # Wait for approval
            approved = await _wait_approval(session)
            if approved:
                tool_result = _execute_tool("write_file", tool_args)
                yield _sse("log", {"content": f"File written: {path}"})
                # Auto-lint Python files
                lint_result = await _auto_lint(path)
                if lint_result:
                    yield _sse("log", {"content": f"Lint issues in {path}:\n{lint_result}"})
                    tool_result += f"\n\nLint warnings:\n{lint_result}"
            else:
                feedback = session.get("reject_feedback", "Rejected by user.")
                tool_result = f"Error: Write to '{path}' rejected. Feedback: {feedback}"
                yield _sse("log", {"content": f"Write rejected: {feedback}"})

        # ─── edit_file — approval required ─────────────────────────────
        elif tool_name == "edit_file":
            path = tool_args.get("path", "")
            old_text = tool_args.get("old_text", "")
            new_text = tool_args.get("new_text", "")

            yield _sse("awaiting_file_write", {
                "path": path,
                "diff": f"<pre>Replace:\n{_esc(old_text)}\n\nWith:\n{_esc(new_text)}</pre>",
                "content": new_text,
                "edit_mode": True
            })

            approved = await _wait_approval(session)
            if approved:
                tool_result = _execute_tool("edit_file", tool_args)
                yield _sse("log", {"content": f"File edited: {path}"})
                lint_result = await _auto_lint(path)
                if lint_result:
                    yield _sse("log", {"content": f"Lint issues in {path}:\n{lint_result}"})
                    tool_result += f"\n\nLint warnings:\n{lint_result}"
            else:
                feedback = session.get("reject_feedback", "Rejected by user.")
                tool_result = f"Error: Edit to '{path}' rejected. Feedback: {feedback}"
                yield _sse("log", {"content": f"Edit rejected: {feedback}"})

        # ─── multi_replace — approval required ──────────────────────────
        elif tool_name == "multi_replace":
            path = tool_args.get("path", "")
            replacements = tool_args.get("replacements", [])
            summary = "; ".join(f"'{r.get('old_text','')[:30]}...' → '{r.get('new_text','')[:30]}...'" for r in replacements[:3])
            yield _sse("awaiting_file_write", {
                "path": path,
                "diff": f"<pre>Multi-replace ({len(replacements)} changes):\n{_esc(summary)}</pre>",
                "content": summary,
                "edit_mode": True
            })
            approved = await _wait_approval(session)
            if approved:
                tool_result = _execute_tool("multi_replace", tool_args)
                yield _sse("log", {"content": f"Multi-replace applied to {path}"})
                lint_result = await _auto_lint(path)
                if lint_result:
                    yield _sse("log", {"content": f"Lint issues in {path}:\n{lint_result}"})
                    tool_result += f"\n\nLint warnings:\n{lint_result}"
            else:
                feedback = session.get("reject_feedback", "Rejected by user.")
                tool_result = f"Error: Multi-replace to '{path}' rejected. Feedback: {feedback}"
                yield _sse("log", {"content": f"Multi-replace rejected: {feedback}"})

        # ─── create_file — approval required ───────────────────────────
        elif tool_name == "create_file":
            path = tool_args.get("path", "")
            yield _sse("awaiting_file_write", {"path": path, "content": tool_args.get("content", ""), "create_mode": True})

            approved = await _wait_approval(session)
            if approved:
                tool_result = _execute_tool("create_file", tool_args)
                yield _sse("log", {"content": f"File created: {path}"})
                lint_result = await _auto_lint(path)
                if lint_result:
                    yield _sse("log", {"content": f"Lint issues in {path}:\n{lint_result}"})
                    tool_result += f"\n\nLint warnings:\n{lint_result}"
            else:
                tool_result = f"Error: Create '{path}' rejected."
                yield _sse("log", {"content": f"Create rejected."})

        # ─── delete_file — approval required ───────────────────────────
        elif tool_name == "delete_file":
            path = tool_args.get("path", "")
            yield _sse("awaiting_file_write", {"path": path, "delete_mode": True})

            approved = await _wait_approval(session)
            if approved:
                tool_result = _execute_tool("delete_file", tool_args)
                yield _sse("log", {"content": f"File deleted: {path}"})
            else:
                tool_result = f"Error: Delete '{path}' rejected."
                yield _sse("log", {"content": f"Delete rejected."})

        # ─── run_command — approval required ───────────────────────────
        elif tool_name in ("run_command",):
            command = tool_args.get("command", "")
            yield _sse("awaiting_command_run", {"command": command})

            approved = await _wait_approval(session)
            if approved:
                yield _sse("log", {"content": f"Running: {command}"})
                tool_result = _execute_tool("run_command", tool_args)

                # Stream terminal output
                for line in tool_result.split("\n"):
                    if line.strip():
                        yield _sse("terminal_log", {"stream": "stdout", "content": line})
            else:
                feedback = session.get("reject_feedback", "Rejected by user.")
                tool_result = f"Error: Command rejected. Feedback: {feedback}"
                yield _sse("log", {"content": f"Command rejected: {feedback}"})

        # ─── Read-only tools (no approval needed) ──────────────────────
        else:
            tool_result = _execute_tool(tool_name, tool_args)
            # Truncate large outputs
            if len(tool_result) > MAX_TOOL_OUTPUT:
                tool_result = tool_result[:MAX_TOOL_OUTPUT] + f"\n... [Truncated, {len(tool_result)} chars total]"

            yield _sse("log", {"content": f"{tool_name} completed"})

        # Append to conversation
        messages.append({"role": "assistant", "content": response_text})
        messages.append({"role": "user", "content": f"Tool '{tool_name}' result:\n{tool_result}"})

    else:
        yield _sse("status", {"status": "completed", "resolution": "Max iterations reached."})

    yield _sse("status", {"status": "finished"})
    _save_session(session_id, messages, {"status": "finished"})


# ─── Helpers ───────────────────────────────────────────────────────────────────
async def _wait_approval(session: dict, timeout: float = 600.0) -> bool:
    """Wait for user to approve or reject. Returns True if approved."""
    session["approved_event"].clear()
    session["rejected_event"].clear()

    try:
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(session["approved_event"].wait()),
                asyncio.create_task(session["rejected_event"].wait())
            ],
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout
        )
        for t in pending:
            t.cancel()
        return bool(done) and session["approved_event"].is_set()
    except asyncio.TimeoutError:
        return False


def _sse(event_type: str, data: dict) -> str:
    """Format an SSE event string."""
    data["type"] = event_type
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _esc(text: str) -> str:
    """Escape HTML for safe display."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─── Set workspace root (for runtime switching) ────────────────────────────────
import app.backends.workspace as _workspace

def set_workspace_root(new_root: str):
    _workspace.WORKSPACE_ROOT = new_root
    global WORKSPACE_ROOT
    WORKSPACE_ROOT = new_root
