"""
utils.py — Shared utility functions for Spark backends

Centralises common logic to avoid duplication across backend modules.
"""
import logging
import httpx

logger = logging.getLogger("spark.backend.utils")


async def resolve_best_model(
    ollama_url: str,
    preferred: list[str] | None = None,
    default: str = "qwen3:8b"
) -> str:
    """
    Resolve the best available Ollama model from a preference list.

    Queries the Ollama /api/tags endpoint and returns the first model from
    the preferred list that is actually available. Falls back to the first
    available model, then to the default string if Ollama is unreachable.

    Args:
        ollama_url: Base URL of the Ollama API (e.g. "http://localhost:11434")
        preferred: Ordered list of model names to try, most-preferred first.
                   Defaults to ["qwen3:14b", "qwen3:8b"].
        default: Fallback model name if nothing is available.

    Returns:
        The resolved model name string.

    Example:
        model = await resolve_best_model(ollama_url, preferred=["qwen3:14b", "qwen3:8b"])
    """
    if preferred is None:
        preferred = ["qwen3:14b", "qwen3:8b"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                available = [m["name"] for m in r.json().get("models", [])]
                # Return first preferred model that is actually installed
                for p in preferred:
                    if p in available:
                        logger.debug(f"Model resolved: {p}")
                        return p
                # Fall back to whatever is first in the list
                if available:
                    logger.debug(f"No preferred model available, using first: {available[0]}")
                    return available[0]
    except Exception as e:
        logger.warning(f"Could not query Ollama model list: {e}. Using default: {default}")

    return default


def get_system_specs() -> dict:
    """
    Retrieve real-time hardware specifications (CPU, RAM, GPUs) on the host machine.
    """
    import os
    specs = {}
    
    # 1. CPU cores
    try:
        specs["cpu_cores"] = os.cpu_count()
    except Exception:
        specs["cpu_cores"] = "Unknown"
        
    # 2. System RAM (Memory)
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        mem_total = 0
        mem_free = 0
        for line in lines:
            if "MemTotal" in line:
                mem_total = int(line.split()[1]) // 1024  # MB
            elif "MemAvailable" in line or "MemFree" in line:
                mem_free = int(line.split()[1]) // 1024  # MB
        specs["ram_total_gb"] = round(mem_total / 1024, 1)
        specs["ram_free_gb"] = round(mem_free / 1024, 1)
    except Exception:
        specs["ram_total_gb"] = "Unknown"
        specs["ram_free_gb"] = "Unknown"

    # 3. GPU (nvidia-smi)
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append(f"GPU {parts[0]}: {parts[1]} ({parts[3]} MB / {parts[2]} MB VRAM)")
            specs["gpus"] = gpus
        else:
            specs["gpus"] = ["None or unavailable"]
    except Exception:
        specs["gpus"] = ["None or unavailable"]

    return specs

