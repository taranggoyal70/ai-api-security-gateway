"""
Agent API Server

FastAPI server that exposes the AI agent via HTTP endpoints.
This allows the dashboard to interact with the agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from agent_client import SecurityAwareAgent
from agent_client_ollama import OllamaSecurityAgent

app = FastAPI(
    title="AI Agent API",
    description="HTTP API for AI agent with security gateway integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    agent_id: str = "support-bot"
    use_ollama: bool = False
    ollama_model: str = "llama3.2"


class AgentResponse(BaseModel):
    success: bool
    agent_response: Optional[str] = None
    tool_calls: list = []
    error: Optional[str] = None


@app.get("/")
async def root():
    return {
        "service": "AI Agent API",
        "status": "running",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY"))
    }


@app.post("/agent/prompt", response_model=AgentResponse)
async def process_agent_prompt(request: PromptRequest):
    """
    Process a user prompt through the AI agent.
    Supports both OpenAI (cloud) and Ollama (local).
    """
    if request.use_ollama:
        # Use Ollama (local, no API key needed)
        agent = OllamaSecurityAgent(
            agent_id=request.agent_id,
            model=request.ollama_model
        )
    else:
        # Use OpenAI (cloud, requires API key)
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable or use Ollama."
            )
        agent = SecurityAwareAgent(agent_id=request.agent_id)
    
    result = await agent.process_prompt(request.prompt)
    
    if result.get("error"):
        return AgentResponse(
            success=False,
            error=result["error"]
        )
    
    return AgentResponse(
        success=True,
        agent_response=result.get("agent_response"),
        tool_calls=result.get("tool_calls", [])
    )


@app.get("/agent/tools")
async def get_available_tools():
    """Get list of available tools/functions the agent can use"""
    agent = SecurityAwareAgent(agent_id="demo")
    return {
        "tools": agent.tools
    }


if __name__ == "__main__":
    import uvicorn
    print("\n🤖 Starting AI Agent API Server...")
    print("📍 URL: http://localhost:8003")
    print("📚 Docs: http://localhost:8003/docs")
    print("\n⚠️  Make sure OPENAI_API_KEY is set!\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
