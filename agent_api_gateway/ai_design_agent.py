"""
AI Design Agent - Canva-like AI Tool Demo

Open-source AI agent that creates designs by calling third-party APIs.
All API calls go through the security gateway.
"""

import httpx
import json
from typing import Dict, Any, List, Optional


class AIDesignAgent:
    """
    AI agent that helps users create designs (like Canva AI).
    
    Capabilities:
    - Generate images via DALL-E
    - Fetch stock photos from Unsplash
    - Remove backgrounds via Remove.bg
    - Apply filters via Cloudinary
    - Suggest fonts from Google Fonts
    
    All API calls are routed through the security gateway.
    """
    
    def __init__(
        self,
        agent_id: str = "design-agent-001",
        gateway_url: str = "http://localhost:7100"
    ):
        self.agent_id = agent_id
        self.gateway_url = gateway_url
        self.client = httpx.Client(timeout=30.0)
        
        # API keys (in production, use environment variables)
        self.api_keys = {
            "unsplash": "YOUR_UNSPLASH_KEY",
            "remove_bg": "YOUR_REMOVEBG_KEY",
            "openai": "YOUR_OPENAI_KEY",
            "cloudinary": "YOUR_CLOUDINARY_KEY"
        }
    
    def _call_api_through_gateway(
        self,
        target_url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        body: Any = None
    ) -> Dict[str, Any]:
        """
        Call third-party API through security gateway.
        Gateway validates both request and response.
        """
        
        response = self.client.post(
            f"{self.gateway_url}/proxy",
            json={
                "agent_id": self.agent_id,
                "target_url": target_url,
                "method": method,
                "headers": headers or {},
                "params": params,
                "body": body
            }
        )
        
        return response.json()
    
    # ========================================================================
    # DESIGN OPERATIONS
    # ========================================================================
    
    def search_stock_photos(self, query: str, per_page: int = 10) -> Dict[str, Any]:
        """
        Search for stock photos on Unsplash.
        
        Example: agent.search_stock_photos("mountain landscape")
        """
        
        print(f"\n🔍 Searching Unsplash for: {query}")
        
        result = self._call_api_through_gateway(
            target_url="https://api.unsplash.com/search/photos",
            method="GET",
            headers={
                "Authorization": f"Client-ID {self.api_keys['unsplash']}"
            },
            params={
                "query": query,
                "per_page": per_page
            }
        )
        
        if result["success"]:
            print(f"✅ Found photos (sanitized: {result['sanitized']})")
            if result["threats_detected"]:
                print(f"⚠️  Threats detected: {result['threats_detected']}")
        else:
            print(f"❌ Request blocked: {result['request_validation']['details']}")
        
        return result
    
    def generate_ai_image(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """
        Generate image using DALL-E.
        
        Example: agent.generate_ai_image("futuristic city skyline")
        """
        
        print(f"\n🎨 Generating image with DALL-E: {prompt}")
        
        result = self._call_api_through_gateway(
            target_url="https://api.openai.com/v1/images/generations",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_keys['openai']}",
                "Content-Type": "application/json"
            },
            body={
                "prompt": prompt,
                "n": 1,
                "size": size
            }
        )
        
        if result["success"]:
            print(f"✅ Image generated (sanitized: {result['sanitized']})")
            if result["threats_detected"]:
                print(f"⚠️  Threats detected: {result['threats_detected']}")
        else:
            print(f"❌ Request blocked: {result['request_validation']['details']}")
        
        return result
    
    def remove_background(self, image_url: str) -> Dict[str, Any]:
        """
        Remove background from image using Remove.bg.
        
        Example: agent.remove_background("https://example.com/photo.jpg")
        """
        
        print(f"\n✂️  Removing background from image")
        
        result = self._call_api_through_gateway(
            target_url="https://api.remove.bg/v1.0/removebg",
            method="POST",
            headers={
                "X-Api-Key": self.api_keys['remove_bg']
            },
            body={
                "image_url": image_url,
                "size": "auto"
            }
        )
        
        if result["success"]:
            print(f"✅ Background removed (sanitized: {result['sanitized']})")
            if result["threats_detected"]:
                print(f"⚠️  Threats detected: {result['threats_detected']}")
        else:
            print(f"❌ Request blocked: {result['request_validation']['details']}")
        
        return result
    
    def get_font_suggestions(self, category: str = "sans-serif") -> Dict[str, Any]:
        """
        Get font suggestions from Google Fonts.
        
        Example: agent.get_font_suggestions("serif")
        """
        
        print(f"\n📝 Getting {category} font suggestions")
        
        result = self._call_api_through_gateway(
            target_url="https://fonts.googleapis.com/css",
            method="GET",
            params={
                "family": "Roboto|Open+Sans|Lato"
            }
        )
        
        if result["success"]:
            print(f"✅ Fonts retrieved (sanitized: {result['sanitized']})")
            if result["threats_detected"]:
                print(f"⚠️  Threats detected: {result['threats_detected']}")
        else:
            print(f"❌ Request blocked: {result['request_validation']['details']}")
        
        return result
    
    # ========================================================================
    # ATTACK SCENARIOS (FOR TESTING)
    # ========================================================================
    
    def test_malicious_api_call(self):
        """
        Test: Try to call untrusted API (should be blocked)
        """
        
        print("\n🔴 TEST: Attempting to call untrusted API")
        
        result = self._call_api_through_gateway(
            target_url="https://evil-api.com/steal-data",
            method="GET"
        )
        
        print(f"Expected: BLOCKED")
        print(f"Actual: {'BLOCKED' if not result['success'] else 'ALLOWED'}")
        
        return result
    
    def test_sql_injection_in_params(self):
        """
        Test: Try SQL injection in search query (should be blocked)
        """
        
        print("\n🔴 TEST: SQL injection in parameters")
        
        result = self._call_api_through_gateway(
            target_url="https://api.unsplash.com/search/photos",
            method="GET",
            params={
                "query": "landscape' OR '1'='1"
            }
        )
        
        print(f"Expected: BLOCKED")
        print(f"Actual: {'BLOCKED' if not result['success'] else 'ALLOWED'}")
        
        return result
    
    def test_api_key_leak(self):
        """
        Test: Try to leak API key in request (should be blocked)
        """
        
        print("\n🔴 TEST: API key leak attempt")
        
        result = self._call_api_through_gateway(
            target_url="https://api.unsplash.com/search/photos",
            method="GET",
            params={
                "query": "test",
                "api_key": "sk-1234567890abcdef1234567890abcdef"
            }
        )
        
        print(f"Expected: BLOCKED")
        print(f"Actual: {'BLOCKED' if not result['success'] else 'ALLOWED'}")
        
        return result


# ============================================================================
# DEMO SCENARIOS
# ============================================================================

def run_demo():
    """Run demo scenarios"""
    
    print("\n" + "="*60)
    print("🎨 AI Design Agent Demo - Canva-like AI Tool")
    print("="*60)
    
    agent = AIDesignAgent()
    
    print("\n" + "="*60)
    print("SCENARIO 1: Normal Operations")
    print("="*60)
    
    # 1. Search for stock photos
    agent.search_stock_photos("mountain landscape")
    
    # 2. Generate AI image
    agent.generate_ai_image("futuristic city skyline")
    
    # 3. Get font suggestions
    agent.get_font_suggestions("sans-serif")
    
    print("\n" + "="*60)
    print("SCENARIO 2: Security Tests")
    print("="*60)
    
    # Test 1: Untrusted API
    agent.test_malicious_api_call()
    
    # Test 2: SQL Injection
    agent.test_sql_injection_in_params()
    
    # Test 3: API Key Leak
    agent.test_api_key_leak()
    
    print("\n" + "="*60)
    print("✅ Demo Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_demo()
