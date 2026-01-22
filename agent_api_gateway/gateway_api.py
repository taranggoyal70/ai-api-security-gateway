"""
Agent-to-API Security Gateway - FastAPI Service

Real-time proxy that intercepts AI agent calls to third-party APIs.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import asyncio

from gateway_core import AgentAPIGateway, ValidationDecision

app = FastAPI(
    title="Agent-to-API Security Gateway",
    description="Real-time interception and validation for AI agents calling third-party APIs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize gateway
gateway = AgentAPIGateway()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ProxyRequest(BaseModel):
    """Request to proxy an API call through the gateway"""
    agent_id: str = Field(..., description="ID of the AI agent making the call")
    target_url: str = Field(..., description="Third-party API URL")
    method: str = Field(default="GET", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    body: Optional[Any] = Field(None, description="Request body")


class ProxyResponse(BaseModel):
    """Response from proxied API call"""
    success: bool
    request_validation: Dict[str, Any]
    response_validation: Optional[Dict[str, Any]]
    response_data: Optional[Any]
    threats_detected: List[str]
    sanitized: bool
    timestamp: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agent-to-API Security Gateway",
        "version": "1.0.0",
        "description": "Real-time interception for AI agents calling third-party APIs",
        "features": [
            "Bidirectional validation (request + response)",
            "API allowlist enforcement",
            "Threat detection in responses",
            "PII sanitization",
            "Real-time monitoring"
        ],
        "endpoints": {
            "proxy": "POST /proxy - Proxy API call through gateway",
            "trusted-apis": "GET /trusted-apis - List trusted APIs",
            "audit-log": "GET /audit-log - View audit log",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "agent-api-gateway",
        "trusted_apis": len(gateway.trusted_apis),
        "total_requests": len(gateway.request_log)
    }


@app.post("/proxy", response_model=ProxyResponse)
async def proxy_api_call(request: ProxyRequest):
    """
    Main proxy endpoint - intercepts AI agent API calls.
    
    Flow:
    1. Validate outgoing request
    2. Forward to third-party API
    3. Validate incoming response
    4. Sanitize if needed
    5. Return to agent
    """
    
    result = await gateway.intercept_api_call(
        agent_id=request.agent_id,
        target_url=request.target_url,
        method=request.method,
        headers=request.headers,
        params=request.params,
        body=request.body
    )
    
    return ProxyResponse(**result)


@app.get("/trusted-apis")
async def get_trusted_apis():
    """Get list of trusted third-party APIs"""
    
    apis = []
    for domain, config in gateway.trusted_apis.items():
        apis.append({
            "domain": domain,
            "name": config["name"],
            "risk_level": config["risk_level"],
            "allowed_endpoints": config["allowed_endpoints"],
            "rate_limit": config["rate_limit"]
        })
    
    return {
        "trusted_apis": apis,
        "total": len(apis)
    }


@app.post("/trusted-apis/add")
async def add_trusted_api(
    domain: str,
    name: str,
    risk_level: str,
    allowed_endpoints: List[str],
    rate_limit: int = 100
):
    """Add a new trusted API to the allowlist"""
    
    gateway.trusted_apis[domain] = {
        "name": name,
        "risk_level": risk_level,
        "allowed_endpoints": allowed_endpoints,
        "rate_limit": rate_limit
    }
    
    return {
        "success": True,
        "message": f"Added {name} to trusted APIs",
        "domain": domain
    }


@app.get("/audit-log")
async def get_audit_log(limit: int = 100):
    """Get audit log of API calls"""
    
    log = gateway.get_audit_log(limit=limit)
    
    # Calculate statistics
    total = len(log)
    successful = sum(1 for entry in log if entry["success"])
    with_threats = sum(1 for entry in log if entry["threats"])
    sanitized = sum(1 for entry in log if entry["sanitized"])
    
    return {
        "audit_log": log,
        "statistics": {
            "total_requests": total,
            "successful": successful,
            "blocked": total - successful,
            "threats_detected": with_threats,
            "sanitized": sanitized
        }
    }


@app.get("/audit-log/agent/{agent_id}")
async def get_agent_audit_log(agent_id: str, limit: int = 50):
    """Get audit log for specific agent"""
    
    log = gateway.get_audit_log(limit=1000)
    agent_log = [entry for entry in log if entry["agent_id"] == agent_id][-limit:]
    
    return {
        "agent_id": agent_id,
        "audit_log": agent_log,
        "total_requests": len(agent_log)
    }


@app.get("/threats")
async def get_threat_statistics():
    """Get threat detection statistics"""
    
    log = gateway.get_audit_log(limit=1000)
    
    threat_counts = {}
    for entry in log:
        for threat in entry["threats"]:
            threat_counts[threat] = threat_counts.get(threat, 0) + 1
    
    return {
        "threat_statistics": threat_counts,
        "total_threats_detected": sum(threat_counts.values()),
        "unique_threat_types": len(threat_counts)
    }


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("\n" + "="*60)
    print("🛡️  Agent-to-API Security Gateway")
    print("="*60)
    print(f"✅ Gateway initialized")
    print(f"✅ {len(gateway.trusted_apis)} trusted APIs configured")
    print("="*60)
    print("🚀 Ready to intercept agent API calls")
    print("="*60 + "\n")


if __name__ == "__main__":
    import uvicorn
    print("\n🛡️  Starting Agent-to-API Security Gateway...")
    print("📍 URL: http://localhost:7100")
    print("📚 Docs: http://localhost:7100/docs\n")
    
    uvicorn.run(app, host="0.0.0.0", port=7100)
