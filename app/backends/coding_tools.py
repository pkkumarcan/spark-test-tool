import os
import re
import shlex
import subprocess
import logging
import glob as glob_module

import app.backends.workspace as _workspace
from app.backends.workspace import is_safe_path, get_absolute_path

logger = logging.getLogger("spark.backend.coding_tools")

MAX_READ_LINES = 500
MAX_SEARCH_RESULTS = 50


def read_file(**kwargs) -> str:
    path = kwargs.get("path", "")
    start_line = kwargs.get("start_line")
    end_line = kwargs.get("end_line")

    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if os.path.isdir(abs_path):
        return f"Error: '{path}' is a directory, not a file."

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total = len(lines)
        truncated = False

        if start_line is not None or end_line is not None:
            s = (start_line or 1) - 1
            e = end_line or total
            lines = lines[s:e]

        if len(lines) > MAX_READ_LINES:
            lines = lines[:MAX_READ_LINES]
            truncated = True

        output = "".join(lines)
        if truncated:
            output += f"\n\n[Truncated at {MAX_READ_LINES} lines. Total: {total} lines. Use start_line/end_line to read specific ranges.]"
        return output
    except Exception as e:
        return f"Error reading file: {e}"


def create_file(**kwargs) -> str:
    path = kwargs.get("path", "")
    content = kwargs.get("content", "")

    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if os.path.exists(abs_path):
        return f"Error: File '{path}' already exists. Use write_file to overwrite."

    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully created file '{path}'."
    except Exception as e:
        return f"Error creating file: {e}"


def write_file(**kwargs) -> str:
    path = kwargs.get("path", "")
    content = kwargs.get("content", "")

    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)

    is_req = path.endswith("requirements.txt")
    old_content = None
    if is_req and os.path.exists(abs_path):
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                old_content = f.read()
        except Exception:
            pass

    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        if is_req:
            from app.backends import security_scanner
            audit = security_scanner.run_project_scan()
            if audit.get("status") == "alert":
                if old_content is not None:
                    with open(abs_path, "w", encoding="utf-8") as f:
                        f.write(old_content)
                else:
                    os.remove(abs_path)
                return f"Error: Write blocked by security scanner. Details: {', '.join(audit.get('alerts', []))}"

        return f"Successfully wrote contents to file '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"


def edit_file(**kwargs) -> str:
    path = kwargs.get("path", "")
    old_text = kwargs.get("old_text", "")
    new_text = kwargs.get("new_text", "")

    if not old_text:
        return "Error: old_text cannot be empty."
    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count(old_text)
        if count == 0:
            return f"Error: old_text not found in '{path}'."
        if count > 1:
            return f"Error: old_text found {count} times in '{path}'. Provide more context to make it unique."

        new_content = content.replace(old_text, new_text, 1)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Successfully edited file '{path}'."
    except Exception as e:
        return f"Error editing file: {e}"


def multi_replace(**kwargs) -> str:
    """Apply multiple non-contiguous replacements to a file in one operation.
    replacements: list of {old_text, new_text} dicts.
    """
    path = kwargs.get("path", "")
    replacements = kwargs.get("replacements", [])

    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if not replacements:
        return "Error: No replacements provided."

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        applied = 0
        errors = []
        for i, repl in enumerate(replacements):
            old_text = repl.get("old_text", "")
            new_text = repl.get("new_text", "")
            if not old_text:
                errors.append(f"Replacement {i+1}: empty old_text")
                continue
            count = content.count(old_text)
            if count == 0:
                errors.append(f"Replacement {i+1}: old_text not found")
                continue
            if count > 1:
                errors.append(f"Replacement {i+1}: old_text found {count} times (not unique)")
                continue
            content = content.replace(old_text, new_text, 1)
            applied += 1

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        result = f"Applied {applied}/{len(replacements)} replacements to '{path}'."
        if errors:
            result += " Errors: " + "; ".join(errors)
        return result
    except Exception as e:
        return f"Error in multi_replace: {e}"


def delete_file(**kwargs) -> str:
    path = kwargs.get("path", "")

    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if os.path.isdir(abs_path):
        return f"Error: '{path}' is a directory. Cannot delete directories with this tool."

    try:
        os.remove(abs_path)
        return f"Successfully deleted file '{path}'."
    except Exception as e:
        return f"Error deleting file: {e}"


