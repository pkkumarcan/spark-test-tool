import os
import json
import logging
import asyncio
import httpx
import re
from fastapi import Request, HTTPException
from duckduckgo_search import DDGS

logger = logging.getLogger("spark.backend.research_agent")


def clean_html(html: str) -> str:
    # Remove script and style tags
    html = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Extract text content
    text = re.sub(r'<.*?>', ' ', html)
    # Normalize spacing
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:8000] # Limit to avoid context limit issues


async def fetch_page(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                return clean_html(r.text)
            return ""
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ""


async def search_yahoo(query: str, max_results: int = 3) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    from urllib.parse import quote, unquote
    url = f"https://search.yahoo.com/search?p={quote(query)}"
    links = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                hrefs = re.findall(r'href="([^"]+)"', r.text)
                for href in hrefs:
                    if "RU=" in href:
                        parts = href.split("RU=")
                        if len(parts) > 1:
                            target = parts[1].split("/RK=")[0]
                            target = unquote(target)
                            if target.startswith("http") and "yahoo.com" not in target and "yimg.com" not in target:
                                if target not in links:
                                    links.append(target)
                    elif href.startswith("http") and "yahoo.com" not in href and "yimg.com" not in href and "search.yahoo" not in href:
                        if href not in links:
                            links.append(href)
                
                # If no links found, try matching generic links in search result divs
                if not links:
                    generic_links = re.findall(r'https?://[a-zA-Z0-9./_\-]+', r.text)
                    for link in generic_links:
                        if "yahoo.com" not in link and "yimg.com" not in link and "google" not in link:
                            if link not in links:
                                links.append(link)
    except Exception as e:
        logger.warning(f"Yahoo Search fallback failed: {e}")
    return links[:max_results]


async def search_tavily(query: str, api_key: str, max_results: int = 3) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": max_results}
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                return [res.get("url") for res in results if res.get("url")]
    except Exception as e:
        logger.warning(f"Tavily search failed: {e}")
    return []


async def search_searxng(query: str, base_url: str, max_results: int = 3) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{base_url.rstrip('/')}/search",
                params={"q": query, "format": "json"}
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                return [res.get("url") for res in results[:max_results] if res.get("url")]
    except Exception as e:
        logger.warning(f"SearXNG search failed: {e}")
    return []


async def search_google(query: str, api_key: str, cse_id: str, max_results: int = 3) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": api_key, "cx": cse_id, "q": query, "num": max_results}
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                return [item.get("link") for item in items if item.get("link")]
    except Exception as e:
        logger.warning(f"Google Custom Search failed: {e}")
    return []


async def search_wikipedia(query: str, max_results: int = 3) -> list:
    try:
        from urllib.parse import quote
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(query)}&limit={max_results}&namespace=0&format=json"
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                if len(data) >= 4:
                    return data[3]
    except Exception as e:
        logger.warning(f"Wikipedia OpenSearch fallback failed: {e}")
    return []


import random

async def search_ddg_with_retry(query: str, backend: str = None, max_results: int = 3) -> tuple:
    urls = []
    for attempt in range(2):
        try:
            if attempt > 0:
                await asyncio.sleep(2.0 * attempt + random.random())
            with DDGS() as ddgs:
                if backend:
                    results = [r for r in ddgs.text(query, backend=backend, max_results=max_results)]
                else:
                    results = [r for r in ddgs.text(query, max_results=max_results)]
                for res in results:
                    href = res.get("href")
                    if href and href not in urls:
                        urls.append(href)
                return urls, True
        except Exception as e:
            err_msg = str(e)
            if "202" in err_msg or "Ratelimit" in err_msg or "RateLimit" in err_msg:
                logger.warning(f"DDG rate-limited on attempt {attempt+1} for backend {backend or 'default'}")
            else:
                logger.warning(f"DDG failed on attempt {attempt+1} for backend {backend or 'default'}: {e}")
    return urls, False




