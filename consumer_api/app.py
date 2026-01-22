"""
Consumer API - Internal Backend Service
========================================
This is YOUR internal API that consumes data from the untrusted vendor API.

Demonstrates OWASP API Security Top 10 (2023) #10: Unsafe Consumption of APIs

Two flows:
1. UNSAFE - Directly forwards vendor data without validation/encoding
2. SAFE - Applies security controls before forwarding to UI
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx
import uvicorn
from typing import Optional

from security import (
    sanitize_vendor_data,
    get_log_tail,
    log_security_event
)

app = FastAPI(
    title="Consumer API (Internal)",
    description="Internal API demonstrating safe vs unsafe consumption of vendor APIs",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VENDOR_API_BASE = "http://localhost:8000"

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Consumer API (Internal)",
        "purpose": "Demonstrates safe vs unsafe consumption of third-party APIs",
        "endpoints": {
            "unsafe": "/sync/unsafe/{id}",
            "safe": "/sync/safe/{id}",
            "health": "/health"
        },
        "vendor_api": VENDOR_API_BASE,
        "security_controls": [
            "Output Encoding (HTML entity encoding)",
            "Security Event Logging",
            "Vendor Error Handling"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "consumer_api",
        "vendor_reachable": await check_vendor_health()
    }

async def check_vendor_health() -> bool:
    """Check if vendor API is reachable"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{VENDOR_API_BASE}/health")
            return response.status_code == 200
    except Exception:
        return False

async def fetch_vendor_data(id: int, mode: str, variant: str) -> dict:
    """
    Fetch data from vendor API
    
    Args:
        id: Product ID
        mode: Attack mode
        variant: XSS variant
        
    Returns:
        Vendor API response JSON
        
    Raises:
        HTTPException: If vendor API fails
    """
    vendor_url = f"{VENDOR_API_BASE}/vendor/catalog/title/{id}"
    params = {"mode": mode, "variant": variant}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(vendor_url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "error": "Vendor API error",
                "vendor_status": e.response.status_code,
                "vendor_response": e.response.json() if e.response.text else None
            }
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Vendor API unreachable",
                "message": str(e),
                "vendor_url": vendor_url
            }
        )

@app.get("/sync/unsafe/{id}")
async def unsafe_flow(
    id: int,
    mode: str = Query(default="xss"),
    variant: str = Query(default="img_onerror")
):
    """
    ⚠️ UNSAFE FLOW - No security controls applied
    
    This endpoint demonstrates UNSAFE consumption of third-party APIs:
    - Fetches vendor data
    - Returns it DIRECTLY without validation or encoding
    - No logging of security events
    - No error handling for vendor failures
    
    This is VULNERABLE to XSS attacks when the UI renders the data.
    
    Args:
        id: Product ID
        mode: Attack mode
        variant: XSS variant
        
    Returns:
        Unmodified vendor data (DANGEROUS!)
    """
    timestamp = datetime.now().isoformat()
    vendor_url = f"{VENDOR_API_BASE}/vendor/catalog/title/{id}?mode={mode}&variant={variant}"
    
    # Fetch vendor data
    vendor_data = await fetch_vendor_data(id, mode, variant)
    
    # ⚠️ UNSAFE: Return vendor data directly without any security controls
    return {
        "request": {
            "flow": "unsafe",
            "vendor_url": vendor_url,
            "timestamp": timestamp,
            "status": 200
        },
        "vendor_raw": vendor_data,
        "controls": {
            "output_encoding": "Not Available",
            "logging": "Not Available",
            "vendor_error_handling": "Not Available"
        },
        "result": vendor_data,  # ⚠️ DANGEROUS: Unmodified vendor data
        "evidence": {
            "log_tail": []  # No logging in unsafe flow
        }
    }

@app.get("/sync/safe/{id}")
async def safe_flow(
    id: int,
    mode: str = Query(default="xss"),
    variant: str = Query(default="img_onerror")
):
    """
    ✅ SAFE FLOW - Security controls applied
    
    This endpoint demonstrates SAFE consumption of third-party APIs:
    - Fetches vendor data
    - Applies HTML encoding to neutralize XSS payloads
    - Logs security events for audit trail
    - Handles vendor errors gracefully
    
    This protects against XSS attacks from untrusted vendor data.
    
    Args:
        id: Product ID
        mode: Attack mode
        variant: XSS variant
        
    Returns:
        Sanitized vendor data with security controls applied
    """
    timestamp = datetime.now().isoformat()
    vendor_url = f"{VENDOR_API_BASE}/vendor/catalog/title/{id}?mode={mode}&variant={variant}"
    
    # Initialize vendor error handling state
    vendor_error_triggered = False
    
    try:
        # Fetch vendor data
        vendor_data = await fetch_vendor_data(id, mode, variant)
        
        # ✅ SAFE: Apply security controls
        sanitized_data, controls = sanitize_vendor_data(vendor_data, is_safe_flow=True)
        
        # Get recent security logs
        log_tail = get_log_tail(lines=10)
        
        return {
            "request": {
                "flow": "safe",
                "vendor_url": vendor_url,
                "timestamp": timestamp,
                "status": 200
            },
            "vendor_raw": vendor_data,
            "controls": controls,
            "result": sanitized_data,  # ✅ SAFE: Encoded data
            "evidence": {
                "log_tail": [line.strip() for line in log_tail]
            }
        }
        
    except HTTPException as e:
        # ✅ Vendor error handling triggered
        vendor_error_triggered = True
        
        # Log the vendor error
        log_security_event("vendor_error", {
            "id": id,
            "variant": variant,
            "error": str(e.detail)
        })
        
        # Return clean error response
        return {
            "request": {
                "flow": "safe",
                "vendor_url": vendor_url,
                "timestamp": timestamp,
                "status": e.status_code
            },
            "vendor_raw": None,
            "controls": {
                "output_encoding": "Not Applied",
                "logging": "Applied",
                "vendor_error_handling": "Triggered"
            },
            "result": {
                "error": "Vendor API error",
                "message": "Failed to fetch data from vendor. Error has been logged.",
                "safe_fallback": True
            },
            "evidence": {
                "log_tail": [line.strip() for line in get_log_tail(lines=10)]
            }
        }

if __name__ == "__main__":
    print("=" * 70)
    print("🟢 CONSUMER API - INTERNAL BACKEND SERVICE")
    print("=" * 70)
    print("✅ Implements security controls for safe API consumption")
    print("📍 Running on: http://localhost:8001")
    print("📚 Docs: http://localhost:8001/docs")
    print("🔗 Vendor API: http://localhost:8000")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8001)