def list_directory(**kwargs) -> str:
    path = kwargs.get("path", ".")

    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."
    if not os.path.isdir(abs_path):
        return f"Error: '{path}' is not a directory."

    try:
        items = sorted(os.listdir(abs_path))
        if not items:
            return f"Directory '{path}' is empty."
        result = []
        for item in items:
            item_path = os.path.join(abs_path, item)
            is_dir = os.path.isdir(item_path)
            if is_dir:
                result.append(f"[DIR]  {item}/")
            else:
                size = os.path.getsize(item_path)
                result.append(f"[FILE] {item} ({size} bytes)")
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {e}"


def search_files(**kwargs) -> str:
    pattern = kwargs.get("pattern", "")
    path = kwargs.get("path", ".")
    include = kwargs.get("include", "*")

    if not pattern:
        return "Error: pattern is required."
    if not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = get_absolute_path(path)
    if not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Error: Invalid regex pattern: {e}"

    results = []
    try:
        for root, dirs, files in os.walk(abs_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                if not glob_module.fnmatch.fnmatch(fname, include):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = os.path.relpath(fpath, _workspace.WORKSPACE_ROOT)
                                results.append(f"{rel}:{i}: {line.rstrip()}")
                                if len(results) >= MAX_SEARCH_RESULTS:
                                    results.append(f"\n[Truncated at {MAX_SEARCH_RESULTS} results. Refine your search pattern.]")
                                    return "\n".join(results)
                except Exception:
                    continue
    except Exception as e:
        return f"Error searching files: {e}"

    if not results:
        return f"No matches found for pattern '{pattern}' in '{path}'."
    return "\n".join(results)


def run_command(**kwargs) -> str:
    command = kwargs.get("command", "")
    timeout = kwargs.get("timeout", 60)

    if not command:
        return "Error: command is required."

    from app.backends import security_scanner
    command_audit = security_scanner.audit_command_string(command)
    if command_audit.get("status") == "alert":
        return f"Error: Command blocked by security audit. Reason: {', '.join(command_audit.get('violations', []))}"

    try:
        cmd_parts = shlex.split(command)
    except ValueError as e:
        return f"Error: Invalid command syntax: {e}"

    if not cmd_parts:
        return "Error: Empty command."

    base_cmd = os.path.basename(cmd_parts[0])
    from app.backends.workspace import ALLOWED_COMMANDS as _ALLOWED
    if base_cmd not in _ALLOWED:
        return (
            f"Error: Command '{base_cmd}' is not in the allowed command list. "
            f"Permitted commands: {', '.join(sorted(_ALLOWED))}"
        )

    blocked_patterns = [r"rm\s+-rf", r"--delete", r"--force-rm"]
    for pat in blocked_patterns:
        if re.search(pat, command, re.IGNORECASE):
            return "Error: Command rejected — dangerous flag pattern detected."

    try:
        res = subprocess.run(
            cmd_parts,
            cwd=_workspace.WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = f"Exit Code: {res.returncode}\n"
        if res.stdout:
            output += f"Stdout:\n{res.stdout}\n"
        if res.stderr:
            output += f"Stderr:\n{res.stderr}\n"
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error running command: {e}"


def git_status(**kwargs) -> str:
    return run_command(command="git status")


def git_diff(**kwargs) -> str:
    path = kwargs.get("path")
    cmd = "git diff"
    if path:
        cmd = f"git diff -- {shlex.quote(path)}"
    return run_command(command=cmd)


def git_log(**kwargs) -> str:
    n = kwargs.get("n", 10)
    return run_command(command=f"git log --oneline -n {n}")


def get_diagnostics(**kwargs) -> str:
    path = kwargs.get("path")
    abs_path = get_absolute_path(path) if path else _workspace.WORKSPACE_ROOT

    if path and not is_safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    if path and not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."

    try:
        if path and os.path.isfile(abs_path):
            res = subprocess.run(
                ["python", "-m", "py_compile", abs_path],
                capture_output=True, text=True, timeout=30
            )
            if res.returncode == 0:
                return f"No compilation errors in '{path}'."
            return f"Compilation errors:\n{res.stderr}"

        res = subprocess.run(
            ["ruff", "check", "--output-format=text", abs_path if path else "."],
            cwd=_workspace.WORKSPACE_ROOT,
            capture_output=True, text=True, timeout=60
        )
        output = ""
        if res.stdout:
            output += res.stdout
        if res.stderr:
            output += res.stderr
        if not output.strip():
            return "No lint issues found."
        return output
    except FileNotFoundError:
        return "Error: 'ruff' not installed. Install with: pip install ruff"
    except Exception as e:
        return f"Error running diagnostics: {e}"


def run_tests(**kwargs) -> str:
    test_path = kwargs.get("test_path")
    cmd = "pytest"
    if test_path:
        cmd = f"pytest {shlex.quote(test_path)}"
    return run_command(command=cmd)


def done(**kwargs) -> str:
    summary = kwargs.get("summary", "Task completed.")
    return f"RESOLVED: {summary}"


_TOOL_REGISTRY = {
    "read_file": read_file,
    "create_file": create_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "multi_replace": multi_replace,
    "delete_file": delete_file,
    "list_directory": list_directory,
    "search_files": search_files,
    "run_command": run_command,
    "git_status": git_status,
    "git_diff": git_diff,
    "git_log": git_log,
    "get_diagnostics": get_diagnostics,
    "run_tests": run_tests,
    "done": done,
}


def execute_tool(name: str, arguments: dict) -> str:
    fn = _TOOL_REGISTRY.get(name)
    if not fn:
        return f"Error: Unknown tool '{name}'. Available tools: {', '.join(sorted(_TOOL_REGISTRY))}"
    try:
        return fn(**arguments)
    except TypeError as e:
        return f"Error: Invalid arguments for '{name}': {e}"
    except Exception as e:
        return f"Error executing tool '{name}': {e}"


TOOLS_SCHEMA = [
    {
        "name": "read_file",
        "description": "Read contents of a file. Supports optional line range.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace file path"},
                "start_line": {"type": "integer", "description": "First line to read (1-indexed)"},
                "end_line": {"type": "integer", "description": "Last line to read (inclusive)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file. Fails if file already exists. Creates parent directories.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace file path"},
                "content": {"type": "string", "description": "File contents"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite content in a file. Creates file if it doesn't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace file path"},
                "content": {"type": "string", "description": "Full text contents to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Surgical text replacement in a file. Replaces exact old_text with new_text.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace file path"},
                "old_text": {"type": "string", "description": "Exact text to find and replace"},
                "new_text": {"type": "string", "description": "Replacement text"}
            },
            "required": ["path", "old_text", "new_text"]
        }
    },
    {
        "name": "multi_replace",
        "description": "Apply multiple non-contiguous text replacements to a file in one operation. Use when you need to edit several different parts of a file at once.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace file path"},
                "replacements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_text": {"type": "string", "description": "Exact text to find"},
                            "new_text": {"type": "string", "description": "Replacement text"}
                        }
                    },
                    "description": "List of {old_text, new_text} replacement pairs"
                }
            },
            "required": ["path", "replacements"]
        }
    },
    {
        "name": "delete_file",
        "description": "Delete a file. Does not delete directories.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace file path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": "List contents of a directory with type and size info.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative workspace directory path"}
            },
            "required": []
        }
    },
    {
        "name": "search_files",
        "description": "Search file contents using regex. Returns matching lines with file:line format. Max 50 results.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory to search in (default: workspace root)"},
                "include": {"type": "string", "description": "File glob pattern to include (default: all files)"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "run_command",
        "description": "Run a shell command with security checks. Output is captured and returned.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 60)"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "git_status",
        "description": "Run git status in the workspace.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "git_diff",
        "description": "Run git diff. Optionally diff a specific file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Optional file path to diff"}
            },
            "required": []
        }
    },
    {
        "name": "git_log",
        "description": "Show recent git log entries.",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Number of log entries (default: 10)"}
            },
            "required": []
        }
    },
    {
        "name": "get_diagnostics",
        "description": "Run lint/type diagnostics on a file or directory using py_compile or ruff.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory to check (default: entire workspace)"}
            },
            "required": []
        }
    },
    {
        "name": "run_tests",
        "description": "Run pytest on the workspace or a specific test path.",
        "parameters": {
            "type": "object",
            "properties": {
                "test_path": {"type": "string", "description": "Specific test file or directory"}
            },
            "required": []
        }
    },
    {
        "name": "done",
        "description": "Signal task completion with a summary message.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Summary of what was accomplished"}
            },
            "required": ["summary"]
        }
    }
]
