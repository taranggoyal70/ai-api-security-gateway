"""
Security Event Models

Data models for security events and decisions
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SecurityDecision(str, Enum):
    """Security decision types"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    REQUIRES_APPROVAL = "requires_approval"


class ControlType(str, Enum):
    """Security control types"""
    SCHEMA_VALIDATION = "schema_validation"
    AGENT_IDENTITY = "agent_identity"
    PARAMETER_GUARDS = "parameter_guards"
    TAINT_TRACKING = "taint_tracking"
    RATE_LIMITING = "rate_limiting"


class SecurityEvent(BaseModel):
    """Security event log entry"""
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_id: str
    endpoint: str
    method: str = "GET"
    decision: SecurityDecision
    blocked_by: Optional[ControlType] = None
    reason: str
    request_params: Dict[str, Any] = Field(default_factory=dict)
    tainted_fields: List[str] = Field(default_factory=list)
    security_checks: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class AgentMetrics(BaseModel):
    """Agent activity metrics"""
    agent_id: str
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    blocks_by_control: Dict[str, int] = Field(default_factory=dict)
    last_request_time: Optional[str] = None
    rate_limit_stats: Dict[str, Dict] = Field(default_factory=dict)
