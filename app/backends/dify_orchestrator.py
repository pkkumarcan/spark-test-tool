import os
import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger("spark.backend.dify_orchestrator")

async def run_dify_workflow(request: Request):
    """
    Triggers a local Dify App workflow.
    Expects json body:
    {
        "api_key": "YOUR_DIFY_APP_API_KEY",
        "inputs": { ... },
        "response_mode": "blocking" | "streaming"
    }
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    api_key = body.get("api_key") or os.getenv("DIFY_DEFAULT_APP_KEY", "")
    inputs = body.get("inputs", {})
    response_mode = body.get("response_mode", "blocking")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Dify App API key is required (either in request or DIFY_DEFAULT_APP_KEY env)")
        
    dify_api_url = os.getenv("DIFY_API_URL", "http://host.docker.internal:5001")
    
    payload = {
        "inputs": inputs,
        "response_mode": "streaming" if response_mode == "streaming" else "blocking",
        "user": "spark-test-tool-gateway"
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Blocking Mode Execution
    if response_mode == "blocking":
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{dify_api_url}/v1/workflows/run",
                    json=payload,
                    headers=headers
                )
                if r.status_code == 200:
                    return r.json()
                else:
                    logger.error(f"Dify workflow failed with status {r.status_code}: {r.text}")
                    raise HTTPException(status_code=r.status_code, detail=f"Dify workflow execution error: {r.text}")
        except Exception as e:
            logger.error(f"Failed to communicate with Dify: {e}")
            raise HTTPException(status_code=502, detail=f"Failed to connect to local Dify service: {str(e)}")
            
    # Streaming Mode Execution
    else:
        async def event_generator():
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST",
                        f"{dify_api_url}/v1/workflows/run",
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            yield f"data: {response.status_code} - Dify endpoint failed\n\n"
                            return
                        async for line in response.aiter_lines():
                            if line:
                                yield f"{line}\n\n"
            except Exception as e:
                logger.error(f"Streaming error with Dify: {e}")
                yield f"data: Error during stream: {str(e)}\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
