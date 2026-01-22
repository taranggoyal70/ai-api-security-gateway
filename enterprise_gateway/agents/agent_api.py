"""
Agent API Server

FastAPI server that exposes AI agents via HTTP.
Allows the dashboard to interact with agents.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from multi_agent_system import OpenAIAgent, OllamaAgent, AgentProvider

app = FastAPI(
    title="Enterprise AI Agent API",
    description="Secure AI agents with gateway integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentPromptRequest(BaseModel):
    prompt: str
    agent_id: str = "support-agent"
    provider: str = "ollama"  # "openai" or "ollama"
    model: Optional[str] = None


class AgentResponse(BaseModel):
    success: bool
    agent_id: str
    provider: str
    agent_response: Optional[str] = None
    tool_calls: list = []
    error: Optional[str] = None


@app.get("/")
async def root():
    return {
        "service": "Enterprise AI Agent API",
        "status": "running",
        "providers": ["openai", "ollama"],
        "gateway_url": "http://localhost:8004"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "ollama_available": True  # Could check Ollama connectivity
    }


@app.post("/agent/prompt", response_model=AgentResponse)
async def process_agent_prompt(request: AgentPromptRequest):
    """
    Process a user prompt through an AI agent.
    The agent will decide which tools to call and send them through the security gateway.
    """
    
    try:
        # Create appropriate agent
        if request.provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise HTTPException(
                    status_code=500,
                    detail="OpenAI API key not configured. Use Ollama or set OPENAI_API_KEY."
                )
            agent = OpenAIAgent(
                agent_id=request.agent_id,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        else:  # ollama
            agent = OllamaAgent(
                agent_id=request.agent_id,
                model=request.model or "llama3.2"
            )
        
        # Process the prompt
        result = await agent.process_prompt(request.prompt)
        
        if "error" in result:
            return AgentResponse(
                success=False,
                agent_id=request.agent_id,
                provider=request.provider,
                error=result["error"]
            )
        
        return AgentResponse(
            success=True,
            agent_id=result.get("agent_id", request.agent_id),
            provider=result.get("provider", request.provider),
            agent_response=result.get("agent_response"),
            tool_calls=result.get("tool_calls", [])
        )
    
    except Exception as e:
        return AgentResponse(
            success=False,
            agent_id=request.agent_id,
            provider=request.provider,
            error=str(e)
        )


@app.get("/agents/available")
async def get_available_agents():
    """Get list of available agent roles"""
    return {
        "agents": [
            {
                "id": "support-agent",
                "name": "Customer Support Agent",
                "description": "Helps with customer inquiries and creates tickets",
                "tools": ["search_knowledge_base", "create_support_ticket", "get_customer_info"]
            },
            {
                "id": "refund-agent",
                "name": "Refund & Billing Agent",
                "description": "Processes refunds and handles billing",
                "tools": ["lookup_order", "issue_refund", "check_payment_status"]
            },
            {
                "id": "admin-agent",
                "name": "Admin & DevOps Assistant",
                "description": "System diagnostics and controlled operations",
                "tools": ["get_system_health", "view_logs", "run_diagnostic", "restart_service"]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("\n🤖 Starting Enterprise AI Agent API...")
    print("📍 URL: http://localhost:8005")
    print("📚 Docs: http://localhost:8005/docs")
    print("🔗 Gateway: http://localhost:8004\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8005)
