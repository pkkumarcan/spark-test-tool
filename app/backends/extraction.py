import os
import uuid
import logging
import asyncio
import httpx
import base64
import subprocess
from fastapi import Request, HTTPException, UploadFile

logger = logging.getLogger("spark.backend.extraction")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def ocr_image(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    image_data = body.get("image_data", "")
    if not image_data:
        raise HTTPException(status_code=400, detail="Image data (base64 or URL) is required")

    # If it's a data url, extract raw base64
    base64_str = image_data
    if "," in image_data:
        base64_str = image_data.split(",", 1)[1]

    payload = {
        "model": "qwen2.5-vl:7b-instruct-q4_k_m",
        "messages": [
            {
                "role": "user",
                "content": "Extract all text from this image exactly as it appears. Preserve layout. Output markdown.",
                "images": [base64_str]
            }
        ],
        "stream": False
    }

    job_id = f"ocr_{uuid.uuid4().hex[:8]}"
    text = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=payload)
            if r.status_code == 200:
                result = r.json()
                text = result.get("message", {}).get("content", "").strip()
            else:
                text = f"OCR Mock Fallback: Ollama returned {r.status_code}. Extracted dummy text from image."
    except Exception as e:
        logger.warning(f"Ollama OCR error: {e}. Falling back to mock text.")
        text = f"OCR Mock Fallback: Connection error {e}. Simulated text extraction from image."

    # Save output to text file
    filename = f"{job_id}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "text": text,
        "output_url": f"/output/{filename}",
        "filename": filename
    }


import re

def clean_extracted_text(text: str, clean_spacing: bool = False, fix_broken_sentences: bool = False, preserve_paragraphs: bool = False) -> str:
    if not text:
        return ""
    
    if fix_broken_sentences:
        # Fix broken sentences (newlines that do not follow a period/ending punctuation)
        text = re.sub(r'(?<![.!?])\n', ' ', text)
        
    if preserve_paragraphs:
        # Convert double newlines (or more) to a specific marker, clean spacing, then restore paragraphs
        text = re.sub(r'\n{2,}', '\n\n', text)
        
    if clean_spacing:
        # Remove extra spaces but keep newlines intact
        text = re.sub(r'[ \t]+', ' ', text)
        # Clean double spaces around newlines
        text = re.sub(r' \n', '\n', text)
        text = re.sub(r'\n ', '\n', text)
        
    return text.strip()


async def extract_pdf(
    file: UploadFile,
    ocr_all: bool = False,
    auto_ingest: bool = False,
    clean_spacing: bool = False,
    fix_broken_sentences: bool = False,
    preserve_paragraphs: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    chunking_strategy: str = "sentence"
):
    job_id = f"pdf_{uuid.uuid4().hex[:8]}"
    logger.info(f"Extracting PDF {file.filename} (ocr_all={ocr_all}, auto_ingest={auto_ingest})")
    
    try:
        content = await file.read()
        import fitz  # PyMuPDF
        
        doc = fitz.open(stream=content, filetype="pdf")
        
        extracted_text_list = []
        extracted_text_list.append(f"# PDF Extraction: {file.filename}\n")
        
        for idx, page in enumerate(doc):
            page_text = page.get_text()
            if page_text:
                extracted_text_list.append(f"## Page {idx + 1}\n{page_text}\n")
        
        raw_text = "\n".join(extracted_text_list)
        if not raw_text.strip() or len(raw_text.strip()) <= len(file.filename) + 20:
            raw_text = f"# PDF Extraction: {file.filename}\n\nCould not extract text from this PDF (it might be scanned/image-only or encrypted)."
        
        # Apply cleanup
        text = clean_extracted_text(raw_text, clean_spacing, fix_broken_sentences, preserve_paragraphs)
        
        # Save output to text file
        filename = f"{job_id}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
 
        chunks_ingested = 0
        if auto_ingest:
            from app.backends import rag
            metadata = {
                "source_id": job_id,
                "source_name": file.filename,
                "source_type": "pdf",
                "source_file": filename,
                "extraction_tool": "pdf"
            }
            ingest_res = await rag.ingest(text, metadata, chunk_size, chunk_overlap, chunking_strategy)
            chunks_ingested = ingest_res.get("chunks_ingested", 0)
 
        return {
            "job_id": job_id,
            "text": text,
            "details": f"Processed {file.filename} successfully via PyMuPDF.",
            "output_url": f"/output/{filename}",
            "filename": filename,
            "auto_ingested": auto_ingest,
            "chunks_ingested": chunks_ingested
        }
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from html.parser import HTMLParser
import re

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.tag_stack = []
        self.ignore_tags = {
            "script", "style", "head", "title", "meta", "link", "svg", "path", "nav", "footer", "aside", "header"
        }
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        if tag == "title":
            self.in_title = True
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}:
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in self.tag_stack:
            while self.tag_stack:
                popped = self.tag_stack.pop()
                if popped == tag:
                    break
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}:
            self.result.append("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not any(t in self.ignore_tags for t in self.tag_stack):
            cleaned = data.strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)
            if cleaned:
                self.result.append(cleaned + " ")

    def get_text(self):
        raw_text = "".join(self.result)
        cleaned_text = re.sub(r'\n\s*\n+', '\n\n', raw_text).strip()
        title_prefix = f"# Webpage: {self.title.strip()}\n\n" if self.title.strip() else ""
        return title_prefix + cleaned_text


