# Spark Distributed AI Network - Master RAG Manifest

This document serves as the single, comprehensive master hardware, software, and topology manifest for the Spark Distributed AI Network. It is designed to be loaded into RAG (Retrieval-Augmented Generation) systems to provide context for intent routing, hardware constraints, API endpoints, and driver optimizations.

---

## 1. Network Node Registry & Access Mappings

The Spark network consists of 5 nodes running a hybrid Linux (Ubuntu) and Windows architecture. IPs are reserved statically on the local router gateway (`10.0.0.1`).

| Node Alias | Hostname | Role / Operating System | MAC Address | IP Address | SSH Username | GPU Acceleration |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NodeA** | `NodeA` | Ubuntu Coordinator / Ubuntu 26.04 | `34:5A:60:49:5D:9C` | `10.0.0.193` | `pkkumar` | Yes (Dual-GPU: RTX 3090, RTX 3060) |
| **NodeB** | `GPU-PC` | Windows AI Worker / Windows 11 Pro | `8C:55:4A:AA:0D:E8` | `10.0.0.162` | `StudioAdmin` | Yes (Dual-GPU: RTX 3060 Ti, RTX 3060) |
| **NodeC** | `PK-HP` | Host PC / Windows 11 Pro | `4C:EB:BD:AC:52:4D` | `10.0.0.227` | `Prdp1` | Yes (Low-power: MX230) |
| **NodeD** | `NodeD` | Ubuntu VM (inside NodeC) / Ubuntu | `00:15:5D:00:E3:01` | `10.0.0.208` | `prdp1200` | No (CPU / Soft-rendering only) |
| **NodeE** | `BOOK3-PK` | Control PC & Dashboard / Windows 11 | `64:6E:E0:F8:41:75` | `10.0.0.244` | `User` | Yes (Single GPU: GTX 1660 Super) |

---

## 2. Hardware Profiles & Resource Allocations

### NodeA — Ubuntu Linux Coordinator
* **Primary Role:** Heavy Inference, ComfyUI visual generation, and vector database host.
* **CPU:** AMD Ryzen 9 5950X (16 Cores / 32 Threads)
* **System RAM:** 128 GiB DDR4
* **Storage:** 2.0 TB NVMe Gen4 SSD
* **GPUs:**
  * **GPU 0 (Primary):** NVIDIA GeForce RTX 3090 (24 GB GDDR6X VRAM) — Used for ComfyUI high-resolution visual/video generation pipelines.
  * **GPU 1 (Secondary):** NVIDIA GeForce RTX 3060 (12 GB GDDR6 VRAM) — Dedicated to ComfyUI Audio/Music workflows.

### NodeB — Windows 11 AI Worker
* **Primary Role:** Text LLM serving, vocal synthesis (TTS), and audio transcription (STT).
* **CPU:** AMD Ryzen 9 5900X (12 Cores / 24 Threads)
* **System RAM:** 32 GiB DDR4
* **GPUs:**
  * **GPU 0 (Primary):** NVIDIA GeForce RTX 3060 Ti (8 GB GDDR6 VRAM) — Runs Ollama for Text LLM serving and Whisper for STT transcription.
  * **GPU 1 (Secondary):** NVIDIA GeForce RTX 3060 (12 GB GDDR6 VRAM) — Dedicated to voice synthesis (F5-TTS).

### NodeC — HP Pavilion Host
* **Primary Role:** Hyper-V virtualization host for Node D.
* **CPU:** Intel Core i7-9700T (8 Cores / 8 Threads)
* **System RAM:** 16 GiB DDR4
* **GPU:** NVIDIA GeForce MX230 (2 GB GDDR5 VRAM) — Minimal acceleration.

### NodeD — Ubuntu Hyper-V Guest VM
* **Primary Role:** Local Assistant VM and sandboxed tests.
* **CPU:** 4 vCPUs (Intel Core i7-9700T allocation)
* **System RAM:** 3.3 GiB RAM (~4 GB dynamic allocated)
* **GPU:** None (CPU execution only).

### NodeE — Surface Book 3 (Control PC)
* **Primary Role:** Development console, central Git repository controller, and Nodes Manager backend server host.
* **CPU:** Intel Core i7-1065G7 (4 Cores / 8 Threads)
* **System RAM:** 32 GiB LPDDR4x
* **GPU:** NVIDIA GeForce GTX 1660 Super Max-Q (6 GB GDDR6 VRAM) — Local testing.

