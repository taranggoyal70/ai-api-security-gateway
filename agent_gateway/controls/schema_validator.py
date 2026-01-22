"""
Schema & Command Validation - Control #1

REAL-TIME ENFORCEMENT:
- Blocks requests with unexpected fields
- Prevents agent hallucinated parameters
- Enforces strict API contracts

This is NOT a simulator - actual request blocking happens here.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ValidationResult(BaseModel):
    valid: bool
    message: str
    violations: List[str] = []


class SchemaValidator:
    """
    Schema validation for agent requests
    
    Prevents:
    - Agent hallucinated fields
    - Unexpected parameters
    - Schema violations
    """
    
    def __init__(self):
        # Define allowed schemas for each endpoint
        self.endpoint_schemas = {
            "/sync/safe": {
                "allowed_fields": ["id", "variant", "mode"],
                "required_fields": ["id"],
                "field_types": {
                    "id": (int, str),
                    "variant": str,
                    "mode": str
                }
            },
            "/sync/unsafe": {
                "allowed_fields": ["id", "variant", "mode"],
                "required_fields": ["id"],
                "field_types": {
                    "id": (int, str),
                    "variant": str,
                    "mode": str
                }
            },
            "/refunds": {
                "allowed_fields": ["customer_id", "amount", "reason"],
                "required_fields": ["customer_id", "amount"],
                "field_types": {
                    "customer_id": (int, str),
                    "amount": (int, float),
                    "reason": str
                }
            },
            "/tickets": {
                "allowed_fields": ["customer_id", "subject", "priority", "description"],
                "required_fields": ["customer_id", "subject"],
                "field_types": {
                    "customer_id": (int, str),
                    "subject": str,
                    "priority": str,
                    "description": str
                }
            },
            "/invoices": {
                "allowed_fields": ["customer_id", "amount", "date", "items"],
                "required_fields": ["customer_id", "amount"],
                "field_types": {
                    "customer_id": (int, str),
                    "amount": (int, float),
                    "date": str,
                    "items": list
                }
            },
            "/export": {
                "allowed_fields": ["format", "filters", "limit"],
                "required_fields": ["format"],
                "field_types": {
                    "format": str,
                    "filters": dict,
                    "limit": int
                }
            }
        }
    
    def validate(self, endpoint: str, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate request against endpoint schema
        
        Returns:
            ValidationResult with pass/fail and violations
        """
        violations = []
        
        # Check if endpoint has defined schema
        if endpoint not in self.endpoint_schemas:
            return ValidationResult(
                valid=True,
                message=f"No schema defined for {endpoint} - allowing",
                violations=[]
            )
        
        schema = self.endpoint_schemas[endpoint]
        allowed_fields = schema["allowed_fields"]
        required_fields = schema["required_fields"]
        field_types = schema["field_types"]
        
        # 1. Check for unexpected fields (agent hallucination)
        for field in params.keys():
            if field not in allowed_fields:
                violations.append(f"Unexpected field: '{field}' not in allowed fields {allowed_fields}")
        
        # 2. Check for missing required fields
        for field in required_fields:
            if field not in params:
                violations.append(f"Missing required field: '{field}'")
        
        # 3. Check field types
        for field, value in params.items():
            if field in field_types:
                expected_type = field_types[field]
                if not isinstance(value, expected_type):
                    violations.append(
                        f"Invalid type for '{field}': expected {expected_type}, got {type(value).__name__}"
                    )
        
        # 4. Check for dangerous field combinations
        if "override_checks" in params:
            violations.append("Dangerous field 'override_checks' detected - agent attempting privilege escalation")
        
        if "admin" in params or "sudo" in params:
            violations.append("Privilege escalation attempt detected")
        
        # Determine if valid
        valid = len(violations) == 0
        
        if valid:
            return ValidationResult(
                valid=True,
                message=f"Schema validation passed for {endpoint}",
                violations=[]
            )
        else:
            return ValidationResult(
                valid=False,
                message=f"Schema validation failed: {len(violations)} violation(s)",
                violations=violations
            )
    
    def add_endpoint_schema(
        self,
        endpoint: str,
        allowed_fields: List[str],
        required_fields: List[str],
        field_types: Dict[str, type]
    ):
        """Add or update schema for an endpoint"""
        self.endpoint_schemas[endpoint] = {
            "allowed_fields": allowed_fields,
            "required_fields": required_fields,
            "field_types": field_types
        }
