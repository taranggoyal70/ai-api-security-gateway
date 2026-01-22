"""
API Security SDK

Easy-to-use SDK for integrating API security validation into any service.
Just wrap your API calls with this SDK and get automatic security validation.
"""

import httpx
from typing import Dict, Any, Optional, Callable
from functools import wraps


class APISecuritySDK:
    """
    SDK for integrating API security validation.
    
    Usage:
        security = APISecuritySDK(validator_url="http://localhost:9000")
        
        # Validate before making API call
        result = security.validate(method="POST", endpoint="/api/users", params={...})
        if result["safe_to_proceed"]:
            # Make actual API call
            pass
    """
    
    def __init__(self, validator_url: str = "http://localhost:9000"):
        self.validator_url = validator_url
        self.client = httpx.Client(timeout=5.0)
    
    def validate(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str] = None,
        parameters: Dict[str, Any] = None,
        body: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate an API request before execution.
        
        Returns:
            {
                "safe_to_proceed": bool,
                "decision": str,
                "risk_score": int,
                "threats_detected": list,
                "recommendations": list
            }
        """
        
        try:
            response = self.client.post(
                f"{self.validator_url}/validate",
                json={
                    "method": method,
                    "endpoint": endpoint,
                    "headers": headers or {},
                    "parameters": parameters or {},
                    "body": body,
                    "client_id": client_id
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "safe_to_proceed": False,
                    "decision": "DENY",
                    "risk_score": 100,
                    "threats_detected": ["validation_service_error"],
                    "details": f"Validator returned {response.status_code}"
                }
        
        except Exception as e:
            # If validator is down, fail open or closed based on config
            # For security, default to DENY
            return {
                "safe_to_proceed": False,
                "decision": "DENY",
                "risk_score": 100,
                "threats_detected": ["validator_unavailable"],
                "details": str(e)
            }
    
    def sanitize(self, data: Any) -> Any:
        """Sanitize sensitive data"""
        
        try:
            response = self.client.post(
                f"{self.validator_url}/sanitize",
                json={"data": data}
            )
            
            if response.status_code == 200:
                return response.json()["sanitized_data"]
            else:
                return data  # Return original if sanitization fails
        
        except Exception:
            return data
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers"""
        
        try:
            response = self.client.get(f"{self.validator_url}/security-headers")
            
            if response.status_code == 200:
                return response.json()["headers"]
            else:
                return {}
        
        except Exception:
            return {}
    
    def validate_batch(self, requests: list) -> Dict[str, Any]:
        """Validate multiple requests"""
        
        try:
            response = self.client.post(
                f"{self.validator_url}/validate-batch",
                json=requests
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"safe_to_proceed": False}
        
        except Exception as e:
            return {"safe_to_proceed": False, "error": str(e)}


# ============================================================================
# DECORATOR FOR AUTOMATIC VALIDATION
# ============================================================================

def secure_api_call(validator_url: str = "http://localhost:9000"):
    """
    Decorator to automatically validate API calls.
    
    Usage:
        @secure_api_call()
        def my_api_function(method, endpoint, params):
            # Your API call logic
            pass
    """
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract API call details from kwargs
            method = kwargs.get('method', 'GET')
            endpoint = kwargs.get('endpoint', '')
            params = kwargs.get('parameters', {})
            headers = kwargs.get('headers', {})
            
            # Validate
            sdk = APISecuritySDK(validator_url)
            result = sdk.validate(
                method=method,
                endpoint=endpoint,
                parameters=params,
                headers=headers
            )
            
            # Check if safe
            if not result.get("safe_to_proceed", False):
                raise SecurityException(
                    f"API call blocked: {result.get('details')}",
                    threats=result.get("threats_detected", []),
                    risk_score=result.get("risk_score", 100)
                )
            
            # Execute original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class SecurityException(Exception):
    """Exception raised when security validation fails"""
    
    def __init__(self, message: str, threats: list = None, risk_score: int = 0):
        super().__init__(message)
        self.threats = threats or []
        self.risk_score = risk_score


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize SDK
    security = APISecuritySDK()
    
    print("\n" + "="*60)
    print("🛡️  API Security SDK - Example Usage")
    print("="*60 + "\n")
    
    # Example 1: Validate a clean request
    print("Example 1: Clean Request")
    result = security.validate(
        method="GET",
        endpoint="/api/users/123",
        parameters={"user_id": "123"}
    )
    print(f"Safe to proceed: {result['safe_to_proceed']}")
    print(f"Risk score: {result['risk_score']}\n")
    
    # Example 2: Validate a malicious request
    print("Example 2: SQL Injection Attack")
    result = security.validate(
        method="GET",
        endpoint="/api/users",
        parameters={"user_id": "123' OR '1'='1"}
    )
    print(f"Safe to proceed: {result['safe_to_proceed']}")
    print(f"Threats: {result['threats_detected']}")
    print(f"Risk score: {result['risk_score']}\n")
    
    # Example 3: Sanitize sensitive data
    print("Example 3: Sanitize Sensitive Data")
    data = {
        "name": "John Doe",
        "card": "4532-1234-5678-9010",
        "ssn": "123-45-6789"
    }
    sanitized = security.sanitize(data)
    print(f"Original: {data}")
    print(f"Sanitized: {sanitized}\n")
    
    # Example 4: Using decorator
    print("Example 4: Using Decorator")
    
    @secure_api_call()
    def make_api_call(method, endpoint, parameters):
        print(f"Executing: {method} {endpoint}")
        return {"success": True}
    
    try:
        # This will pass validation
        result = make_api_call(
            method="GET",
            endpoint="/api/users/123",
            parameters={"user_id": "123"}
        )
        print(f"Result: {result}\n")
    except SecurityException as e:
        print(f"Blocked: {e}\n")
    
    try:
        # This will be blocked
        result = make_api_call(
            method="GET",
            endpoint="/api/users",
            parameters={"user_id": "123' OR '1'='1"}
        )
    except SecurityException as e:
        print(f"Blocked: {e}")
        print(f"Threats: {e.threats}")
        print(f"Risk: {e.risk_score}\n")
    
    print("="*60)
    print("✅ SDK Examples Complete")
    print("="*60 + "\n")
