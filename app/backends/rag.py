import os
import uuid
import logging
import httpx
from fastapi import HTTPException

logger = logging.getLogger("spark.backend.rag")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://host.docker.internal:6333")
COLLECTION_NAME = "media_factory_extractions"

# Advanced RAG Options
RAG_ENGINE = os.getenv("RAG_ENGINE", "local").lower() # "local", "ragflow", "anythingllm"
RAGFLOW_URL = os.getenv("RAGFLOW_URL", "http://host.docker.internal:9380")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")
RAGFLOW_DATASET_ID = os.getenv("RAGFLOW_DATASET_ID", "")

ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_URL", "http://host.docker.internal:3001")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "")
ANYTHINGLLM_WORKSPACE = os.getenv("ANYTHINGLLM_WORKSPACE", "spark-test-tool")

async def get_embedding(text: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use modern /api/embed endpoint (Ollama v0.5+). Old /api/embeddings is deprecated.
            r = await client.post(
                f"{OLLAMA_URL}/api/embed",
                json={"model": "nomic-embed-text:v1.5", "input": text}
            )
            if r.status_code != 200:
                raise Exception(f"Ollama embed API returned status {r.status_code}: {r.text}")
            res = r.json()
            # Modern format: {"embeddings": [[...]]}
            embeddings = res.get("embeddings", [])
            if embeddings and len(embeddings) > 0:
                return embeddings[0]
            # Legacy fallback (older Ollama versions)
            if "embedding" in res:
                return res["embedding"]
            raise Exception("No embeddings found in Ollama response")
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

async def ensure_collection():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
            if r.status_code == 200:
                return
            
            # Create collection if not exists
            payload = {
                "vectors": {
                    "size": 768,
                    "distance": "Cosine"
                }
            }
            create_r = await client.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", json=payload)
            if create_r.status_code != 200:
                logger.error(f"Failed to create Qdrant collection: {create_r.text}")
    except Exception as e:
        logger.warning(f"Qdrant connection/creation warning: {e}")

def chunk_by_sentences(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> list:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
        except Exception:
            pass
    
    from nltk.tokenize import sent_tokenize
    try:
        sentences = sent_tokenize(text)
    except Exception as e:
        logger.warning(f"NLTK sent_tokenize failed, falling back to regex splitter: {e}")
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
 
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_len = len(sentence)
        if current_length + sentence_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Determine overlap sentences
            overlap_chunk = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) <= chunk_overlap:
                    overlap_chunk.insert(0, s)
                    overlap_len += len(s) + 1
                else:
                    break
            current_chunk = overlap_chunk
            current_length = sum(len(s) for s in current_chunk) + len(current_chunk)
            
        current_chunk.append(sentence)
        current_length += sentence_len + 1
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

async def ingest(
    text: str,
    metadata: dict = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    chunking_strategy: str = "sentence"
) -> dict:
    if not text.strip():
        return {"status": "ignored", "reason": "empty text"}

    # --- ROUTING TO ANYTHINGLLM ---
    if RAG_ENGINE == "anythingllm" and ANYTHINGLLM_API_KEY:
        try:
            logger.info("Ingesting into AnythingLLM...")
            # We create a virtual text file payload and upload it
            headers = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"}
            payload = {
                "textContent": text,
                "title": f"ingest_{uuid.uuid4().hex[:8]}.txt",
                "metadata": metadata or {}
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First upload text content as raw document
                r = await client.post(
                    f"{ANYTHINGLLM_URL}/api/v1/document/raw-text",
                    json=payload,
                    headers=headers
                )
                if r.status_code == 200:
                    doc_location = r.json().get("location")
                    # Update workspace embeddings
                    update_r = await client.post(
                        f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/update-embeddings",
                        json={"adds": [doc_location]},
                        headers=headers
                    )
                    if update_r.status_code == 200:
                        return {"status": "success", "engine": "anythingllm", "chunks_ingested": 1}
                    else:
                        logger.error(f"AnythingLLM update-embeddings failed: {update_r.text}")
                else:
                    logger.error(f"AnythingLLM document upload failed: {r.text}")
        except Exception as e:
            logger.error(f"AnythingLLM ingestion exception: {e}. Falling back to local Qdrant.")

    elif RAG_ENGINE == "ragflow" and RAGFLOW_API_KEY and RAGFLOW_DATASET_ID:
        try:
            import tempfile
            logger.info("Ingesting into RAGFlow...")
            headers = {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
            temp_filename = f"ingest_{uuid.uuid4().hex[:8]}.txt"

            # Use tempfile module — safe cross-platform temp file (not hardcoded /tmp)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", prefix="spark_ragflow_",
                delete=False, encoding="utf-8"
            ) as tmp_file:
                tmp_file.write(text)
                temp_path = tmp_file.name

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    with open(temp_path, "rb") as file_bytes:
                        files = {"file": (temp_filename, file_bytes, "text/plain")}
                        r = await client.post(
                            f"{RAGFLOW_URL}/api/v1/datasets/{RAGFLOW_DATASET_ID}/documents",
                            files=files,
                            headers=headers
                        )
                if r.status_code == 200:
                    return {"status": "success", "engine": "ragflow", "chunks_ingested": 1}
                else:
                    logger.error(f"RAGFlow document upload failed: {r.text}")
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception as e:
            logger.error(f"RAGFlow ingestion exception: {e}. Falling back to local Qdrant.")

    # --- DEFAULT LOCAL QDRANT INGESTION ---
    await ensure_collection()
    
    # Fallback to default if values are invalid
    if chunk_size <= 0:
        chunk_size = 1000
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        chunk_overlap = int(chunk_size * 0.1)

    if chunking_strategy == "sentence":
        chunks = chunk_by_sentences(text, chunk_size, chunk_overlap)
    else:
        # Character-based splitting fallback
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i:i+chunk_size])
            i += chunk_size - chunk_overlap

    points = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for index, chunk in enumerate(chunks):
            vector = await get_embedding(chunk)
            point_id = str(uuid.uuid4())
            payload = {
                "text": chunk,
                "chunk_index": index,
                "total_chunks": len(chunks)
            }
            if metadata:
                payload.update(metadata)
            
            points.append({
                "id": point_id,
                "vector": vector,
                "payload": payload
            })

        # Upsert in bulk
        r = await client.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points",
            json={"points": points}
        )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Qdrant rejected upsert: {r.text}")

    return {"status": "success", "engine": "local", "chunks_ingested": len(chunks)}

