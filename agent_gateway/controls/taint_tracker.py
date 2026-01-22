"""
User-Input Taint Tracking - Control #4 (AI-Specific)

REAL-TIME ENFORCEMENT:
- Marks values from user prompts as TAINTED
- Applies extra checks to tainted data
- Prevents prompt injection attacks

This is AI-SPECIFIC security - not in traditional API gateways.
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel
import re


class TaintResult(BaseModel):
    safe: bool
    message: str
    requires_approval: bool = False


class TaintTracker:
    """
    Taint tracking for user prompt data
    
    Prevents:
    - Prompt injection attacks
    - Unsafe user input reaching sensitive fields
    - Autonomous dangerous actions
    """
    
    def __init__(self):
        # Define sensitive fields that require extra checks if tainted
        self.sensitive_fields = {
            "amount": "financial",
            "refund": "financial",
            "delete": "destructive",
            "admin": "privileged",
            "password": "credential",
            "api_key": "credential",
            "export": "data_exfiltration"
        }
        
        # Taint propagation rules
        self.taint_propagation = {
            "financial": ["amount", "refund", "payment", "invoice"],
            "destructive": ["delete", "remove", "drop", "truncate"],
            "privileged": ["admin", "sudo", "root", "override"],
            "credential": ["password", "api_key", "token", "secret"]
        }
    
    def mark_tainted_fields(
        self,
        params: Dict[str, Any],
        user_prompt: str
    ) -> List[str]:
        """
        Identify which parameter values came from user prompt
        
        Returns:
            List of tainted field names
        """
        tainted = []
        
        # Extract potential values from prompt
        prompt_values = self._extract_values_from_prompt(user_prompt)
        
        # Check which params match prompt values
        for field, value in params.items():
            if self._value_matches_prompt(value, prompt_values):
                tainted.append(field)
        
        return tainted
    
    def check_tainted_sensitive(
        self,
        endpoint: str,
        params: Dict[str, Any],
        tainted_fields: List[str]
    ) -> TaintResult:
        """
        Check if tainted data reaches sensitive fields
        
        Returns:
            TaintResult with safety decision
        """
        
        # No tainted fields = safe
        if not tainted_fields:
            return TaintResult(
                safe=True,
                message="No tainted fields detected",
                requires_approval=False
            )
        
        # Check if any tainted field is sensitive
        sensitive_tainted = []
        for field in tainted_fields:
            if field in self.sensitive_fields:
                sensitive_tainted.append(field)
        
        # No sensitive tainted fields = safe
        if not sensitive_tainted:
            return TaintResult(
                safe=True,
                message=f"Tainted fields {tainted_fields} are not sensitive",
                requires_approval=False
            )
        
        # Sensitive tainted fields detected
        field_types = [self.sensitive_fields[f] for f in sensitive_tainted]
        
        # Financial fields require approval
        if "financial" in field_types:
            return TaintResult(
                safe=False,
                message=f"Tainted financial fields detected: {sensitive_tainted}. Requires human approval.",
                requires_approval=True
            )
        
        # Destructive fields are blocked
        if "destructive" in field_types:
            return TaintResult(
                safe=False,
                message=f"Tainted destructive fields detected: {sensitive_tainted}. Blocked for safety.",
                requires_approval=False
            )
        
        # Privileged fields are blocked
        if "privileged" in field_types:
            return TaintResult(
                safe=False,
                message=f"Tainted privileged fields detected: {sensitive_tainted}. Blocked for security.",
                requires_approval=False
            )
        
        # Credential fields are always blocked
        if "credential" in field_types:
            return TaintResult(
                safe=False,
                message=f"Tainted credential fields detected: {sensitive_tainted}. Blocked.",
                requires_approval=False
            )
        
        # Default: require approval for safety
        return TaintResult(
            safe=False,
            message=f"Tainted sensitive fields: {sensitive_tainted}. Requires approval.",
            requires_approval=True
        )
    
    def _extract_values_from_prompt(self, prompt: str) -> Set[str]:
        """Extract potential parameter values from user prompt"""
        values = set()
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', prompt)
        values.update(numbers)
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]*)"', prompt)
        values.update(quoted)
        quoted = re.findall(r"'([^']*)'", prompt)
        values.update(quoted)
        
        # Extract words (potential IDs, names)
        words = re.findall(r'\b[a-zA-Z0-9_-]+\b', prompt)
        values.update(words)
        
        return values
    
    def _value_matches_prompt(self, value: Any, prompt_values: Set[str]) -> bool:
        """Check if parameter value likely came from prompt"""
        value_str = str(value)
        
        # Direct match
        if value_str in prompt_values:
            return True
        
        # Numeric match
        if isinstance(value, (int, float)):
            if value_str in prompt_values:
                return True
            # Check without decimal
            if str(int(value)) in prompt_values:
                return True
        
        return False
    
    def add_sensitive_field(self, field_name: str, field_type: str):
        """Add a field to sensitive tracking"""
        self.sensitive_fields[field_name] = field_type
