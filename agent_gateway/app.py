"""
Agent Security Gateway - Real-Time API Security System
Port 8002

This is a PRODUCTION-GRADE security gateway that:
- Inspects live AI agent requests
- Enforces 5 core security controls
- Blocks malicious calls in real-time
- Logs all security decisions
- Provides WebSocket updates for dashboard

NO SIMULATION - This is a real security system.
"""

from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
import json
import asyncio
from enum import Enum

from controls.schema_validator import SchemaValidator
from controls.agent_identity import AgentIdentityEnforcer
from controls.parameter_guards import ParameterGuardrails
from controls.taint_tracker import TaintTracker
from controls.rate_limiter import RateLimiter
from models.security_event import SecurityEvent, SecurityDecision

app = FastAPI(
    title="Agent Security Gateway",
    description="Real-time API security for AI agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize security controls
schema_validator = SchemaValidator()
agent_identity = AgentIdentityEnforcer()
parameter_guards = ParameterGuardrails()
taint_tracker = TaintTracker()
rate_limiter = RateLimiter()

# WebSocket connections for real-time dashboard
active_connections: List[WebSocket] = []

# Security event log (in-memory for demo, use DB in production)
security_events: List[Dict[str, Any]] = []


class AgentRequest(BaseModel):
    """Request from AI agent"""
    endpoint: str = Field(..., description="Target API endpoint")
    method: str = Field(default="GET", description="HTTP method")
    params: Dict[str, Any] = Field(default_factory=dict, description="Request parameters")
    user_prompt: Optional[str] = Field(None, description="Original user prompt")
    agent_reasoning: Optional[str] = Field(None, description="Agent's reasoning")


class GatewayResponse(BaseModel):
    """Gateway decision response"""
    allowed: bool
    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    security_checks: Dict[str, Any]
    forwarded_response: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: str


@app.get("/")
async def root():
    """Gateway information"""
    return {
        "service": "Agent Security Gateway",
        "version": "1.0.0",
        "status": "operational",
        "controls": [
            "Schema Validation",
            "Agent Identity Enforcement",
            "Parameter Guardrails",
            "Taint Tracking",
            "Rate Limiting"
        ],
        "mode": "PRODUCTION (Real-time enforcement)"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": len(active_connections),
        "total_events": len(security_events)
    }


@app.post("/gateway/secure", response_model=GatewayResponse)
async def secure_gateway(
    request: AgentRequest,
    x_agent_id: str = Header(..., description="Agent identifier"),
    x_request_id: Optional[str] = Header(None, description="Request tracking ID")
):
    """
    Main security gateway endpoint - Real-time enforcement
    
    Flow:
    1. Schema Validation
    2. Agent Identity Check
    3. Parameter Guardrails
    4. Taint Tracking
    5. Rate Limiting
    6. Forward to Consumer API (if allowed)
    """
    
    request_id = x_request_id or f"req_{datetime.utcnow().timestamp()}"
    timestamp = datetime.utcnow().isoformat()
    
    security_checks = {
        "schema_validation": {"passed": False, "details": None},
        "agent_identity": {"passed": False, "details": None},
        "parameter_guards": {"passed": False, "details": None},
        "taint_tracking": {"passed": False, "details": None},
        "rate_limiting": {"passed": False, "details": None}
    }
    
    # Track tainted data from user prompt
    tainted_fields = []
    if request.user_prompt:
        tainted_fields = taint_tracker.mark_tainted_fields(
            request.params,
            request.user_prompt
        )
    
    try:
        # 1️⃣ SCHEMA VALIDATION
        schema_result = schema_validator.validate(
            endpoint=request.endpoint,
            params=request.params
        )
        security_checks["schema_validation"] = {
            "passed": schema_result.valid,
            "details": schema_result.message,
            "violations": schema_result.violations
        }
        
        if not schema_result.valid:
            await log_security_event(
                request_id=request_id,
                agent_id=x_agent_id,
                blocked_by="schema_validation",
                reason=schema_result.message,
                request_data=request.dict()
            )
            
            return GatewayResponse(
                allowed=False,
                blocked_by="Schema Validation",
                reason=schema_result.message,
                security_checks=security_checks,
                timestamp=timestamp,
                request_id=request_id
            )
        
        # 2️⃣ AGENT IDENTITY ENFORCEMENT
        identity_result = agent_identity.check_permission(
            agent_id=x_agent_id,
            endpoint=request.endpoint,
            method=request.method
        )
        security_checks["agent_identity"] = {
            "passed": identity_result.allowed,
            "details": identity_result.message,
            "agent_id": x_agent_id
        }
        
        if not identity_result.allowed:
            await log_security_event(
                request_id=request_id,
                agent_id=x_agent_id,
                blocked_by="agent_identity",
                reason=identity_result.message,
                request_data=request.dict()
            )
            
            return GatewayResponse(
                allowed=False,
                blocked_by="Agent Identity",
                reason=identity_result.message,
                security_checks=security_checks,
                timestamp=timestamp,
                request_id=request_id
            )
        
        # 3️⃣ PARAMETER GUARDRAILS
        guardrail_result = parameter_guards.check_limits(
            endpoint=request.endpoint,
            params=request.params
        )
        security_checks["parameter_guards"] = {
            "passed": guardrail_result.passed,
            "details": guardrail_result.message,
            "violations": guardrail_result.violations
        }
        
        if not guardrail_result.passed:
            await log_security_event(
                request_id=request_id,
                agent_id=x_agent_id,
                blocked_by="parameter_guardrails",
                reason=guardrail_result.message,
                request_data=request.dict()
            )
            
            return GatewayResponse(
                allowed=False,
                blocked_by="Parameter Guardrails",
                reason=guardrail_result.message,
                security_checks=security_checks,
                timestamp=timestamp,
                request_id=request_id
            )
        
        # 4️⃣ TAINT TRACKING
        taint_result = taint_tracker.check_tainted_sensitive(
            endpoint=request.endpoint,
            params=request.params,
            tainted_fields=tainted_fields
        )
        security_checks["taint_tracking"] = {
            "passed": taint_result.safe,
            "details": taint_result.message,
            "tainted_fields": tainted_fields,
            "requires_approval": taint_result.requires_approval
        }
        
        if not taint_result.safe:
            await log_security_event(
                request_id=request_id,
                agent_id=x_agent_id,
                blocked_by="taint_tracking",
                reason=taint_result.message,
                request_data=request.dict(),
                tainted_fields=tainted_fields
            )
            
            return GatewayResponse(
                allowed=False,
                blocked_by="Taint Tracking",
                reason=taint_result.message,
                security_checks=security_checks,
                timestamp=timestamp,
                request_id=request_id
            )
        
        # 5️⃣ RATE LIMITING
        rate_result = rate_limiter.check_rate(
            agent_id=x_agent_id,
            endpoint=request.endpoint
        )
        security_checks["rate_limiting"] = {
            "passed": rate_result.allowed,
            "details": rate_result.message,
            "current_rate": rate_result.current_count,
            "limit": rate_result.limit
        }
        
        if not rate_result.allowed:
            await log_security_event(
                request_id=request_id,
                agent_id=x_agent_id,
                blocked_by="rate_limiting",
                reason=rate_result.message,
                request_data=request.dict()
            )
            
            return GatewayResponse(
                allowed=False,
                blocked_by="Rate Limiting",
                reason=rate_result.message,
                security_checks=security_checks,
                timestamp=timestamp,
                request_id=request_id
            )
        
        # ✅ ALL CHECKS PASSED - Forward to Consumer API
        consumer_response = await forward_to_consumer_api(
            endpoint=request.endpoint,
            method=request.method,
            params=request.params
        )
        
        await log_security_event(
            request_id=request_id,
            agent_id=x_agent_id,
            blocked_by=None,
            reason="All security checks passed",
            request_data=request.dict(),
            allowed=True
        )
        
        return GatewayResponse(
            allowed=True,
            blocked_by=None,
            reason="Request approved and forwarded",
            security_checks=security_checks,
            forwarded_response=consumer_response,
            timestamp=timestamp,
            request_id=request_id
        )
        
    except Exception as e:
        await log_security_event(
            request_id=request_id,
            agent_id=x_agent_id,
            blocked_by="system_error",
            reason=str(e),
            request_data=request.dict()
        )
        
        raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")


async def forward_to_consumer_api(endpoint: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Forward approved request to Consumer API"""
    consumer_url = f"http://localhost:8001{endpoint}"
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(consumer_url, params=params)
        elif method == "POST":
            response = await client.post(consumer_url, json=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response.json()


async def log_security_event(
    request_id: str,
    agent_id: str,
    blocked_by: Optional[str],
    reason: str,
    request_data: Dict[str, Any],
    allowed: bool = False,
    tainted_fields: List[str] = None
):
    """Log security event and broadcast to WebSocket clients"""
    event = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": agent_id,
        "allowed": allowed,
        "blocked_by": blocked_by,
        "reason": reason,
        "request_data": request_data,
        "tainted_fields": tainted_fields or []
    }
    
    security_events.append(event)
    
    # Broadcast to all connected WebSocket clients
    await broadcast_event(event)


async def broadcast_event(event: Dict[str, Any]):
    """Broadcast security event to all WebSocket connections"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(event)
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        active_connections.remove(conn)


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time security events"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send recent events on connect
        recent_events = security_events[-50:] if len(security_events) > 50 else security_events
        await websocket.send_json({
            "type": "history",
            "events": recent_events
        })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/events")
async def get_events(limit: int = 100):
    """Get recent security events"""
    return {
        "total": len(security_events),
        "events": security_events[-limit:]
    }


@app.get("/stats")
async def get_stats():
    """Get security statistics"""
    total = len(security_events)
    blocked = sum(1 for e in security_events if not e["allowed"])
    allowed = total - blocked
    
    blocks_by_control = {}
    for event in security_events:
        if event["blocked_by"]:
            blocks_by_control[event["blocked_by"]] = blocks_by_control.get(event["blocked_by"], 0) + 1
    
    return {
        "total_requests": total,
        "allowed": allowed,
        "blocked": blocked,
        "block_rate": (blocked / total * 100) if total > 0 else 0,
        "blocks_by_control": blocks_by_control,
        "active_websocket_connections": len(active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    print("🛡️  Agent Security Gateway starting...")
    print("📊 Real-time enforcement enabled")
    print("🔒 5 security controls active")
    print("🌐 WebSocket monitoring on /ws/events")
    uvicorn.run(app, host="0.0.0.0", port=8002)
