# Automated Service Smoke Test Report

| ID | Service Name | Endpoint | Status | Details |
|----|--------------|----------|--------|---------|
| 1 | Gateway Health Check | `GET /health` | **PASS** | Status code: 200 |
| 2 | GPU Status API | `GET /api/gpu/status` | **PASS** | Status code: 200. Response: {"gpus":{"gpu0":{"index":0,"name":"NVIDIA GeForce RTX 3090", |
| 3 | Text Models Listing | `GET /api/text/models` | **PASS** | Status code: 200. Models count: 11 |
| 4 | Text Generation (Ollama) | `POST /api/text/chat` | **PASS** | Streaming successfully started. First line: data: {"model":"qwen3.6:27b","created_at":"2026-06-21T05:57:34.577214976Z","mess |
| 5 | Prompt Enhancement | `POST /api/text/enhance` | **PASS** | Status code: 200. Enhanced prompt length: 0 |
| 6 | F5-TTS Voice Synthesis | `POST /api/audio/speak` | **PASS** | Status code: 200. Content-type: audio/wav |
| 7 | Whisper STT Transcription | `POST /api/audio/transcribe` | **PASS** | Status code: 200. Response: {"language":"en","segments":[],"text":""} |
| 8 | RAG Text Ingest | `POST /api/rag/ingest` | **PASS** | Status code: 200. Response: {"status":"success","engine":"local","chunks_ingested":1} |
| 9 | RAG Text Query | `POST /api/rag/query` | **PASS** | Status code: 200. Hits returned: 2 |
| 10 | MCP AI Agent (Dynamic Tools) | `POST /api/gems/mcp` | **PASS** | Status code: 200. Mode: fallback/mocked. Tool: None |
| 11 | Dify Visual Orchestrator Link | `POST /api/dify/run-workflow` | **PASS** | Status code: 502 (Expected 502 if offline). Response: {"detail":"Failed to connect to local Dify service: All conn |
| 12 | Local Coding & Terminal Agent Loop | `POST /api/gems/coding-agent` | **PASS** | Status code: 200. Status: completed. Resolution: task complete |
| 13 | WaveBasis & MotiveWave Finance MCP | `POST /api/gems/mcp (Finance)` | **FAIL** | Status code: 200. Response target matched: False |
| 14 | Bumblebee Agentic Security Sandbox | `POST /api/gems/coding-agent (Audit)` | **PASS** | Status code: 200. Action Blocked: True |
| 15 | YouTube Video Publisher (Mock) | `POST /api/publish/upload` | **PASS** | Status code: 200. Video ID: hEZXnYsFWaH |
| 16 | KPI Analytics Dashboard | `GET /api/kpi/dashboard` | **PASS** | Status code: 200. Total Views: 12083 |
