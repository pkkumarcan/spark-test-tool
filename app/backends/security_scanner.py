import os
import re
import subprocess
import json
import logging

logger = logging.getLogger("spark.backend.security")

_default_workspace = "/app" if os.path.exists("/app/app/main.py") else os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", _default_workspace)
BUMBLEBEE_PATH = os.getenv("BUMBLEBEE_PATH", "bumblebee")

def run_project_scan(target_path: str = WORKSPACE_ROOT) -> dict:
    """
    Executes the Bumblebee Go binary tool against the workspace to audit dependencies.
    Falls back to a static python dependency audit if the binary is offline.
    """
    # 1. Attempt to trigger the Perplexity Bumblebee binary
    try:
        # Run Bumblebee CLI scan
        res = subprocess.run(
            [BUMBLEBEE_PATH, "scan", "--profile", "project", "--path", target_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            try:
                # Parse structured NDJSON/JSON results
                scan_data = json.loads(res.stdout)
                vulnerabilities = scan_data.get("vulnerabilities", [])
                if vulnerabilities:
                    return {
                        "status": "alert",
                        "scanner": "bumblebee-cli",
                        "alerts": [v.get("message") for v in vulnerabilities]
                    }
                return {"status": "clean", "scanner": "bumblebee-cli"}
            except Exception:
                # Fallback to checking return code/output flags
                if "MALICIOUS" in res.stdout:
                    return {"status": "alert", "scanner": "bumblebee-cli", "alerts": ["Bumblebee CLI flagged dependency threat."]}
                return {"status": "clean", "scanner": "bumblebee-cli"}
    except Exception as e:
        logger.debug(f"Bumblebee CLI not found or failed: {e}. Running local python dependency verification.")

    # 2. pip-audit fallback — real CVE scanner (install: pip install pip-audit)
    req_file = os.path.join(target_path, "requirements.txt")
    if os.path.exists(req_file):
        try:
            res = subprocess.run(
                ["pip-audit", "--requirement", req_file, "--format", "json", "--no-deps"],
                capture_output=True, text=True, timeout=60
            )
            if res.returncode == 0:
                try:
                    data = json.loads(res.stdout)
                    vulns = data.get("vulnerabilities", [])
                    if vulns:
                        return {
                            "status": "alert",
                            "scanner": "pip-audit",
                            "alerts": [f"{v.get('name')} {v.get('version')}: {v.get('description', 'vulnerability detected')}" for v in vulns]
                        }
                    return {"status": "clean", "scanner": "pip-audit"}
                except json.JSONDecodeError:
                    pass
        except FileNotFoundError:
            logger.debug("pip-audit not found. Install with: pip install pip-audit")
        except subprocess.TimeoutExpired:
            logger.warning("pip-audit timed out.")
        except Exception as e:
            logger.debug(f"pip-audit failed: {e}")

    # 3. Last resort: static signature check (very limited — only catches known evil package names)
    alerts = []
    if os.path.exists(req_file):
        try:
            with open(req_file, "r") as f:
                content = f.read()
            known_malicious = [
                "pep517-malicious", "request-logger-malicious",
                "discord-tokens-stealer", "browser-cookies-stealer",
                "colourama",  # typosquat of colorama
                "python-binance-stealer",
            ]
            for entry in known_malicious:
                if entry in content:
                    alerts.append(f"Supply chain warning: known malicious package '{entry}' found in requirements.txt")
        except Exception as ex:
            logger.error(f"Failed to read requirements.txt during security audit: {ex}")

    return {
        "status": "clean" if not alerts else "alert",
        "scanner": "static-signature",
        "alerts": alerts
    }

def audit_command_string(command: str) -> dict:
    """
    Analyzes shell command strings for pipeline safety violations, blocking code execution attacks.
    """
    violations = []
    
    # Static pattern matching for code execution vulnerabilities
    rules = [
        (r"curl\s+.*\s*\|\s*bash", "Piping curl directly to bash"),
        (r"wget\s+.*\s*\|\s*bash", "Piping wget directly to bash"),
        (r"base64\s+-d\s*\|\s*bash", "Decoding obfuscated base64 payload to bash"),
        (r"/etc/passwd", "Unauthorized system password database read"),
        (r"/etc/shadow", "Unauthorized system credential read"),
        (r"curl\s+.*http://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", "Direct external IP connection bypass attempt")
    ]
    
    for regex, reason in rules:
        if re.search(regex, command, re.IGNORECASE):
            violations.append(reason)
            
    return {
        "status": "clean" if not violations else "alert",
        "violations": violations
    }