async def conduct_research(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    return await conduct_research_from_params(body, ollama_url)


async def conduct_research_from_params(body: dict, ollama_url: str):

    query = body.get("prompt", "")
    if not query.strip():
        raise HTTPException(status_code=400, detail="Research query is required")

    job_id = f"res_{os.urandom(4).hex()}"
    logger.info(f"[{job_id}] Step 1: Formulating search queries for query: '{query}'")

    # Step 1: Formulate search queries using local LLM
    # Resolve the best available model
    from app.backends.utils import resolve_best_model
    resolved_model = await resolve_best_model(ollama_url, preferred=["qwen3:14b", "qwen3:8b"])

    search_formulator_prompt = (
        f"You are a research assistant. Based on the user's research topic, output exactly 2 search queries optimized for search engines.\n"
        f"Output ONLY a JSON list of strings, with no additional explanation.\n"
        f"Topic: {query}"
    )
    
    ollama_payload = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": search_formulator_prompt}
        ],
        "format": "json",
        "stream": False
    }

    search_queries = [query]
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "").strip()
                queries = json.loads(content)
                if isinstance(queries, list) and len(queries) > 0:
                    search_queries = queries
    except Exception as e:
        logger.warning(f"[{job_id}] Search query formulation failed, using raw query: {e}")

    logger.info(f"[{job_id}] Step 2: Executing search queries: {search_queries}")

    # Step 2: Search with configured providers and fallbacks
    urls = []
    errors = []
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    searxng_url = os.getenv("SEARXNG_URL")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")

    for idx, q in enumerate(search_queries):
        if idx > 0:
            # Add delay between queries to avoid rate limits
            await asyncio.sleep(3.0 + random.random() * 2.0)
        
        success = False

        # 1. Try Tavily
        if tavily_api_key:
            try:
                tav_res = await search_tavily(q, tavily_api_key, max_results=3)
                if tav_res:
                    for href in tav_res:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] Tavily Search succeeded for query '{q}'")
            except Exception as e:
                errors.append(f"Tavily API: {e}")

        # 2. Try Google CSE
        if not success and google_api_key and google_cse_id:
            try:
                google_res = await search_google(q, google_api_key, google_cse_id, max_results=3)
                if google_res:
                    for href in google_res:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] Google Custom Search succeeded for query '{q}'")
            except Exception as e:
                errors.append(f"Google CSE: {e}")

        # 3. Try SearXNG
        if not success and searxng_url:
            try:
                searx_res = await search_searxng(q, searxng_url, max_results=3)
                if searx_res:
                    for href in searx_res:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] SearXNG Search succeeded for query '{q}'")
            except Exception as e:
                errors.append(f"SearXNG: {e}")

        # 4. Try DuckDuckGo Default
        if not success:
            try:
                ddg_urls, ddg_success = await search_ddg_with_retry(q, max_results=3)
                if ddg_success:
                    for href in ddg_urls:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] DuckDuckGo Default Search succeeded for query '{q}'")
            except Exception as e:
                errors.append(f"DDG Default: {e}")

        # 5. Try DuckDuckGo HTML
        if not success:
            try:
                ddg_urls, ddg_success = await search_ddg_with_retry(q, backend="html", max_results=3)
                if ddg_success:
                    for href in ddg_urls:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] DuckDuckGo HTML Search succeeded for query '{q}'")
            except Exception as e:
                errors.append(f"DDG HTML: {e}")

        # 6. Try DuckDuckGo Lite
        if not success:
            try:
                ddg_urls, ddg_success = await search_ddg_with_retry(q, backend="lite", max_results=3)
                if ddg_success:
                    for href in ddg_urls:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] DuckDuckGo Lite Search succeeded for query '{q}'")
            except Exception as e:
                errors.append(f"DDG Lite: {e}")

        # 7. Try Yahoo
        if not success:
            try:
                yahoo_results = await search_yahoo(q, max_results=3)
                if yahoo_results:
                    for href in yahoo_results:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] Yahoo Search fallback succeeded for query '{q}'")
            except Exception as e:
                err_msg = str(e)
                errors.append(f"Yahoo fallback: {err_msg}")
                logger.warning(f"[{job_id}] Yahoo Search fallback failed for query '{q}': {err_msg}")

        # 8. Try Wikipedia
        if not success:
            try:
                wiki_results = await search_wikipedia(q, max_results=3)
                if wiki_results:
                    for href in wiki_results:
                        if href not in urls:
                            urls.append(href)
                    success = True
                    logger.info(f"[{job_id}] Wikipedia Search fallback succeeded for query '{q}'")
            except Exception as e:
                err_msg = str(e)
                errors.append(f"Wikipedia fallback: {err_msg}")
                logger.warning(f"[{job_id}] Wikipedia Search fallback failed for query '{q}': {err_msg}")


    urls = urls[:5] # limit to top 5 URLs
    if not urls:
        if errors:
            # If search failed due to rate limits or connection errors
            raise HTTPException(
                status_code=502, 
                detail=f"Search engine unreachable or rate-limited. Errors encountered:\n" + "\n".join(errors)
            )
        raise HTTPException(status_code=404, detail="No search results found for query.")

    # Step 3: Fetch and scrape page contents in parallel
    logger.info(f"[{job_id}] Step 3: Scraping top pages: {urls}")
    scrape_tasks = [fetch_page(url) for url in urls]
    page_texts = await asyncio.gather(*scrape_tasks)

    valid_sources = []
    for url, text in zip(urls, page_texts):
        if text.strip():
            valid_sources.append({"url": url, "text": text})

    if not valid_sources:
        raise HTTPException(status_code=502, detail="Failed to scrape content from any search results.")

    # Step 4: Summarize each page to form research notes
    logger.info(f"[{job_id}] Step 4: Summarizing page contents...")
    summaries = []
    for idx, src in enumerate(valid_sources):
        summary_prompt = (
            f"You are a research analyst. Summarize the following web content into key facts, figures, and research notes. "
            f"Be concise, objective, and cite critical points.\n\n"
            f"URL: {src['url']}\n"
            f"Content:\n{src['text'][:4000]}"
        )
        
        summary_payload = {
            "model": ollama_payload["model"],
            "messages": [{"role": "user", "content": summary_prompt}],
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(f"{ollama_url}/api/chat", json=summary_payload)
                if r.status_code == 200:
                    summary_text = r.json().get("message", {}).get("content", "").strip()
                    summaries.append(f"### Source [{idx + 1}]: {src['url']}\n{summary_text}")
        except Exception as e:
            logger.warning(f"Failed to summarize source {src['url']}: {e}")

    # Step 5: Synthesize final report in markdown
    logger.info(f"[{job_id}] Step 5: Synthesizing final research report...")
    notes_combined = "\n\n".join(summaries)
    
    synthesis_prompt = (
        f"You are a senior technical writer. Write a comprehensive, well-structured research report "
        f"answering the user's query based ONLY on the provided research notes. "
        f"Format the report beautifully in Markdown. Include headers, bullet points, and a bibliography citing the source URLs.\n\n"
        f"Query: {query}\n\n"
        f"Research Notes:\n{notes_combined}"
    )

    synthesis_payload = {
        "model": ollama_payload["model"],
        "messages": [{"role": "user", "content": synthesis_prompt}],
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=synthesis_payload)
            if r.status_code == 200:
                report = r.json().get("message", {}).get("content", "").strip()
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "report": report,
                    "sources": [s["url"] for s in valid_sources]
                }
            raise Exception(f"Ollama returned {r.status_code}")
    except Exception as e:
        logger.error(f"[{job_id}] Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to synthesize research report: {str(e)}")