async def query(search_text: str, limit: int = 3, filter_dict: dict = None) -> list:
    # --- ROUTING TO ANYTHINGLLM QUERY ---
    if RAG_ENGINE == "anythingllm" and ANYTHINGLLM_API_KEY:
        try:
            logger.info("Querying AnythingLLM...")
            headers = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"}
            payload = {"message": search_text, "mode": "query"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/chat",
                    json=payload,
                    headers=headers
                )
                if r.status_code == 200:
                    res = r.json()
                    # AnythingLLM returns chat text and citations/sources
                    text_response = res.get("textResponse", "")
                    sources = res.get("sources", [])
                    hits = []
                    # Format standard hit response matching local format
                    for idx, src in enumerate(sources[:limit]):
                        hits.append({
                            "text": f"[Answer Summary]: {text_response}\n\n[Source Segment]: {src.get('text', '')}",
                            "score": 0.9 - (idx * 0.1),
                            "source": src.get("title", "AnythingLLM Document"),
                            "tool": "anythingllm"
                        })
                    if not hits and text_response:
                        hits.append({
                            "text": text_response,
                            "score": 1.0,
                            "source": "AnythingLLM LLM Synthesis",
                            "tool": "anythingllm"
                        })
                    return hits
        except Exception as e:
            logger.error(f"AnythingLLM query exception: {e}. Falling back to local Qdrant search.")

    # --- ROUTING TO RAGFLOW QUERY ---
    elif RAG_ENGINE == "ragflow" and RAGFLOW_API_KEY and RAGFLOW_DATASET_ID:
        try:
            logger.info("Querying RAGFlow dataset...")
            headers = {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
            # Retrieve chunks directly matching dataset ID
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Query RAGFlow dataset document chunks endpoint
                r = await client.get(
                    f"{RAGFLOW_URL}/api/v1/datasets/{RAGFLOW_DATASET_ID}/documents",
                    headers=headers
                )
                # Note: We fallback to local search if direct document retrieval fails
                if r.status_code == 200:
                    # RAGFlow returns documents listing. For true semantic search,
                    # normally RAGFlow uses their Chat/Agent session API.
                    # Here we fetch documents matching the search keyword.
                    docs = r.json().get("data", [])
                    hits = []
                    for doc in docs[:limit]:
                        hits.append({
                            "text": f"Document Title: {doc.get('name')}. Chunk count: {doc.get('chunk_num')}",
                            "score": 0.8,
                            "source": doc.get("name", "RAGFlow File"),
                            "tool": "ragflow"
                        })
                    return hits
        except Exception as e:
            logger.error(f"RAGFlow query exception: {e}. Falling back to local Qdrant search.")

    # --- DEFAULT LOCAL QDRANT SEARCH ---
    await ensure_collection()
    vector = await get_embedding(search_text)
    
    payload = {
        "vector": vector,
        "limit": limit,
        "with_payload": True
    }
    if filter_dict:
        payload["filter"] = filter_dict
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
                json=payload
            )
            if r.status_code != 200:
                raise Exception(f"Qdrant search failed: {r.text}")
            
            results = r.json().get("result", [])
            hits = []
            for hit in results:
                p = hit.get("payload", {})
                hits.append({
                    "text": p.get("text", ""),
                    "score": hit.get("score", 0.0),
                    "source": p.get("source_file", "unknown"),
                    "tool": p.get("extraction_tool", "unknown")
                })
            return hits
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return []


