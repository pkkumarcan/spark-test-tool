import os
import logging
import json
import httpx
import re
import asyncio
from fastapi import Request, HTTPException

# Import MCP SDK components dynamically to avoid failure if package isn't installed yet
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False

logger = logging.getLogger("spark.backend.mcp_agent")

# Workspace root — resolved from env var (same logic as coding_agent)
_default_workspace = "/app" if os.path.exists("/app/app/main.py") else os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", _default_workspace)

# Fallback/Simulated MCP tools registry
MOCKED_MCP_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a specific city.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city and state, e.g. San Francisco, CA"}
            },
            "required": ["location"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the local corporate knowledge base for internal documentation.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to lookup"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate_loan_payments",
        "description": "Calculate monthly loan payments based on principal, interest rate, and term.",
        "parameters": {
            "type": "object",
            "properties": {
                "principal": {"type": "number", "description": "The loan amount in dollars"},
                "rate": {"type": "number", "description": "Annual interest rate (e.g. 5.5)"},
                "years": {"type": "integer", "description": "Loan term in years"}
            },
            "required": ["principal", "rate", "years"]
        }
    }
]

def execute_mocked_tool(tool_name: str, arguments: dict) -> str:
    if tool_name == "get_weather":
        loc = arguments.get("location", "Unknown")
        return f"Weather in {loc}: 72°F (22°C), Sunny, Wind 5mph, Humidity 45%."
    elif tool_name == "search_knowledge_base":
        q = arguments.get("query", "")
        return f"Found 1 result for '{q}': 'Spark Workstation setup uses RTX 3090/3060 configurations. Qdrant is on port 6333, Ollama is on port 11434.'"
    elif tool_name == "calculate_loan_payments":
        p = arguments.get("principal", 0)
        r = arguments.get("rate", 0) / 100 / 12
        y = arguments.get("years", 0) * 12
        if r == 0:
            m = p / y if y > 0 else 0
        else:
            m = (p * r * (1 + r)**y) / ((1 + r)**y - 1) if y > 0 else 0
        return f"Calculation completed. Principal: ${p:,}, Monthly Payment: ${m:.2f} (Term: {arguments.get('years')} years at {arguments.get('rate')}% APR)."
    return f"Error: Tool {tool_name} not found."

# Define the active MCP servers we want to spin up on-demand
CURRENT_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

MCP_SERVERS_CONFIG = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", WORKSPACE_ROOT]
    },
    "sqlite": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db",
                 os.path.join(os.getenv("OUTPUT_DIR", "/app/output"), "mail_state.db")]
    },
    "comfyui": {
        "command": "python3",
        "args": [os.path.join(CURRENT_BACKEND_DIR, "comfyui_mcp_server.py")]
    },
    "finance": {
        "command": "python3",
        "args": [os.path.join(CURRENT_BACKEND_DIR, "finance_mcp_server.py")]
    }
}

