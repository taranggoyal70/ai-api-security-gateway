"""
Parameter Risk Guardrails - Control #3

REAL-TIME ENFORCEMENT:
- Checks dangerous values even if schema valid
- Blocks BFLA-style abuse
- Enforces business logic limits

This is NOT a simulator - actual value checking happens here.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class GuardrailResult(BaseModel):
    passed: bool
    message: str
    violations: List[str] = []


class ParameterGuardrails:
    """
    Parameter value guardrails
    
    Prevents:
    - Excessive values (amount, limit, etc.)
    - Dangerous formats (full_db export)
    - Business logic violations
    """
    
    def __init__(self):
        # Define guardrails for each endpoint
        self.guardrails = {
            "/refunds": {
                "amount": {
                    "max": 500,
                    "min": 0,
                    "type": "currency",
                    "message": "Refund amount must be between $0 and $500"
                }
            },
            "/invoices": {
                "amount": {
                    "max": 10000,
                    "min": 0,
                    "type": "currency",
                    "message": "Invoice amount must be between $0 and $10,000"
                }
            },
            "/export": {
                "format": {
                    "forbidden": ["full_db", "raw_sql", "admin_export"],
                    "allowed": ["csv", "json", "pdf"],
                    "message": "Export format must be csv, json, or pdf"
                },
                "limit": {
                    "max": 1000,
                    "min": 1,
                    "type": "count",
                    "message": "Export limit must be between 1 and 1000 records"
                }
            },
            "/tickets": {
                "priority": {
                    "allowed": ["low", "medium", "high", "urgent"],
                    "message": "Priority must be: low, medium, high, or urgent"
                }
            },
            "/sync/safe": {
                "id": {
                    "max": 999,
                    "min": 1,
                    "type": "id",
                    "message": "Product ID must be between 1 and 999"
                }
            },
            "/sync/unsafe": {
                "id": {
                    "max": 999,
                    "min": 1,
                    "type": "id",
                    "message": "Product ID must be between 1 and 999"
                }
            }
        }
    
    def check_limits(self, endpoint: str, params: Dict[str, Any]) -> GuardrailResult:
        """
        Check parameter values against guardrails
        
        Returns:
            GuardrailResult with pass/fail and violations
        """
        violations = []
        
        # Check if endpoint has guardrails
        if endpoint not in self.guardrails:
            return GuardrailResult(
                passed=True,
                message=f"No guardrails defined for {endpoint}",
                violations=[]
            )
        
        endpoint_guards = self.guardrails[endpoint]
        
        # Check each parameter
        for param_name, param_value in params.items():
            if param_name not in endpoint_guards:
                continue
            
            guard = endpoint_guards[param_name]
            
            # Check max value
            if "max" in guard:
                if isinstance(param_value, (int, float)) and param_value > guard["max"]:
                    violations.append(
                        f"{param_name}={param_value} exceeds maximum of {guard['max']}. {guard.get('message', '')}"
                    )
            
            # Check min value
            if "min" in guard:
                if isinstance(param_value, (int, float)) and param_value < guard["min"]:
                    violations.append(
                        f"{param_name}={param_value} below minimum of {guard['min']}. {guard.get('message', '')}"
                    )
            
            # Check forbidden values
            if "forbidden" in guard:
                if param_value in guard["forbidden"]:
                    violations.append(
                        f"{param_name}={param_value} is forbidden. {guard.get('message', '')}"
                    )
            
            # Check allowed values
            if "allowed" in guard:
                if param_value not in guard["allowed"]:
                    violations.append(
                        f"{param_name}={param_value} not in allowed values {guard['allowed']}. {guard.get('message', '')}"
                    )
        
        # Check for dangerous patterns
        for param_name, param_value in params.items():
            if isinstance(param_value, str):
                # Check for SQL injection patterns
                if any(keyword in param_value.lower() for keyword in ["drop table", "delete from", "truncate"]):
                    violations.append(f"Dangerous SQL pattern detected in {param_name}")
                
                # Check for command injection
                if any(char in param_value for char in [";", "|", "&", "`"]):
                    violations.append(f"Potential command injection in {param_name}")
        
        # Determine if passed
        passed = len(violations) == 0
        
        if passed:
            return GuardrailResult(
                passed=True,
                message=f"All guardrails passed for {endpoint}",
                violations=[]
            )
        else:
            return GuardrailResult(
                passed=False,
                message=f"Guardrail violations: {len(violations)} issue(s)",
                violations=violations
            )
    
    def add_guardrail(
        self,
        endpoint: str,
        param_name: str,
        max_val: Optional[float] = None,
        min_val: Optional[float] = None,
        allowed: Optional[List[str]] = None,
        forbidden: Optional[List[str]] = None,
        message: str = ""
    ):
        """Add or update guardrail for endpoint parameter"""
        if endpoint not in self.guardrails:
            self.guardrails[endpoint] = {}
        
        guard = {}
        if max_val is not None:
            guard["max"] = max_val
        if min_val is not None:
            guard["min"] = min_val
        if allowed is not None:
            guard["allowed"] = allowed
        if forbidden is not None:
            guard["forbidden"] = forbidden
        if message:
            guard["message"] = message
        
        self.guardrails[endpoint][param_name] = guard
