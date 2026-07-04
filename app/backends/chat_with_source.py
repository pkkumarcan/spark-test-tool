import os
import uuid
import logging
import httpx
import shutil
import tempfile
import subprocess
from fastapi import Request, HTTPException
from app.backends import rag
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger("spark.backend.chat_with_source")

async def ingest_source(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    source_type = body.get("type", "").strip().lower()
    payload = body.get("payload", "").strip()

    if not source_type or not payload:
        raise HTTPException(status_code=400, detail="Both 'type' and 'payload' are required")

    source_id = f"src_{uuid.uuid4().hex[:8]}"
    text_content = ""
    metadata = {
        "source_id": source_id,
        "source_type": source_type
    }

    if source_type == "github":
        logger.info(f"Ingesting GitHub repo: {payload}")
        temp_dir = tempfile.mkdtemp()
        try:
            # Run git clone in temp directory
            cmd = ["git", "clone", "--depth", "1", payload, temp_dir]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if process.returncode != 0:
                raise Exception(f"Git clone failed: {process.stderr}")

            # Walk files
            file_contents = []
            allowed_extensions = {".py", ".js", ".html", ".css", ".md", ".txt", ".json", ".yaml", ".yml", ".sh"}
            total_size = 0
            max_size_bytes = 1024 * 1024 # 1MB limit for safety

            for root, dirs, files in os.walk(temp_dir):
                # Ignore git folder
                if ".git" in dirs:
                    dirs.remove(".git")
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in allowed_extensions:
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                if content.strip():
                                    rel_path = os.path.relpath(filepath, temp_dir)
                                    file_contents.append(f"--- File: {rel_path} ---\n{content}\n")
                                    total_size += len(content)
                                    if total_size > max_size_bytes:
                                        break
                        except Exception as fe:
                            logger.warning(f"Could not read {filepath}: {fe}")
                if total_size > max_size_bytes:
                    break

            text_content = "\n\n".join(file_contents)
            metadata["source_name"] = payload.split("/")[-1].replace(".git", "")
        except Exception as e:
            logger.error(f"GitHub ingestion error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to clone or read GitHub repo: {str(e)}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif source_type == "youtube":
        logger.info(f"Ingesting YouTube video: {payload}")
        # Extract video ID
        video_id = ""
        if "v=" in payload:
            video_id = payload.split("v=")[1].split("&")[0]
        elif "youtu.be/" in payload:
            video_id = payload.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = payload

        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL or Video ID")

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            lines = [t.get("text", "") for t in transcript]
            text_content = "\n".join(lines)
            metadata["source_name"] = f"YouTube Video {video_id}"
            metadata["youtube_video_id"] = video_id
        except Exception as e:
            logger.error(f"YouTube transcript error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube transcript: {str(e)}")

    elif source_type == "gmail":
        logger.info("Ingesting Gmail email payload")
        text_content = payload
        metadata["source_name"] = f"Email Document {source_id[-4:]}"

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="No readable text content found to ingest")

    # Ingest to RAG memory (Qdrant)
    try:
        ingest_res = await rag.ingest(text_content, metadata)
        return {
            "status": "success",
            "source_id": source_id,
            "source_name": metadata["source_name"],
            "chunks_ingested": ingest_res.get("chunks_ingested", 0)
        }
    except Exception as e:
        logger.error(f"Failed to ingest source to Qdrant: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to save source context: {str(e)}")


async def chat_with_source(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    prompt = body.get("prompt", "").strip()
    source_id = body.get("source_id", "").strip()

    if not prompt or not source_id:
        raise HTTPException(status_code=400, detail="Both 'prompt' and 'source_id' are required")

    logger.info(f"Chatting with source {source_id} for prompt: {prompt}")

    # Query Qdrant with filter
    filter_dict = {
        "must": [
            {
                "key": "source_id",
                "match": {"value": source_id}
            }
        ]
    }

    try:
        hits = await rag.query(prompt, limit=5, filter_dict=filter_dict)
    except Exception as e:
        logger.error(f"Qdrant source query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search source document memory: {str(e)}")

    if not hits:
        context = "No reference matches found in the document memory."
    else:
        context = "\n\n".join([f"--- Context Segment {idx+1} ---\n{hit['text']}" for idx, hit in enumerate(hits)])

    # Call Ollama with context
    system_prompt = (
        "You are an assistant trained to answer queries based on a specific uploaded document source. "
        "Use the provided context segments to answer the user query as accurately as possible. "
        "If you do not know the answer based on the context, state that clearly."
    )

    prompt_formatted = (
        f"Context:\n{context}\n\n"
        f"User Query: {prompt}"
    )

    ollama_payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_formatted}
        ],
        "stream": False
    }

    # Model resolution
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if "qwen3:14b" in models:
                    ollama_payload["model"] = "qwen3:14b"
                elif "qwen3:8b" in models:
                    ollama_payload["model"] = "qwen3:8b"
                elif models:
                    ollama_payload["model"] = models[0]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code == 200:
                final_response = r.json().get("message", {}).get("content", "").strip()
                return {
                    "status": "completed",
                    "response": final_response,
                    "reference_hits_count": len(hits)
                }
            else:
                raise HTTPException(status_code=502, detail=f"Ollama returned {r.status_code}")
    except Exception as e:
        logger.error(f"Chat with source query synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