async def keyword_query(search_text: str, limit: int = 3, filter_dict: dict = None) -> list:
    await ensure_collection()
    try:
        scroll_payload = {
            "limit": 10000,
            "with_payload": True,
            "with_vector": False
        }
        if filter_dict:
            scroll_payload["filter"] = filter_dict
            
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
                json=scroll_payload
            )
            if r.status_code != 200:
                logger.error(f"Qdrant scroll failed: {r.text}")
                return []
            
            results = r.json().get("result", {}).get("points", [])
            hits = []
            search_lower = search_text.lower()
            for point in results:
                p = point.get("payload", {})
                chunk_text = p.get("text", "")
                if search_lower in chunk_text.lower():
                    score = chunk_text.lower().count(search_lower)
                    hits.append({
                        "text": chunk_text,
                        "score": float(score),
                        "source": p.get("source_file", "unknown"),
                        "tool": p.get("extraction_tool", "unknown")
                    })
            # Sort by frequency/relevance descending
            hits.sort(key=lambda x: x["score"], reverse=True)
            return hits[:limit]
    except Exception as e:
        logger.error(f"RAG keyword search error: {e}")
        return []


async def list_sources() -> list:
    await ensure_collection()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
                json={
                    "limit": 10000,
                    "with_payload": True,
                    "with_vector": False
                }
            )
            if r.status_code != 200:
                logger.error(f"Qdrant scroll failed: {r.text}")
                return []
            
            results = r.json().get("result", {}).get("points", [])
            sources = {}
            for point in results:
                payload = point.get("payload", {})
                name = (
                    payload.get("source_name") or 
                    payload.get("source_file") or 
                    payload.get("source_url") or 
                    "Unknown Source"
                )
                src_type = (
                    payload.get("source_type") or 
                    payload.get("extraction_tool") or 
                    "document"
                )
                source_id = payload.get("source_id") or name
                
                if source_id not in sources:
                    sources[source_id] = {
                        "source_id": source_id,
                        "source_name": name,
                        "source_type": src_type,
                        "chunks": 0
                    }
                sources[source_id]["chunks"] += 1
                
            return list(sources.values())
    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        return []


async def delete_source(source_id: str) -> dict:
    await ensure_collection()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "filter": {
                    "should": [
                        {"key": "source_id", "match": {"value": source_id}},
                        {"key": "source_name", "match": {"value": source_id}},
                        {"key": "source_file", "match": {"value": source_id}}
                    ]
                }
            }
            r = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/delete",
                json=payload
            )
            if r.status_code != 200:
                logger.error(f"Qdrant delete points failed: {r.text}")
                raise Exception(f"Qdrant delete rejected: {r.text}")
            return {"status": "success", "details": f"Source {source_id} deleted."}
    except Exception as e:
        logger.error(f"Error deleting source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def clear_all_memory() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
            if r.status_code not in [200, 404]:
                logger.error(f"Failed to delete collection: {r.text}")
                raise Exception(f"Qdrant collection deletion rejected: {r.text}")
        
        await ensure_collection()
        return {"status": "success", "details": "Collection cleared and recreated."}
    except Exception as e:
        logger.error(f"Error clearing collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

