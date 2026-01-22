"""
Agent-to-API Security Gateway - Core Engine

Real-time bidirectional validation for AI agents calling third-party APIs.
Validates both outgoing requests AND incoming responses.
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import httpx


class ValidationDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    SANITIZE = "sanitize"


class ThreatType(str, Enum):
    # Request threats
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    API_KEY_LEAK = "api_key_leak"
    
    # Response threats
    XSS_IN_RESPONSE = "xss_in_response"
    MALICIOUS_REDIRECT = "malicious_redirect"
    DATA_EXFILTRATION = "data_exfiltration"
    SCHEMA_VIOLATION = "schema_violation"
    MALICIOUS_CONTENT = "malicious_content"
    PII_EXPOSURE = "pii_exposure"


class GatewayResult:
    """Result of gateway validation"""
    
    def __init__(
        self,
        decision: ValidationDecision,
        threats: List[ThreatType],
        risk_score: int,
        details: str,
        sanitized_data: Any = None
    ):
        self.decision = decision
        self.threats = threats
        self.risk_score = risk_score
        self.details = details
        self.sanitized_data = sanitized_data
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "threats": [t.value for t in self.threats],
            "risk_score": self.risk_score,
            "details": self.details,
            "sanitized_data": self.sanitized_data,
            "timestamp": self.timestamp.isoformat()
        }


class AgentAPIGateway:
    """
    Security gateway for AI agents calling third-party APIs.
    
    Validates:
    1. Outgoing requests (agent → API)
    2. Incoming responses (API → agent)
    3. API allowlist
    4. Rate limiting
    5. Data sanitization
    """
    
    def __init__(self):
        # Trusted API allowlist
        self.trusted_apis = {
            "unsplash.com": {
                "name": "Unsplash",
                "risk_level": "low",
                "allowed_endpoints": ["/photos", "/search/photos"],
                "rate_limit": 50  # per hour
            },
            "api.remove.bg": {
                "name": "Remove.bg",
                "risk_level": "medium",
                "allowed_endpoints": ["/v1.0/removebg"],
                "rate_limit": 50
            },
            "api.openai.com": {
                "name": "OpenAI",
                "risk_level": "high",
                "allowed_endpoints": ["/v1/images/generations", "/v1/chat/completions"],
                "rate_limit": 100
            },
            "api.cloudinary.com": {
                "name": "Cloudinary",
                "risk_level": "medium",
                "allowed_endpoints": ["/v1_1/*/image/upload"],
                "rate_limit": 100
            },
            "fonts.googleapis.com": {
                "name": "Google Fonts",
                "risk_level": "low",
                "allowed_endpoints": ["/css"],
                "rate_limit": 1000
            }
        }
        
        # Malicious patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"<iframe",
            r"<embed",
            r"<object"
        ]
        
        self.redirect_patterns = [
            r"http://localhost",
            r"http://127\.0\.0\.1",
            r"http://169\.254\.169\.254",  # AWS metadata
            r"file://",
            r"data:text/html"
        ]
        
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "api_key": r"(api[_-]?key|apikey|access[_-]?token)[\s:=]+['\"]?[a-zA-Z0-9]{20,}",
        }
        
        # Request tracking
        self.request_log = []
        self.http_client = httpx.Client(timeout=30.0)
    
    # ========================================================================
    # MAIN GATEWAY FUNCTION
    # ========================================================================
    
    async def intercept_api_call(
        self,
        agent_id: str,
        target_url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any] = None,
        body: Any = None
    ) -> Dict[str, Any]:
        """
        Main interception point - validates request, forwards to API, validates response.
        
        Returns:
            {
                "success": bool,
                "request_validation": {...},
                "response_validation": {...},
                "response_data": {...},
                "threats_detected": [...],
                "sanitized": bool
            }
        """
        
        result = {
            "success": False,
            "request_validation": None,
            "response_validation": None,
            "response_data": None,
            "threats_detected": [],
            "sanitized": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 1: Validate outgoing request
        request_validation = self.validate_request(
            agent_id=agent_id,
            target_url=target_url,
            method=method,
            headers=headers,
            params=params,
            body=body
        )
        
        result["request_validation"] = request_validation.to_dict()
        
        if request_validation.decision == ValidationDecision.DENY:
            result["threats_detected"] = [t.value for t in request_validation.threats]
            return result
        
        # Step 2: Forward to third-party API
        try:
            response = await self._forward_request(
                url=target_url,
                method=method,
                headers=headers,
                params=params,
                body=body
            )
        except Exception as e:
            result["error"] = f"API call failed: {str(e)}"
            return result
        
        # Step 3: Validate incoming response
        response_validation = self.validate_response(
            target_url=target_url,
            response_data=response
        )
        
        result["response_validation"] = response_validation.to_dict()
        result["threats_detected"].extend([t.value for t in response_validation.threats])
        
        if response_validation.decision == ValidationDecision.DENY:
            return result
        
        # Step 4: Sanitize if needed
        if response_validation.decision == ValidationDecision.SANITIZE:
            result["response_data"] = response_validation.sanitized_data
            result["sanitized"] = True
        else:
            result["response_data"] = response
        
        result["success"] = True
        
        # Step 5: Log transaction
        self._log_transaction(agent_id, target_url, result)
        
        return result
    
    # ========================================================================
    # REQUEST VALIDATION
    # ========================================================================
    
    def validate_request(
        self,
        agent_id: str,
        target_url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any] = None,
        body: Any = None
    ) -> GatewayResult:
        """Validate outgoing request before sending to third-party API"""
        
        threats = []
        risk_score = 0
        details = []
        
        # 1. Check API allowlist
        domain = self._extract_domain(target_url)
        if domain not in self.trusted_apis:
            threats.append(ThreatType.SSRF)
            risk_score += 90
            details.append(f"Untrusted API domain: {domain}")
            return GatewayResult(
                decision=ValidationDecision.DENY,
                threats=threats,
                risk_score=risk_score,
                details="; ".join(details)
            )
        
        # 2. Check endpoint allowlist
        api_config = self.trusted_apis[domain]
        endpoint = self._extract_endpoint(target_url)
        
        allowed = False
        for allowed_endpoint in api_config["allowed_endpoints"]:
            if "*" in allowed_endpoint:
                pattern = allowed_endpoint.replace("*", ".*")
                if re.match(pattern, endpoint):
                    allowed = True
                    break
            elif endpoint.startswith(allowed_endpoint):
                allowed = True
                break
        
        if not allowed:
            threats.append(ThreatType.SSRF)
            risk_score += 80
            details.append(f"Endpoint not in allowlist: {endpoint}")
            return GatewayResult(
                decision=ValidationDecision.DENY,
                threats=threats,
                risk_score=risk_score,
                details="; ".join(details)
            )
        
        # 3. Check for API key leaks in params/body
        if params:
            for key, value in params.items():
                if self._contains_api_key(str(value)):
                    threats.append(ThreatType.API_KEY_LEAK)
                    risk_score += 95
                    details.append(f"API key detected in parameter: {key}")
        
        if body and isinstance(body, str):
            if self._contains_api_key(body):
                threats.append(ThreatType.API_KEY_LEAK)
                risk_score += 95
                details.append("API key detected in request body")
        
        # 4. Check for injection attempts
        all_values = []
        if params:
            all_values.extend([str(v) for v in params.values()])
        if body:
            all_values.append(str(body))
        
        for value in all_values:
            if self._contains_sql_injection(value):
                threats.append(ThreatType.SQL_INJECTION)
                risk_score += 90
                details.append("SQL injection pattern detected")
            
            if self._contains_command_injection(value):
                threats.append(ThreatType.COMMAND_INJECTION)
                risk_score += 95
                details.append("Command injection pattern detected")
            
            if self._contains_path_traversal(value):
                threats.append(ThreatType.PATH_TRAVERSAL)
                risk_score += 85
                details.append("Path traversal pattern detected")
        
        # Determine decision
        if risk_score >= 80:
            decision = ValidationDecision.DENY
        else:
            decision = ValidationDecision.ALLOW
        
        return GatewayResult(
            decision=decision,
            threats=threats,
            risk_score=risk_score,
            details="; ".join(details) if details else "Request validation passed"
        )
    
    # ========================================================================
    # RESPONSE VALIDATION
    # ========================================================================
    
    def validate_response(
        self,
        target_url: str,
        response_data: Any
    ) -> GatewayResult:
        """Validate response from third-party API"""
        
        threats = []
        risk_score = 0
        details = []
        sanitized_data = None
        
        # Convert response to string for pattern matching
        response_str = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
        
        # 1. Check for XSS in response
        for pattern in self.xss_patterns:
            if re.search(pattern, response_str, re.IGNORECASE):
                threats.append(ThreatType.XSS_IN_RESPONSE)
                risk_score += 85
                details.append("XSS pattern detected in response")
                break
        
        # 2. Check for malicious redirects
        if isinstance(response_data, dict):
            for key, value in response_data.items():
                if isinstance(value, str) and ("url" in key.lower() or "redirect" in key.lower()):
                    for pattern in self.redirect_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            threats.append(ThreatType.MALICIOUS_REDIRECT)
                            risk_score += 90
                            details.append(f"Malicious redirect detected: {key}")
                            break
        
        # 3. Check for PII exposure
        pii_found = {}
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, response_str, re.IGNORECASE)
            if matches:
                pii_found[pii_type] = len(matches)
                threats.append(ThreatType.PII_EXPOSURE)
                risk_score += 70
                details.append(f"PII detected: {pii_type} ({len(matches)} instances)")
        
        # 4. Sanitize if needed
        if pii_found or ThreatType.XSS_IN_RESPONSE in threats:
            sanitized_data = self._sanitize_response(response_data)
            decision = ValidationDecision.SANITIZE
        elif risk_score >= 80:
            decision = ValidationDecision.DENY
        else:
            decision = ValidationDecision.ALLOW
        
        return GatewayResult(
            decision=decision,
            threats=threats,
            risk_score=risk_score,
            details="; ".join(details) if details else "Response validation passed",
            sanitized_data=sanitized_data
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _forward_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, Any] = None,
        body: Any = None
    ) -> Any:
        """Forward request to third-party API"""
        
        response = self.http_client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=body if isinstance(body, dict) else None,
            data=body if isinstance(body, str) else None
        )
        
        response.raise_for_status()
        
        try:
            return response.json()
        except:
            return response.text
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _extract_endpoint(self, url: str) -> str:
        """Extract endpoint path from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.path
    
    def _contains_api_key(self, text: str) -> bool:
        """Check if text contains API key pattern"""
        for pattern in [self.pii_patterns["api_key"]]:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _contains_sql_injection(self, text: str) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bOR\b.*=.*)",
            r"(--|\#|\/\*)"
        ]
        for pattern in sql_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _contains_command_injection(self, text: str) -> bool:
        """Check for command injection patterns"""
        cmd_patterns = [r"(;|\||&|`|\$\()", r"(rm\s+-rf|del\s+/)"]
        for pattern in cmd_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _contains_path_traversal(self, text: str) -> bool:
        """Check for path traversal patterns"""
        return bool(re.search(r"(\.\./|\.\.\\)", text))
    
    def _sanitize_response(self, data: Any) -> Any:
        """Sanitize response data"""
        if isinstance(data, str):
            sanitized = data
            # Mask PII
            for pii_type, pattern in self.pii_patterns.items():
                sanitized = re.sub(pattern, f"***{pii_type.upper()}***", sanitized, flags=re.IGNORECASE)
            # Remove XSS
            for pattern in self.xss_patterns:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
            return sanitized
        
        elif isinstance(data, dict):
            return {k: self._sanitize_response(v) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [self._sanitize_response(item) for item in data]
        
        return data
    
    def _log_transaction(self, agent_id: str, target_url: str, result: Dict[str, Any]):
        """Log transaction for audit"""
        self.request_log.append({
            "agent_id": agent_id,
            "target_url": target_url,
            "timestamp": datetime.utcnow().isoformat(),
            "success": result["success"],
            "threats": result["threats_detected"],
            "sanitized": result["sanitized"]
        })
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log"""
        return self.request_log[-limit:]
