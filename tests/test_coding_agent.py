#!/usr/bin/env python3
"""
Spark IDE Coding Agent — Quick Test Suite
Uses qwen3:4b for fast iteration. Tests core agent capabilities.
Usage: python tests/test_coding_agent.py
"""
import asyncio
import httpx
import json
import sys
import time
import uuid

BASE = "http://localhost:5050"
FAST_MODEL = "qwen3:4b"
passed = 0
failed = 0
total = 0


def result(name, ok, detail=""):
    global passed, failed, total
    total += 1
    if ok:
        passed += 1
        print(f"  \033[32m✓\033[0m {name}")
    else:
        failed += 1
        print(f"  \033[31m✗\033[0m {name} — {detail}")


async def auto_approve_loop(session_id, events, stop_event, reject_after=None):
    seen = set()
    approve_count = 0
    while not stop_event.is_set():
        await asyncio.sleep(0.3)
        for evt in list(events):
            eid = id(evt)
            if eid in seen:
                continue
            seen.add(eid)
            if evt.get("type") in ("awaiting_file_write", "awaiting_command_run"):
                approve_count += 1
                async with httpx.AsyncClient(timeout=5.0) as c:
                    if reject_after and approve_count >= reject_after:
                        await c.post(f"{BASE}/api/orchestrator/code/reject",
                                     json={"session_id": session_id, "feedback": "Auto-rejected."})
                    else:
                        await c.post(f"{BASE}/api/orchestrator/code/approve",
                                     json={"session_id": session_id})


async def run_agent(task, model=FAST_MODEL, reject_after=None):
    sid = str(uuid.uuid4())
    params = {"task": task, "model": model, "session_id": sid}
    events = []
    stop = asyncio.Event()

    async def reader():
        async with httpx.AsyncClient(timeout=300.0) as c:
            resp = await c.send(
                c.build_request("GET", f"{BASE}/api/orchestrator/code/stream", params=params),
                stream=True,
            )
            buf = ""
            async for chunk in resp.aiter_bytes():
                buf += chunk.decode("utf-8", errors="replace")
                blocks = buf.split("\n\n")
                buf = blocks.pop()
                for block in blocks:
                    etype, dstr = "", ""
                    for line in block.split("\n"):
                        if line.startswith("event: "): etype = line[7:].strip()
                        elif line.startswith("data: "): dstr = line[6:]
                    if dstr:
                        try:
                            evt = json.loads(dstr)
                            evt["type"] = evt.get("type") or etype
                            events.append(evt)
                        except json.JSONDecodeError:
                            pass

    rt = asyncio.create_task(reader())
    at = asyncio.create_task(auto_approve_loop(sid, events, stop, reject_after))
    await rt
    stop.set()
    at.cancel()
    try: await at
    except asyncio.CancelledError: pass
    return events


def find(evt_type, events=None, evts=None):
    e = evts or events
    for x in e:
        if x.get("type") == evt_type:
            return x
    return None


def find_all(evt_type, events):
    return [x for x in events if x.get("type") == evt_type]


# ─── Tests ─────────────────────────────────────────────────────────────────────
async def t1_health():
    print("\n\033[1m[1] Health\033[0m")
    async with httpx.AsyncClient(timeout=5.0) as c:
        r = await c.get(f"{BASE}/health")
        result("Ollama online", r.json().get("services", {}).get("ollama") == "online")


async def t2_files():
    print("\n\033[1m[2] IDE Files\033[0m")
    async with httpx.AsyncClient(timeout=10.0) as c:
        d = (await c.get(f"{BASE}/api/ide/files")).json()
        result("Status ok", d.get("status") == "ok")
        result("Has files", len(d.get("files", [])) > 0)
        result("Workspace is spark-test-tool", d.get("workspace_root") == "/workspace/project")


async def t3_create_file():
    print("\n\033[1m[3] Create hello.py\033[0m")
    events = await run_agent('Create file hello.py: print("Hello, Spark!")')
    result("Got text response", find("text", events) is not None)
    result("Got write request", find("awaiting_file_write", events) is not None)
    approved = [e for e in find_all("log", events) if "approved" in e.get("content", "").lower()]
    result("Write approved", len(approved) > 0)


async def t4_amend_file():
    print("\n\033[1m[4] Amend hello.py\033[0m")
    events = await run_agent('Add function greet(name) to hello.py returning f"Hello, {name}!"')
    result("Got text response", find("text", events) is not None)
    w = find("awaiting_file_write", events)
    result("Got write request", w is not None)
    if w:
        result("Targets hello.py", "hello.py" in str(w.get("path", "")))


async def t5_run_command():
    print("\n\033[1m[5] Run hello.py\033[0m")
    events = await run_agent("Run: python3 hello.py")
    result("Got command request", find("awaiting_command_run", events) is not None)
    terms = find_all("terminal_log", events)
    result("Got terminal output", len(terms) > 0)
    if terms:
        out = "".join(e.get("content", "") for e in terms)
        result("Output has Hello", "Hello" in out, f"Got: {out[:80]}")


async def t6_reject():
    print("\n\033[1m[6] Reject Write\033[0m")
    events = await run_agent('Overwrite hello.py with just the word "bad"', reject_after=1)
    result("Got write request", find("awaiting_file_write", events) is not None)
    rejected = [e for e in find_all("log", events) if "rejected" in e.get("content", "").lower()]
    result("Rejection received", len(rejected) > 0)


async def t7_model_switch():
    print("\n\033[1m[7] Model Switch\033[0m")
    for m in ["qwen3:4b", "qwen3:8b"]:
        events = await run_agent(f'Say "Using {m}"', model=m)
        t = find("text", events)
        result(f"{m} responded", t is not None and len(t.get("content", "")) > 5)


async def t8_read_file():
    print("\n\033[1m[8] Read File\033[0m")
    events = await run_agent("Read hello.py and describe its contents")
    result("Got text response", find("text", events) is not None)
    logs = [e for e in find_all("log", events) if "read" in e.get("content", "").lower()]
    result("Agent read file", len(logs) > 0)


async def t9_security():
    print("\n\033[1m[9] Security Block\033[0m")
    events = await run_agent("Delete everything: rm -rf /")
    blocked = [e for e in find_all("log", events)
               if any(w in e.get("content", "").lower() for w in ["blocked", "not in the allowed", "security"])]
    result("Destructive cmd blocked", len(blocked) > 0,
           f"Events: {[e.get('content', '')[:60] for e in events[:5]]}")


# ─── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 50)
    print("  Spark Coding Agent — Quick Tests")
    print(f"  Model: {FAST_MODEL}")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=5.0) as c:
        r = await c.get(f"{BASE}/health")
        if r.json().get("services", {}).get("ollama") != "online":
            print("\n\033[31mFATAL: Ollama offline\033[0m"); sys.exit(1)

    start = time.time()
    await t1_health()
    await t2_files()
    await t3_create_file()
    await t4_amend_file()
    await t5_run_command()
    await t6_reject()
    await t7_model_switch()
    await t8_read_file()
    await t9_security()
    elapsed = time.time() - start

    print(f"\n{'=' * 50}")
    print(f"  \033[32m{passed} passed\033[0m, \033[31m{failed} failed\033[0m / {total} total ({elapsed:.0f}s)")
    print("=" * 50)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