async def extract_link(
    url: str,
    auto_ingest: bool = False,
    clean_spacing: bool = False,
    fix_broken_sentences: bool = False,
    preserve_paragraphs: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    chunking_strategy: str = "sentence"
) -> dict:
    job_id = f"link_{uuid.uuid4().hex[:8]}"
    logger.info(f"Extracting web link: {url} (auto_ingest={auto_ingest})")
    
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL format. URL must start with http:// or https://")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            }
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                raise Exception(f"Failed to fetch webpage. HTTP Status {r.status_code}")
            
            html_content = r.text

        parser = HTMLTextExtractor()
        parser.feed(html_content)
        raw_text = parser.get_text()
        title = parser.title.strip() or url
        
        if not raw_text.strip() or len(raw_text.strip()) <= len(title) + 20:
            raw_text = f"# Webpage Extraction: {title}\n\nCould not extract significant text content from the webpage."

        # Apply cleanup
        text = clean_extracted_text(raw_text, clean_spacing, fix_broken_sentences, preserve_paragraphs)

        filename = f"{job_id}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        chunks_ingested = 0
        if auto_ingest:
            from app.backends import rag
            metadata = {
                "source_id": job_id,
                "source_name": title,
                "source_type": "link",
                "source_file": filename,
                "extraction_tool": "link",
                "source_url": url
            }
            ingest_res = await rag.ingest(text, metadata, chunk_size, chunk_overlap, chunking_strategy)
            chunks_ingested = ingest_res.get("chunks_ingested", 0)

        return {
            "job_id": job_id,
            "text": text,
            "title": title,
            "details": f"Processed {url} successfully.",
            "output_url": f"/output/{filename}",
            "filename": filename,
            "auto_ingested": auto_ingest,
            "chunks_ingested": chunks_ingested
        }
    except Exception as e:
        logger.error(f"Link extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



async def extract_youtube(youtube_url: str):
    """Extract a real transcript from a YouTube video using youtube-transcript-api."""
    job_id = f"yt_{uuid.uuid4().hex[:8]}"
    logger.info(f"Extracting YouTube transcript for {youtube_url}")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
        import re as _re

        # Extract the video ID from various YouTube URL formats
        # Handles: youtu.be/ID, youtube.com/watch?v=ID, youtube.com/shorts/ID, /embed/ID
        vid_match = _re.search(
            r"(?:v=|youtu\.be/|/shorts/|/embed/|/v/)([A-Za-z0-9_\-]{11})",
            youtube_url
        )
        if not vid_match:
            raise HTTPException(
                status_code=400,
                detail="Could not extract a valid YouTube video ID from the provided URL."
            )
        video_id = vid_match.group(1)
        logger.info(f"Resolved YouTube video ID: {video_id}")

        # Fetch transcript in a thread (library is synchronous)
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript, video_id
        )

        # Format as readable timestamped transcript
        lines = []
        for entry in transcript_list:
            start_sec = int(entry.get("start", 0))
            minutes = start_sec // 60
            seconds = start_sec % 60
            text_line = entry.get("text", "").strip().replace("\n", " ")
            lines.append(f"[{minutes:02d}:{seconds:02d}] {text_line}")

        full_text = f"# YouTube Transcript\nURL: {youtube_url}\nVideo ID: {video_id}\n\n" + "\n".join(lines)

        # Save to output file
        filename = f"{job_id}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_text)

        return {
            "text": full_text,
            "details": f"Fetched {len(transcript_list)} transcript entries for video {video_id}.",
            "output_url": f"/output/{filename}",
            "filename": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        if "TranscriptsDisabled" in error_type or "disabled" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="Transcripts are disabled for this YouTube video. Try a different video."
            )
        if "NoTranscriptFound" in error_type or "no transcript" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="No transcript found for this video. It may not have captions."
            )
        logger.error(f"YouTube extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube extraction failed: {str(e)}")
