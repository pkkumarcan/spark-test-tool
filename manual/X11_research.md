---
chapter_id: X11
title: "Research Workflow"
layer: "Planning"
status: "implemented"
purpose: "Collect facts, sources, and notes for script accuracy using web search and local LLMs"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "20m"
inputs:
  - "Research topic/prompt"
outputs:
  - "Markdown research report"
  - "Source URLs"
qc_gates:
  - "Report generated with citations"
  - "At least 3 sources found"
default_tools:
  primary: "research_agent.py (DuckDuckGo + Ollama)"
  fallback: "Manual web search"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X11"
  run: "run_X11"
  score: "score_X11"
  retry: "retry_X11"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X11 — Research Workflow

## Chapter Card
**Chapter:** `X11 — Research Workflow`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Collect facts, sources, and notes for script accuracy using web search and local LLMs.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **Endpoint:** `POST /api/research/generate`
- **File:** `app/backends/research_agent.py` (421 lines)
- **Search Providers:** DuckDuckGo (primary), Tavily, Google CSE, SearXNG, Yahoo, Wikipedia
- **LLM:** Ollama (qwen3:14b or qwen3:8b)

**Quality Gates:**
- Gate 1: Report generated with citations
- Gate 2: At least 3 sources found and summarized

---

## 1) Quickstart (Golden Path)

### Goal
Generate a research report on a topic using web search and LLM summarization.

### When to run
- Before script writing (X13)
- When fact-checking content
- For deep topic exploration

### Golden Path Steps
1) **Send research request**:
   ```bash
   curl -X POST http://localhost:5050/api/research/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "quantum computing trends 2026"}'
   ```
   Expected: Job ID returned with poll URL

2) **Poll for completion**:
   ```bash
   curl http://localhost:5050/api/jobs/{job_id}
   ```
   Expected: Status changes from "pending" to "completed"

3) **Retrieve report**:
   - Report returned in job result
   - Contains markdown-formatted research with source URLs

### Done looks like
- [ ] Research report generated
- [ ] At least 3 sources cited
- [ ] Report is factually accurate
- [ ] Sources are accessible

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Research query | `prompt` field | Topic to research |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Search depth | `depth` field | "standard" or "deep" |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Research report | Job result | Markdown with citations |
| Source URLs | Embedded in report | Links to original sources |

### Definition of Done (DoD)
Report generated + sources cited + facts verifiable.

---

## 3) Config & Standards

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `TAVILY_API_KEY` | None | Tavily search API key (optional) |
| `SEARXNG_URL` | None | SearXNG instance URL (optional) |
| `GOOGLE_API_KEY` | None | Google Custom Search API key (optional) |
| `GOOGLE_CSE_ID` | None | Google Custom Search Engine ID (optional) |

### Search Provider Fallback Chain
1. Tavily (if API key provided)
2. Google Custom Search (if API key + CSE ID provided)
3. SearXNG (if URL provided)
4. DuckDuckGo Default
5. DuckDuckGo HTML
6. DuckDuckGo Lite
7. Yahoo Search
8. Wikipedia OpenSearch

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool:** `research_agent.py`
  - **Search:** DuckDuckGo (no API key required)
  - **LLM:** Ollama (qwen3:14b preferred, qwen3:8b fallback)
  - **Scraping:** httpx with HTML cleaning
  - **Strengths:** Multi-provider fallback, async parallel scraping
  - **Weaknesses:** Rate limits on free search APIs

### Alternatives (approved)
- **Tavily API** — Higher quality results, requires API key
- **Google Custom Search** — Best results, requires API key + CSE ID

---

## 5) Procedure (Operator Steps)

### Step 1 — Formulate Search Queries
- **Inputs:** User research topic
- **Action:** LLM generates 2 optimized search queries
- **Expected output:** JSON list of search query strings
- **Common failures:** LLM returns invalid JSON
- **Fix:** Use raw topic as search query

### Step 2 — Execute Web Search
- **Inputs:** Search queries
- **Action:** Search with configured providers (fallback chain)
- **Expected output:** List of relevant URLs
- **Common failures:** All providers rate-limited
- **Fix:** Wait and retry, or use different query

### Step 3 — Scrape Page Contents
- **Inputs:** URLs from search
- **Action:** Fetch and extract text from top 5 pages
- **Expected output:** Cleaned text content from each page
- **Common failures:** Page not accessible, JavaScript-heavy
- **Fix:** Skip failed pages, use remaining content

### Step 4 — Summarize Sources
- **Inputs:** Page contents
- **Action:** LLM summarizes each page to key facts
- **Expected output:** Bullet-point summaries per source
- **Common failures:** LLM timeout
- **Fix:** Reduce content length, use faster model

### Step 5 — Synthesize Report
- **Inputs:** All summaries
- **Action:** LLM writes comprehensive research report
- **Expected output:** Markdown report with headers, bullets, bibliography
- **Common failures:** Report too generic
- **Fix:** Add more specific instructions in query

---

## 6) Agent Interface (Automation Hooks)

### Functions
- `validate_X11(job_id) -> {pass: bool, reasons:[], warnings:[]}`
- `run_X11(job_id, profile) -> {status, outputs[], timings}`
- `score_X11(job_id) -> {quality:1-10, speed:1-10, notes}`
- `retry_X11(job_id, strategy) -> {attempts, best_run_id}`

### API Endpoints
- `POST /api/research/generate` — Start research job
- `GET /api/jobs/{job_id}` — Poll job status
- `DELETE /api/jobs/{job_id}` — Cancel job

---

## 7) Smoke Tests

### Smoke Test A — Minimal (fast)
- **Goal:** Prove research pipeline works
- **Input:** "What is Python?"
- **Steps:** Send request, poll until complete
- **Pass criteria:** Report generated with at least 1 source
- **If fails:** Check Ollama running, check network

### Smoke Test B — Standard (realistic)
- **Goal:** Test multi-source research
- **Input:** "Latest advances in quantum computing 2026"
- **Steps:** Send request, poll until complete
- **Pass criteria:** Report with 3+ sources, factually accurate
- **If fails:** Check search provider availability

---

## 8) Troubleshooting

### Issue 1 — "No search results found"
- **Cause:** All search providers rate-limited or unreachable
- **Fix:** Wait 5 minutes, try different query
- **Prevention:** Use Tavily API for production

### Issue 2 — "LLM summarization failed"
- **Cause:** Ollama overloaded or model not loaded
- **Fix:** Check `ollama list`, restart if needed
- **Prevention:** Monitor GPU usage

### Issue 3 — "Report too generic"
- **Cause:** Search query too broad
- **Fix:** Use more specific query with keywords
- **Prevention:** Guide user to be specific

---

## 9) Change Log

- 2026-06-15 — Initial implementation with actual codebase content
- 2025-12-24 — Original template created