---

## 3. Network Service Ports & Endpoints

Use these endpoints to query the live services on each node:

* **Node A (Ubuntu Coordinator):**
  * Ollama LLM API: `http://10.0.0.193:11435`
  * ComfyUI Visual Engine: `http://10.0.0.193:8188`
  * SearXNG Search Engine: `http://10.0.0.193:8888`
  * Gateway Application (Test Tool): `http://10.0.0.193:5050`
  * Whisper STT (Container): `http://10.0.0.193:8010` (mapped to `9000` internally)
  * F5-TTS Vocal Engine: `http://10.0.0.193:8020` (mapped to `8000` internally)
* **Node B (Windows Worker):**
  * Ollama LLM API: `http://10.0.0.162:11434`
  * Whisper STT (Container): `http://10.0.0.162:8010` (mapped to `9000` internally)
  * F5-TTS Vocal Engine: `http://10.0.0.162:8020` (mapped to `8000` internally)
  * Topaz Video/Photo AI Service: `http://10.0.0.162:5060`
  * Middleware API: `http://10.0.0.162:8000`
* **Node E (Control PC):**
  * Central Nodes Manager API Backend: `http://10.0.0.244:8086`
  * Dashboard GUI: `file:///c:/projects/local tools/nodes_manager.html`

---

## 4. NVIDIA GPU Studio Driver Updates (June 2026 Release)

The network GPUs run the June 2026 NVIDIA Studio/Production Driver branch (Windows **v610.62**, Linux **v610.x / v595.x**).

### Efficiency & Performance Impacts:
1. **Multi-GPU Coordination (llama.cpp & Ollama):**
   * This release optimizes weights splitting and PCIe bus synchronization across dual-GPU configurations (Node A and Node B).
   * **Impact:** High token generation speeds (TPS) and lower CPU latency when running models split across local GPUs.
2. **VRAM Page Migration & Virtualization (ComfyUI):**
   * Improves page migration when swapping multi-gigabyte models (e.g., Flux, SDXL, ControlNet) between Host RAM and GPU VRAM.
   * **Impact:** Eliminates Out-of-Memory (OOM) crashes during concurrent visual rendering passes on Node A.
3. **Power Efficiency:**
   * Optimized clock management during idle and low-load states reduces thermal load and power consumption.

### Performance Maximization Guidelines:
* **HAGS (Hardware-Accelerated GPU Scheduling):** Must be enabled on Windows nodes (Node B, Node C, Node E) under Windows Graphics Settings to optimize VRAM virtualization.
* **CUDA Graphs:** Used in PyTorch on Node A/B to construct static execution graphs, bypassing driver latency.

---

## 5. Intelligent Workload Routing Strategy

For media production (YouTube and social media asset creation), tasks should be distributed as follows to utilize all CPUs/GPUs in harmony:

```
[User Request] ──> [Spark Orchestrator (Node A)]
                        │
      ┌─────────────────┼──────────────────┐
      ▼                 ▼                  ▼
 [Visual Tasks]   [Text & Speech]    [Search & VM]
  (ComfyUI, Flux)  (Ollama, Whisper)   (SearXNG)
      │                 │                  │
  Node A (3090)     Node B (3060Ti)    Node A (CPU)
  - VRAM: 24GB      - VRAM: 8GB + 12GB - Port: 8888
```

1. **Heavy Visuals (Image/Video):** Route to **Node A** to utilize the 24 GB GDDR6X VRAM on the RTX 3090.
2. **Audio/Music Generation:** Route to **Node A (Secondary GPU)** to isolate the 12 GB RTX 3060, leaving the 3090 fully dedicated to visual pipelines.
3. **Text LLM Chat & RAG:** Route to **Node B** to run Ollama on the RTX 3060 Ti (8GB), avoiding VRAM conflicts on Node A.
4. **Vocal Synthesis (TTS):** Route to **Node B (Secondary GPU)** to run F5-TTS on the RTX 3060 (12GB) to achieve fast real-time audio generation.
5. **Speech-to-Text (STT):** Route to **Node B** to utilize the faster CPU/GPU bus for transcription.
6. **Search & Crawling:** Route to **Node A** locally to query the SearXNG search engine (`http://localhost:8888`).
7. **Topaz Video/Photo AI Processing:** Route to **Node B** (`http://10.0.0.162:5060`) to leverage Windows-native GPU acceleration and prevent overloading Node A's visual generation pipelines.
