"""
API Security Validation Service - FastAPI Server

Standalone microservice that ONLY does API security validation.
Any service can call this to validate their API requests.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from security_validator import APISecurityValidator, SecurityDecision

app = FastAPI(
    title="API Security Validation Service",
    description="Dedicated microservice for API security validation - validates ALL API security threats",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize validator
validator = APISecurityValidator()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SecurityValidationRequest(BaseModel):
    """Request to validate API security"""
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    endpoint: str = Field(..., description="API endpoint path")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query/path parameters")
    body: Optional[str] = Field(None, description="Request body (if any)")
    client_id: Optional[str] = Field(None, description="Client/user ID for rate limiting")


class SecurityValidationResponse(BaseModel):
    """Response from security validation"""
    decision: str
    threats_detected: List[str]
    risk_score: int
    details: str
    recommendations: List[str]
    timestamp: str
    safe_to_proceed: bool


class SanitizationRequest(BaseModel):
    """Request to sanitize data"""
    data: Any = Field(..., description="Data to sanitize")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "API Security Validation Service",
        "version": "1.0.0",
        "description": "Validates API requests for security threats",
        "endpoints": {
            "validate": "POST /validate - Validate API request",
            "sanitize": "POST /sanitize - Sanitize sensitive data",
            "headers": "GET /security-headers - Get recommended security headers",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "api-security-validator",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/validate", response_model=SecurityValidationResponse)
async def validate_api_request(request: SecurityValidationRequest):
    """
    Validate an API request for security threats.
    
    This is the main endpoint - validates against:
    - SQL Injection
    - Command Injection
    - Path Traversal
    - SSRF
    - XSS
    - Sensitive Data Exposure
    - Broken Authentication
    - Rate Limiting
    - Schema Validation
    """
    
    result = validator.validate_api_request(
        method=request.method,
        endpoint=request.endpoint,
        headers=request.headers,
        parameters=request.parameters,
        body=request.body,
        client_id=request.client_id
    )
    
    return SecurityValidationResponse(
        decision=result.decision,
        threats_detected=[t.value for t in result.threats_detected],
        risk_score=result.risk_score,
        details=result.details,
        recommendations=result.recommendations,
        timestamp=result.timestamp.isoformat(),
        safe_to_proceed=(result.decision == SecurityDecision.ALLOW)
    )


@app.post("/sanitize")
async def sanitize_data(request: SanitizationRequest):
    """
    Sanitize data to remove sensitive information.
    
    Masks:
    - Credit card numbers
    - SSN
    - API keys
    - Passwords
    - JWT tokens
    - AWS keys
    """
    
    sanitized = validator.sanitize_output(request.data)
    
    return {
        "original_type": type(request.data).__name__,
        "sanitized_data": sanitized,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/security-headers")
async def get_security_headers():
    """
    Get recommended security headers for API responses.
    
    Returns headers that should be included in all API responses
    to prevent common attacks.
    """
    
    headers = validator.get_security_headers()
    
    return {
        "headers": headers,
        "description": "Add these headers to all API responses",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/validate-batch")
async def validate_batch(requests: List[SecurityValidationRequest]):
    """
    Validate multiple API requests in batch.
    Useful for validating a sequence of operations.
    """
    
    results = []
    
    for req in requests:
        result = validator.validate_api_request(
            method=req.method,
            endpoint=req.endpoint,
            headers=req.headers,
            parameters=req.parameters,
            body=req.body,
            client_id=req.client_id
        )
        
        results.append({
            "endpoint": req.endpoint,
            "decision": result.decision,
            "risk_score": result.risk_score,
            "threats": [t.value for t in result.threats_detected],
            "safe": result.decision == SecurityDecision.ALLOW
        })
    
    # Overall decision
    any_denied = any(r["decision"] == SecurityDecision.DENY for r in results)
    total_risk = sum(r["risk_score"] for r in results)
    
    return {
        "results": results,
        "overall_decision": "DENY" if any_denied else "ALLOW",
        "total_risk_score": total_risk,
        "safe_to_proceed": not any_denied,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/threats")
async def list_threat_types():
    """List all threat types this service can detect"""
    from security_validator import ThreatType
    
    return {
        "threat_types": [
            {
                "type": threat.value,
                "description": threat.name.replace("_", " ").title()
            }
            for threat in ThreatType
        ],
        "total_threats": len(ThreatType)
    }


@app.get("/stats")
async def get_statistics():
    """Get validation statistics"""
    # In production, track actual stats
    return {
        "service": "api-security-validator",
        "uptime": "operational",
        "threats_detected_today": 0,
        "requests_validated_today": 0,
        "average_risk_score": 0
    }


# ============================================================================
# MIDDLEWARE FOR AUTOMATIC VALIDATION
# ============================================================================

@app.middleware("http")
async def validate_incoming_requests(request: Request, call_next):
    """
    Middleware to automatically validate all incoming requests.
    This demonstrates how to use the validator as middleware.
    """
    
    # Skip validation for docs and health endpoints
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Extract request details
    headers = dict(request.headers)
    
    # Get query parameters
    params = dict(request.query_params)
    
    # Validate
    result = validator.validate_api_request(
        method=request.method,
        endpoint=request.url.path,
        headers=headers,
        parameters=params,
        client_id=headers.get("x-client-id")
    )
    
    # If denied, return error
    if result.decision == SecurityDecision.DENY:
        return {
            "error": "Security validation failed",
            "details": result.details,
            "threats": [t.value for t in result.threats_detected],
            "risk_score": result.risk_score
        }
    
    # Add security headers to response
    response = await call_next(request)
    
    security_headers = validator.get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("\n" + "="*60)
    print("🛡️  API Security Validation Service")
    print("="*60)
    print("✅ Security Validator initialized")
    print("✅ Threat detection active")
    print("="*60)
    print("🚀 Service ready to validate API requests")
    print("="*60 + "\n")


if __name__ == "__main__":
    import uvicorn
    print("\n🛡️  Starting API Security Validation Service...")
    print("📍 URL: http://localhost:9000")
    print("📚 Docs: http://localhost:9000/docs\n")
    
    uvicorn.run(app, host="0.0.0.0", port=9000)
