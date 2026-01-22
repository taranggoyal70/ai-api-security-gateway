"""
API Security Validation Service

Standalone microservice dedicated ONLY to API security validation.
Can be used by any service to validate API calls before execution.

This is NOT an AI agent - it's a pure security validation service.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum


class SecurityDecision(str, Enum):
    """Security validation decision"""
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


class ThreatType(str, Enum):
    """Types of API security threats"""
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    XSS = "xss"
    XXE = "xxe"
    BROKEN_AUTH = "broken_authentication"
    BROKEN_ACCESS = "broken_access_control"
    RATE_LIMIT = "rate_limit_exceeded"
    INVALID_SCHEMA = "invalid_schema"
    SENSITIVE_DATA = "sensitive_data_exposure"


class SecurityValidationResult:
    """Result of security validation"""
    
    def __init__(
        self,
        decision: SecurityDecision,
        threats_detected: List[ThreatType],
        risk_score: int,
        details: str,
        recommendations: List[str] = None
    ):
        self.decision = decision
        self.threats_detected = threats_detected
        self.risk_score = risk_score
        self.details = details
        self.recommendations = recommendations or []
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "threats_detected": self.threats_detected,
            "risk_score": self.risk_score,
            "details": self.details,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


class APISecurityValidator:
    """
    Dedicated API Security Validation Service
    
    ONLY validates API security - no business logic, no AI, no execution.
    Pure security validation that any service can use.
    """
    
    def __init__(self):
        # SQL Injection patterns
        self.sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bSELECT\b.*\bFROM\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(--|\#|\/\*|\*\/)",  # SQL comments
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)",
            r"('.*OR.*'.*=.*')",
            r"(\d+\s*=\s*\d+)",  # 1=1
        ]
        
        # Command Injection patterns
        self.command_patterns = [
            r"(;|\||&|`|\$\(|\$\{)",  # Command separators
            r"(\.\./|\.\.\\)",  # Path traversal
            r"(/bin/|/usr/bin/|cmd\.exe|powershell)",
            r"(wget|curl|nc|netcat)",
            r"(rm\s+-rf|del\s+/|format)",
        ]
        
        # Path Traversal patterns
        self.path_traversal_patterns = [
            r"(\.\./|\.\./\.\./)",
            r"(\.\.\\|\.\.\\\.\.\\)",
            r"(%2e%2e%2f|%2e%2e/|..%2f|%2e%2e%5c)",
            r"(/etc/passwd|/etc/shadow|C:\\Windows)",
        ]
        
        # SSRF patterns
        self.ssrf_patterns = [
            r"(localhost|127\.0\.0\.1|0\.0\.0\.0)",
            r"(169\.254\.169\.254)",  # AWS metadata
            r"(::1|0000:0000:0000:0000:0000:0000:0000:0001)",  # IPv6 localhost
            r"(file://|gopher://|dict://|ftp://)",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"(<script[^>]*>.*</script>)",
            r"(javascript:)",
            r"(onerror\s*=|onload\s*=|onclick\s*=)",
            r"(<iframe|<embed|<object)",
        ]
        
        # Sensitive data patterns
        self.sensitive_patterns = {
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "api_key": r"(api[_-]?key|apikey|access[_-]?token)[\s:=]+['\"]?[a-zA-Z0-9]{20,}",
            "password": r"(password|passwd|pwd)[\s:=]+['\"]?[^\s'\"]+",
            "jwt": r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
            "aws_key": r"AKIA[0-9A-Z]{16}",
        }
        
        # Rate limiting
        self.rate_limits = defaultdict(lambda: deque())
    
    # ========================================================================
    # MAIN VALIDATION ENTRY POINT
    # ========================================================================
    
    def validate_api_request(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str],
        parameters: Dict[str, Any],
        body: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> SecurityValidationResult:
        """
        Main validation function - checks ALL API security threats.
        
        This is the single entry point for API security validation.
        """
        
        threats = []
        risk_score = 0
        details = []
        recommendations = []
        
        # 1. SQL Injection Check
        sql_result = self.check_sql_injection(parameters, body)
        if sql_result["detected"]:
            threats.append(ThreatType.SQL_INJECTION)
            risk_score += 90
            details.append(f"SQL Injection: {sql_result['details']}")
            recommendations.append("Use parameterized queries")
        
        # 2. Command Injection Check
        cmd_result = self.check_command_injection(parameters, body)
        if cmd_result["detected"]:
            threats.append(ThreatType.COMMAND_INJECTION)
            risk_score += 95
            details.append(f"Command Injection: {cmd_result['details']}")
            recommendations.append("Sanitize all user inputs")
        
        # 3. Path Traversal Check
        path_result = self.check_path_traversal(parameters, endpoint)
        if path_result["detected"]:
            threats.append(ThreatType.PATH_TRAVERSAL)
            risk_score += 85
            details.append(f"Path Traversal: {path_result['details']}")
            recommendations.append("Validate file paths")
        
        # 4. SSRF Check
        ssrf_result = self.check_ssrf(parameters, body)
        if ssrf_result["detected"]:
            threats.append(ThreatType.SSRF)
            risk_score += 90
            details.append(f"SSRF: {ssrf_result['details']}")
            recommendations.append("Validate URLs against allowlist")
        
        # 5. XSS Check
        xss_result = self.check_xss(parameters, body)
        if xss_result["detected"]:
            threats.append(ThreatType.XSS)
            risk_score += 70
            details.append(f"XSS: {xss_result['details']}")
            recommendations.append("Encode output, use Content-Security-Policy")
        
        # 6. Sensitive Data Exposure Check
        sensitive_result = self.check_sensitive_data(parameters, body, headers)
        if sensitive_result["detected"]:
            threats.append(ThreatType.SENSITIVE_DATA)
            risk_score += 80
            details.append(f"Sensitive Data: {sensitive_result['details']}")
            recommendations.append("Mask sensitive data in logs/responses")
        
        # 7. Authentication Check
        auth_result = self.check_authentication(headers, endpoint)
        if not auth_result["valid"]:
            threats.append(ThreatType.BROKEN_AUTH)
            risk_score += 85
            details.append(f"Auth Issue: {auth_result['details']}")
            recommendations.append("Implement proper authentication")
        
        # 8. Rate Limiting Check
        if client_id:
            rate_result = self.check_rate_limit(client_id, endpoint)
            if not rate_result["allowed"]:
                threats.append(ThreatType.RATE_LIMIT)
                risk_score += 60
                details.append(f"Rate Limit: {rate_result['details']}")
                recommendations.append("Implement exponential backoff")
        
        # 9. Schema Validation
        schema_result = self.validate_schema(method, endpoint, parameters)
        if not schema_result["valid"]:
            threats.append(ThreatType.INVALID_SCHEMA)
            risk_score += 50
            details.append(f"Schema: {schema_result['details']}")
            recommendations.append("Follow API schema strictly")
        
        # Determine decision
        if risk_score >= 80:
            decision = SecurityDecision.DENY
        elif risk_score >= 50:
            decision = SecurityDecision.WARN
        else:
            decision = SecurityDecision.ALLOW
        
        return SecurityValidationResult(
            decision=decision,
            threats_detected=threats,
            risk_score=min(risk_score, 100),
            details="; ".join(details) if details else "No threats detected",
            recommendations=recommendations
        )
    
    # ========================================================================
    # INDIVIDUAL SECURITY CHECKS
    # ========================================================================
    
    def check_sql_injection(
        self,
        parameters: Dict[str, Any],
        body: Optional[str]
    ) -> Dict[str, Any]:
        """Detect SQL injection attempts"""
        
        # Check all string parameters
        for key, value in parameters.items():
            if isinstance(value, str):
                for pattern in self.sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return {
                            "detected": True,
                            "details": f"SQL pattern in parameter '{key}': {pattern}"
                        }
        
        # Check body
        if body:
            for pattern in self.sql_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    return {
                        "detected": True,
                        "details": f"SQL pattern in request body"
                    }
        
        return {"detected": False}
    
    def check_command_injection(
        self,
        parameters: Dict[str, Any],
        body: Optional[str]
    ) -> Dict[str, Any]:
        """Detect command injection attempts"""
        
        for key, value in parameters.items():
            if isinstance(value, str):
                for pattern in self.command_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return {
                            "detected": True,
                            "details": f"Command injection in parameter '{key}'"
                        }
        
        if body:
            for pattern in self.command_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    return {
                        "detected": True,
                        "details": "Command injection in request body"
                    }
        
        return {"detected": False}
    
    def check_path_traversal(
        self,
        parameters: Dict[str, Any],
        endpoint: str
    ) -> Dict[str, Any]:
        """Detect path traversal attempts"""
        
        # Check endpoint
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, endpoint, re.IGNORECASE):
                return {
                    "detected": True,
                    "details": "Path traversal in endpoint"
                }
        
        # Check parameters
        for key, value in parameters.items():
            if isinstance(value, str):
                for pattern in self.path_traversal_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return {
                            "detected": True,
                            "details": f"Path traversal in parameter '{key}'"
                        }
        
        return {"detected": False}
    
    def check_ssrf(
        self,
        parameters: Dict[str, Any],
        body: Optional[str]
    ) -> Dict[str, Any]:
        """Detect SSRF attempts"""
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Check if it looks like a URL
                if "://" in value or value.startswith("//"):
                    for pattern in self.ssrf_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            return {
                                "detected": True,
                                "details": f"SSRF attempt in parameter '{key}'"
                            }
        
        if body:
            for pattern in self.ssrf_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    return {
                        "detected": True,
                        "details": "SSRF attempt in request body"
                    }
        
        return {"detected": False}
    
    def check_xss(
        self,
        parameters: Dict[str, Any],
        body: Optional[str]
    ) -> Dict[str, Any]:
        """Detect XSS attempts"""
        
        for key, value in parameters.items():
            if isinstance(value, str):
                for pattern in self.xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return {
                            "detected": True,
                            "details": f"XSS in parameter '{key}'"
                        }
        
        if body:
            for pattern in self.xss_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    return {
                        "detected": True,
                        "details": "XSS in request body"
                    }
        
        return {"detected": False}
    
    def check_sensitive_data(
        self,
        parameters: Dict[str, Any],
        body: Optional[str],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Detect sensitive data exposure"""
        
        # Check parameters
        for key, value in parameters.items():
            if isinstance(value, str):
                for data_type, pattern in self.sensitive_patterns.items():
                    if re.search(pattern, value, re.IGNORECASE):
                        return {
                            "detected": True,
                            "details": f"Sensitive data ({data_type}) in parameter '{key}'"
                        }
        
        # Check headers (API keys, tokens)
        for header, value in headers.items():
            if isinstance(value, str):
                for data_type, pattern in self.sensitive_patterns.items():
                    if re.search(pattern, f"{header}:{value}", re.IGNORECASE):
                        return {
                            "detected": True,
                            "details": f"Sensitive data ({data_type}) in header"
                        }
        
        return {"detected": False}
    
    def check_authentication(
        self,
        headers: Dict[str, str],
        endpoint: str
    ) -> Dict[str, Any]:
        """Validate authentication"""
        
        # Check for authentication header
        auth_header = headers.get("Authorization") or headers.get("authorization")
        
        # Public endpoints don't need auth
        public_endpoints = ["/health", "/status", "/docs"]
        if any(endpoint.startswith(ep) for ep in public_endpoints):
            return {"valid": True}
        
        if not auth_header:
            return {
                "valid": False,
                "details": "Missing authentication header"
            }
        
        # Basic validation (in production, verify token/signature)
        if not (auth_header.startswith("Bearer ") or auth_header.startswith("Basic ")):
            return {
                "valid": False,
                "details": "Invalid authentication format"
            }
        
        return {"valid": True}
    
    def check_rate_limit(
        self,
        client_id: str,
        endpoint: str
    ) -> Dict[str, Any]:
        """Check rate limiting"""
        
        key = f"{client_id}:{endpoint}"
        now = datetime.utcnow()
        
        # Clean old requests (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        history = self.rate_limits[key]
        while history and history[0] < cutoff:
            history.popleft()
        
        # Check limit (100 requests per minute per endpoint)
        if len(history) >= 100:
            return {
                "allowed": False,
                "details": f"Rate limit exceeded: {len(history)}/100 per minute"
            }
        
        # Record this request
        history.append(now)
        
        return {"allowed": True}
    
    def validate_schema(
        self,
        method: str,
        endpoint: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate request against API schema"""
        
        # In production, load actual API schema
        # For now, basic validation
        
        # Check for common issues
        if not method:
            return {"valid": False, "details": "Missing HTTP method"}
        
        if not endpoint:
            return {"valid": False, "details": "Missing endpoint"}
        
        # Check parameter types
        for key, value in parameters.items():
            if value is None:
                continue
            
            # Check for extremely long values (potential DoS)
            if isinstance(value, str) and len(value) > 10000:
                return {
                    "valid": False,
                    "details": f"Parameter '{key}' exceeds maximum length"
                }
        
        return {"valid": True}
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def sanitize_output(self, data: Any) -> Any:
        """Sanitize output to remove sensitive data"""
        
        if isinstance(data, str):
            sanitized = data
            
            # Mask sensitive patterns
            for data_type, pattern in self.sensitive_patterns.items():
                sanitized = re.sub(pattern, f"***{data_type.upper()}***", sanitized, flags=re.IGNORECASE)
            
            return sanitized
        
        elif isinstance(data, dict):
            return {k: self.sanitize_output(v) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [self.sanitize_output(item) for item in data]
        
        return data
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers"""
        
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    validator = APISecurityValidator()
    
    print("\n" + "="*60)
    print("🛡️  API SECURITY VALIDATION SERVICE")
    print("="*60 + "\n")
    
    # Test 1: Clean request
    print("Test 1: Clean Request")
    result = validator.validate_api_request(
        method="GET",
        endpoint="/api/users/123",
        headers={"Authorization": "Bearer token123"},
        parameters={"user_id": "123"}
    )
    print(f"Decision: {result.decision}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Details: {result.details}\n")
    
    # Test 2: SQL Injection
    print("Test 2: SQL Injection Attack")
    result = validator.validate_api_request(
        method="GET",
        endpoint="/api/users",
        headers={"Authorization": "Bearer token123"},
        parameters={"user_id": "123' OR '1'='1"}
    )
    print(f"Decision: {result.decision}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Threats: {result.threats_detected}")
    print(f"Details: {result.details}")
    print(f"Recommendations: {result.recommendations}\n")
    
    # Test 3: Command Injection
    print("Test 3: Command Injection Attack")
    result = validator.validate_api_request(
        method="POST",
        endpoint="/api/execute",
        headers={"Authorization": "Bearer token123"},
        parameters={"command": "ls; rm -rf /"}
    )
    print(f"Decision: {result.decision}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Threats: {result.threats_detected}")
    print(f"Details: {result.details}\n")
    
    # Test 4: Sensitive Data
    print("Test 4: Sensitive Data Exposure")
    result = validator.validate_api_request(
        method="POST",
        endpoint="/api/payment",
        headers={"Authorization": "Bearer token123"},
        parameters={"card_number": "4532-1234-5678-9010"}
    )
    print(f"Decision: {result.decision}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Threats: {result.threats_detected}")
    print(f"Details: {result.details}\n")
    
    print("="*60)
    print("✅ API Security Validation Complete")
    print("="*60 + "\n")
