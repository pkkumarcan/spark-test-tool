import os
import time
import logging

logger = logging.getLogger("spark.backend.telemetry")

try:
    from langfuse import Langfuse
    HAS_LANGFUSE = True
except ImportError:
    HAS_LANGFUSE = False
    logger.warning("Langfuse package is not installed. Telemetry tracing will be disabled.")

_langfuse_client = None

def get_langfuse_client():
    global _langfuse_client
    if not HAS_LANGFUSE:
        return None
        
    if _langfuse_client is None:
        # Check if environment is configured
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-default")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-default")
        host = os.getenv("LANGFUSE_HOST", "http://host.docker.internal:3002")
        
        try:
            _langfuse_client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            logger.info(f"Initialized Langfuse client at {host}")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse client: {e}")
            _langfuse_client = None
            
    return _langfuse_client

def trace_generation(
    name: str,
    model: str,
    prompt: str,
    completion: str,
    latency_seconds: float = None,
    system_prompt: str = None,
    error: str = None
):
    """
    Submits a single generation trace to Langfuse.
    """
    client = get_langfuse_client()
    if not client:
        return None
        
    try:
        # Create a trace
        trace = client.trace(
            name=name,
            metadata={
                "environment": "spark-test-tool-local",
                "framework": "fastapi"
            }
        )
        
        # Log LLM generation event within trace
        generation = trace.generation(
            name="llm-call",
            model=model,
            prompt=prompt,
            completion=completion,
            system_prompt=system_prompt,
            error_message=error,
            metadata={"latency_seconds": latency_seconds}
        )
        # Flush events to Langfuse API
        client.flush()
        return trace.id
    except Exception as e:
        logger.debug(f"Langfuse tracing event submission failed: {e}")
        return None