async def execute_real_mcp_tool(server_name: str, config: dict, tool_name: str, arguments: dict) -> str:
    if not HAS_MCP_SDK:
        return "Error: MCP Python SDK is not installed."
    
    logger.info(f"Connecting to real MCP Server '{server_name}' to execute tool '{tool_name}'...")
    server_params = StdioServerParameters(
        command=config["command"],
        args=config["args"],
        env=None
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
                result = await session.call_tool(tool_name, arguments=arguments)
                
                # Format response content
                if hasattr(result, "content") and result.content:
                    text_parts = []
                    for content_item in result.content:
                        if hasattr(content_item, "text"):
                            text_parts.append(content_item.text)
                        elif isinstance(content_item, dict) and "text" in content_item:
                            text_parts.append(content_item["text"])
                    return "\n".join(text_parts)
                return str(result)
    except Exception as e:
        logger.error(f"Failed to execute real MCP tool '{tool_name}' on '{server_name}': {e}")
        return f"Error executing tool '{tool_name}' via MCP server '{server_name}': {e}"

async def discover_all_mcp_tools() -> tuple[list[dict], dict[str, str]]:
    """Connects to all configured servers in parallel to list their tools.
       Returns (merged_tool_schemas, tool_to_server_map)"""
    if not HAS_MCP_SDK:
        logger.warning("MCP SDK not installed. Using mocked tools.")
        return MOCKED_MCP_TOOLS, {}

    merged_tools = []
    tool_to_server = {}

    async def get_server_tools(server_name: str, config: dict):
        server_params = StdioServerParameters(
            command=config["command"],
            args=config["args"],
            env=None
        )
        try:
            # Short timeout to avoid hanging if npx is missing
            async with asyncio.timeout(10.0):
                async with stdio_client(server_params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        tools_result = await session.list_tools()
                        
                        server_tools = []
                        # list_tools returns a list of tools or a ListToolsResult object
                        tools_list = tools_result.tools if hasattr(tools_result, "tools") else tools_result
                        
                        for tool in tools_list:
                            name = tool.name if hasattr(tool, "name") else tool.get("name")
                            desc = tool.description if hasattr(tool, "description") else tool.get("description")
                            schema = tool.inputSchema if hasattr(tool, "inputSchema") else tool.get("inputSchema", {})
                            
                            server_tools.append({
                                "name": name,
                                "description": desc,
                                "parameters": schema
                            })
                            tool_to_server[name] = server_name
                        logger.info(f"Discovered {len(server_tools)} tools from MCP Server '{server_name}'")
                        return server_tools
        except Exception as e:
            logger.warning(f"Could not discover tools from MCP Server '{server_name}': {e}. Ensure Node.js and npx are installed.")
            return []

    # Query active servers in parallel
    tasks = [get_server_tools(name, config) for name, config in MCP_SERVERS_CONFIG.items()]
    results = await asyncio.gather(*tasks)
    
    for r in results:
        merged_tools.extend(r)
        
    if not merged_tools:
        logger.warning("No real MCP tools discovered. Falling back to mocked tools.")
        return MOCKED_MCP_TOOLS, {}
        
    return merged_tools, tool_to_server

async def run_mcp_agent(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    prompt = body.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    logger.info(f"Running MCP Agent for prompt: {prompt}")

    # Discover real tools from filesystem/sqlite or use fallback
    mcp_tools, tool_to_server = await discover_all_mcp_tools()
    is_real = len(tool_to_server) > 0

    # Use Ollama to decide on tool calling
    tool_selector_prompt = (
        f"You are an MCP agent coordinator. You have access to the following tools:\n"
        f"{json.dumps(mcp_tools, indent=2)}\n\n"
        f"Your task: Decide if the user prompt requires a tool. If yes, respond with a JSON object "
        f"specifying the tool 'name' and the 'arguments' to pass to it. "
        f"If no tool is required, respond with 'NO_TOOL'.\n"
        f"Output ONLY the JSON object or the string 'NO_TOOL' with no additional explanation.\n\n"
        f"User Prompt: {prompt}"
    )

    ollama_payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": "You are a tool-calling router. Respond only with JSON or 'NO_TOOL'."},
            {"role": "user", "content": tool_selector_prompt}
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

    # Step 1: Query LLM to see if tool is needed
    tool_needed = False
    selected_tool = None
    tool_args = {}
    tool_output = ""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code == 200:
                response_text = r.json().get("message", {}).get("content", "").strip()
                if "NO_TOOL" not in response_text:
                    # Clean markdown codeblocks if any
                    cleaned_json = re.sub(r'```json\s*(.*?)\s*```', r'\1', response_text, flags=re.DOTALL).strip()
                    try:
                        tool_call = json.loads(cleaned_json)
                        selected_tool = tool_call.get("name")
                        tool_args = tool_call.get("arguments", {})
                        if selected_tool:
                            tool_needed = True
                    except Exception as je:
                        logger.warning(f"Failed to parse LLM tool selection JSON: {je}. Raw: {response_text}")
    except Exception as e:
        logger.error(f"MCP LLM tool routing query failed: {e}")

    # Step 2: If tool is selected, execute it
    if tool_needed:
        logger.info(f"MCP Tool Selected: {selected_tool} with arguments: {tool_args}")
        if is_real and selected_tool in tool_to_server:
            server_name = tool_to_server[selected_tool]
            config = MCP_SERVERS_CONFIG[server_name]
            tool_output = await execute_real_mcp_tool(server_name, config, selected_tool, tool_args)
        else:
            # Fall back to mocked tools
            tool_output = execute_mocked_tool(selected_tool, tool_args)
        logger.info(f"MCP Tool Output: {tool_output}")

        # Step 3: Run final synthesis with the tool output
        synthesis_prompt = (
            f"You are an MCP agent. Answer the user prompt based on the executed tool results.\n\n"
            f"User Prompt: {prompt}\n"
            f"Executed Tool: {selected_tool}\n"
            f"Arguments: {json.dumps(tool_args)}\n"
            f"Tool Output: {tool_output}"
        )
    else:
        # Just answer directly
        synthesis_prompt = (
            f"You are an MCP agent. You determined no tools were needed to answer this query. Answer the user prompt directly.\n\n"
            f"User Prompt: {prompt}"
        )

    synthesis_payload = {
        "model": ollama_payload["model"],
        "messages": [
            {"role": "user", "content": synthesis_prompt}
        ],
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=synthesis_payload)
            if r.status_code == 200:
                final_response = r.json().get("message", {}).get("content", "").strip()
                return {
                    "status": "completed",
                    "mode": "real" if (tool_needed and selected_tool in tool_to_server) else "fallback/mocked",
                    "tool_called": selected_tool if tool_needed else None,
                    "tool_arguments": tool_args if tool_needed else None,
                    "tool_output": tool_output if tool_needed else None,
                    "final_response": final_response
                }
            else:
                raise HTTPException(status_code=502, detail=f"Ollama returned {r.status_code}")
    except Exception as e:
        logger.error(f"MCP final response LLM synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

