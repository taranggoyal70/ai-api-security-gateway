"""
Vendor API - Untrusted Third-Party Service
===========================================
This simulates a malicious or compromised vendor API that returns
potentially dangerous XSS payloads in its responses.

OWASP API Security Top 10 (2023) #10: Unsafe Consumption of APIs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

app = FastAPI(
    title="Vendor API (Untrusted)",
    description="Simulated third-party vendor API returning malicious payloads",
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

# XSS Payload Variants
XSS_PAYLOADS = {
    "script_tag": "<script>alert('Hacked by Vendor API!')</script>",
    "img_onerror": "<img src=x onerror=alert('Hacked by Vendor API!')>",
    "svg_onload": "<svg onload=alert('Hacked by Vendor API!')></svg>",
    "onclick_requires_user": "<button onclick=alert('Hacked by Vendor API!')>Click me to trigger XSS</button>",
    "link_js_scheme": "<a href=javascript:alert('Hacked by Vendor API!')>Click this link</a>",
    "html_injection_no_js": "<b style='color:red;font-size:24px'>🎬 FREE MOVIE DOWNLOAD 🎬</b>"
}

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Vendor API (Untrusted Third-Party)",
        "warning": "⚠️ This API returns malicious payloads for security testing",
        "endpoints": {
            "catalog": "/vendor/catalog/title/{id}",
            "health": "/health"
        },
        "supported_variants": list(XSS_PAYLOADS.keys())
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vendor_api",
        "warning": "Returns malicious payloads"
    }

@app.get("/vendor/catalog/title/{id}")
async def get_catalog_title(
    id: int,
    mode: str = Query(default="xss", description="Attack mode"),
    variant: str = Query(default="img_onerror", description="XSS variant")
):
    """
    Vendor catalog endpoint - Returns product titles with XSS payloads
    
    This simulates a compromised or malicious vendor API that injects
    XSS payloads into legitimate-looking data fields.
    
    Args:
        id: Product ID (only 101 is valid for demo)
        mode: Attack mode (currently only 'xss' supported)
        variant: Type of XSS payload to inject
    
    Returns:
        JSON with malicious payload in 'title' field
    """
    
    # Only support ID 101 for demo
    if id != 101:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Product not found",
                "id": id,
                "message": "Only ID 101 is available in this demo"
            }
        )
    
    # Validate variant
    if variant not in XSS_PAYLOADS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid variant",
                "variant": variant,
                "supported_variants": list(XSS_PAYLOADS.keys())
            }
        )
    
    # Get the malicious payload
    malicious_title = XSS_PAYLOADS[variant]
    
    # Return response with XSS payload embedded in title
    return {
        "id": id,
        "title": malicious_title,  # ⚠️ MALICIOUS PAYLOAD HERE
        "description": "Vendor provided data. Do not trust this content!",
        "source": "vendor_api",
        "mode": mode,
        "variant": variant,
        "warning": "⚠️ This response contains a malicious XSS payload for security testing"
    }

if __name__ == "__main__":
    print("=" * 70)
    print("🔴 VENDOR API - UNTRUSTED THIRD-PARTY SERVICE")
    print("=" * 70)
    print("⚠️  WARNING: This API returns malicious XSS payloads")
    print("📍 Running on: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000)
