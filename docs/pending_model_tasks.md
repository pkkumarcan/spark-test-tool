# Pending Model Downloads & Setup Tasks

This file tracks the pending model downloads and environment setup tasks required to complete the Spark Media Factory installation for Node 1.

## 1. Agent System Integration Tasks (To be executed by the agent)
- [x] Add Qdrant Vector DB service to `docker-compose.yml`.
- [x] Add RAG ingest and query test cases to `run_smoke_tests.py` and verify end-to-end functionality.

---

## 2. Hugging Face Authentication (Required for ACE-Step XL)
- [x] Run `huggingface-cli login` and enter your HF token.
- [x] Accept terms on the [ACE-Step SFT Model Page](https://huggingface.co/ACE-Step/acestep-v15-xl-sft) and [ACE-Step Turbo Model Page](https://huggingface.co/ACE-Step/acestep-v15-xl-turbo).

---

## 3. ACE-Step Repo and XL Model Downloads
- [x] Clone the correct repository: `https://github.com/ace-step/ACE-Step-1.5.git`. (Downloaded at `/home/pkkumar/Ace-Step1.5/`)
- [x] Download `ACE-Step/acestep-v15-xl-sft` checkpoints.
- [x] Download `ACE-Step/acestep-v15-xl-turbo` checkpoints. (Verified at `/home/pkkumar/Ace-Step1.5/acestep-v15-turbo/`)
- [x] Download ACE-Step 1.5 Base model (Public). (Verified at `/home/pkkumar/spark-factory/models/ace-step-1.5-base`)

---

## 4. Wan 2.2 T2V A14B (MoE) Cinematic Model Download
- [ ] Download the GGUF weights from `LightX2V/LightX2V-GGUF` (specifically the `Q4_K_M` quant) to `/home/pkkumar/spark-factory/models/wan2.2-a14b-gguf`:
  ```bash
  huggingface-cli download LightX2V/LightX2V-GGUF --include 'Wan2.2-T2V-A14B*Q4_K_M*' --local-dir /home/pkkumar/spark-factory/models/wan2.2-a14b-gguf
  ```
- [ ] Download the companion VAE and text encoders:
  ```bash
  huggingface-cli download Wan-AI/Wan2.2-T2V-A14B wan_2.1_vae.safetensors --local-dir /home/pkkumar/spark-factory/models/vae
  huggingface-cli download Wan-AI/Wan2.2-T2V-A14B umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir /home/pkkumar/spark-factory/models/text_encoders
  ```

---

## 5. STAR Video SR (Optional/Non-blocking)
- [ ] Clone `https://github.com/NJU-PCALab/STAR.git` and download weights from the Google Drive links in the repository readme.
  ```bash
  git clone https://github.com/NJU-PCALab/STAR.git
  cd STAR && pip install -r requirements.txt
  ```

---

## 6. Workstation Node 2 (RTX 3060 12GB) Additional Pending Downloads
These are models required specifically for the 12GB GPU configuration that are not already available on the system:

- [x] **Ollama Text Models:**
  ```bash
  ollama pull qwen3:8b
  ollama pull qwen3:14b
  ```
- [x] **Wan 2.2 Video Models:**
  * **Wan 2.2 (5B) FP8:**
    ```bash
    huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors --local-dir /home/pkkumar/spark-factory/models/diffusion_models
    huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged split_files/vae/wan2.2_vae.safetensors --local-dir /home/pkkumar/spark-factory/models/vae
    huggingface-cli download Comfy-Org/Wan_2.2_ComfyUI_Repackaged split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir /home/pkkumar/spark-factory/models/text_encoders
    ```
  * **Wan 2.2 (14B GGUF-Q4):**
    ```bash
    huggingface-cli download city96/Wan2.2-T2V-14B-gguf --include '*Q4_K_M*' --local-dir /home/pkkumar/spark-factory/models/wan2.2-14b-gguf
    ```
- [ ] **FLUX & SDXL Image Models:**
  * **FLUX.1 Schnell (GGUF-Q4_K):**
    ```bash
    huggingface-cli download city96/FLUX.1-schnell-gguf --include '*Q4_K_M*' --local-dir /home/pkkumar/spark-factory/models/flux1-schnell-gguf
    huggingface-cli download comfyanonymous/flux_text_encoders t5xxl_fp8_e4m3fn.safetensors clip_l.safetensors --local-dir /home/pkkumar/spark-factory/models/clip
    ```
  * **Stable Diffusion XL 1.0:**
    ```bash
    huggingface-cli download stabilityai/stable-diffusion-xl-base-1.0 sd_xl_base_1.0.safetensors --local-dir /home/pkkumar/spark-factory/models/sdxl
    huggingface-cli download stabilityai/stable-diffusion-xl-base-1.0 sd_xl_refiner_1.0.safetensors --local-dir /home/pkkumar/spark-factory/models/sdxl
    ```
  * **FLUX.1 Dev (GGUF-Q8):**
    ```bash
    huggingface-cli download city96/FLUX.1-dev-gguf --include '*Q8_0*' --local-dir /home/pkkumar/spark-factory/models/flux1-dev-gguf
    huggingface-cli download comfyanonymous/flux_text_encoders t5xxl_fp8_e4m3fn.safetensors clip_l.safetensors --local-dir /home/pkkumar/spark-factory/models/clip
    ```
- [ ] **3D Asset Models:**
  * **Hunyuan3D-2mini:**
    ```bash
    huggingface-cli download tencent/Hunyuan3D-2mini --local-dir /home/pkkumar/spark-factory/models/hunyuan3d-2mini
    ```
  * **Hunyuan3D-2:**
    ```bash
    huggingface-cli download tencent/Hunyuan3D-2 --local-dir /home/pkkumar/spark-factory/models/hunyuan3d-2
    ```
