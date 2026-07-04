"""Shared workspace configuration used by coding_agent and coding_tools."""
import os

_default_workspace = "/app" if os.path.exists("/app/app/main.py") else os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", _default_workspace)

ALLOWED_COMMANDS = {
    # Python
    "python", "python3", "pip", "pytest", "ruff", "black", "mypy", "py_compile",
    # JS/TS
    "node", "npm", "npx", "yarn", "pnpm", "bun", "vite", "tsc", "eslint", "prettier",
    # Rust
    "cargo", "rustc",
    # Go
    "go",
    # Shell/Utils
    "ls", "cat", "echo", "head", "tail", "wc", "find", "grep", "sed", "awk",
    "sort", "uniq", "diff", "tee", "xargs", "mkdir", "cp", "mv", "touch",
    # Git
    "git",
    # Docker
    "docker", "docker-compose",
    # System
    "which", "env", "date", "uname",
}

def is_safe_path(path: str) -> bool:
    abs_path = os.path.realpath(os.path.join(WORKSPACE_ROOT, path))
    return abs_path.startswith(os.path.realpath(WORKSPACE_ROOT))

def get_absolute_path(path: str) -> str:
    return os.path.realpath(os.path.join(WORKSPACE_ROOT, path))
