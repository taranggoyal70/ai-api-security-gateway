"""
Phase 2: Core Governance Policies

Defines the governance model for agent actions:
- Tool allowlists and permissions
- Scoped permissions with least privilege
- Execution guards and autonomy levels
- Data classification and handling rules
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime, timedelta


class DataClassification(str, Enum):
    """Data sensitivity levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"  # PII, PHI, financial data


class ApprovalRequirement(str, Enum):
    """When approval is needed"""
    NEVER = "never"  # Fully autonomous
    CONDITIONAL = "conditional"  # Based on parameters
    ALWAYS = "always"  # Every time


class PolicyDecision(str, Enum):
    """Policy enforcement decisions"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    SANITIZE = "sanitize"  # Allow but sanitize output


class ToolPolicy(BaseModel):
    """Policy for a specific tool"""
    tool_name: str
    allowed_agents: List[str]
    approval_requirement: ApprovalRequirement
    max_calls_per_minute: int
    max_calls_per_hour: int
    parameter_constraints: Dict[str, Any] = {}
    output_sanitization: bool = False
    requires_audit: bool = True


class ParameterConstraint(BaseModel):
    """Constraint on a tool parameter"""
    parameter_name: str
    data_type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None  # Regex pattern
    required: bool = False


class ExecutionGuard(BaseModel):
    """Guard conditions for execution"""
    guard_name: str
    description: str
    check_function: str  # Name of function to call
    failure_action: PolicyDecision
    applies_to_tools: List[str] = []  # Empty = all tools
    applies_to_agents: List[str] = []  # Empty = all agents


# ============================================================================
# TOOL POLICIES
# ============================================================================

TOOL_POLICIES = {
    "search_knowledge_base": ToolPolicy(
        tool_name="search_knowledge_base",
        allowed_agents=["support-agent", "admin-agent"],
        approval_requirement=ApprovalRequirement.NEVER,
        max_calls_per_minute=20,
        max_calls_per_hour=500,
        parameter_constraints={
            "query": {
                "max_length": 500,
                "no_sql_injection": True
            }
        },
        output_sanitization=False,
        requires_audit=True
    ),
    
    "create_support_ticket": ToolPolicy(
        tool_name="create_support_ticket",
        allowed_agents=["support-agent"],
        approval_requirement=ApprovalRequirement.NEVER,
        max_calls_per_minute=10,
        max_calls_per_hour=100,
        parameter_constraints={
            "priority": {
                "allowed_values": ["low", "medium", "high"]
            },
            "subject": {
                "max_length": 200
            },
            "description": {
                "max_length": 2000
            }
        },
        requires_audit=True
    ),
    
    "lookup_order": ToolPolicy(
        tool_name="lookup_order",
        allowed_agents=["support-agent", "refund-agent"],
        approval_requirement=ApprovalRequirement.NEVER,
        max_calls_per_minute=20,
        max_calls_per_hour=500,
        parameter_constraints={},
        requires_audit=True
    ),
    
    "issue_refund": ToolPolicy(
        tool_name="issue_refund",
        allowed_agents=["refund-agent"],
        approval_requirement=ApprovalRequirement.CONDITIONAL,  # Based on amount
        max_calls_per_minute=3,
        max_calls_per_hour=20,
        parameter_constraints={
            "amount": {
                "min_value": 0.01,
                "max_value": 10000.0,  # Hard limit
                "approval_threshold": 500.0  # Requires approval above this
            },
            "reason": {
                "required": True,
                "min_length": 10
            }
        },
        requires_audit=True
    ),
    
    "restart_service": ToolPolicy(
        tool_name="restart_service",
        allowed_agents=["admin-agent"],
        approval_requirement=ApprovalRequirement.ALWAYS,  # Always needs approval
        max_calls_per_minute=2,
        max_calls_per_hour=10,
        parameter_constraints={
            "environment": {
                "allowed_values": ["dev", "staging"],  # Never prod
                "forbidden_values": ["prod", "production"]
            }
        },
        requires_audit=True
    ),
    
    "execute_database_query": ToolPolicy(
        tool_name="execute_database_query",
        allowed_agents=[],  # No agent allowed
        approval_requirement=ApprovalRequirement.ALWAYS,
        max_calls_per_minute=1,
        max_calls_per_hour=5,
        parameter_constraints={
            "query": {
                "forbidden_patterns": [
                    r"DROP\s+TABLE",
                    r"DELETE\s+FROM",
                    r"TRUNCATE",
                    r"ALTER\s+TABLE",
                    r"--",  # SQL comments
                    r"/\*.*\*/"  # Block comments
                ]
            }
        },
        requires_audit=True
    ),
    
    "export_customer_data": ToolPolicy(
        tool_name="export_customer_data",
        allowed_agents=[],  # Highly restricted
        approval_requirement=ApprovalRequirement.ALWAYS,
        max_calls_per_minute=1,
        max_calls_per_hour=3,
        parameter_constraints={
            "customer_ids": {
                "max_count": 100  # Max 100 customers per export
            },
            "include_pii": {
                "requires_special_approval": True
            }
        },
        output_sanitization=True,  # Sanitize PII in output
        requires_audit=True
    )
}


# ============================================================================
# EXECUTION GUARDS
# ============================================================================

EXECUTION_GUARDS = [
    ExecutionGuard(
        guard_name="rate_limit_guard",
        description="Prevent rapid-fire requests that could indicate attack or runaway loop",
        check_function="check_rate_limit",
        failure_action=PolicyDecision.DENY,
        applies_to_tools=[],  # All tools
        applies_to_agents=[]  # All agents
    ),
    
    ExecutionGuard(
        guard_name="taint_tracking_guard",
        description="Detect user-originated data in sensitive parameters",
        check_function="check_taint_tracking",
        failure_action=PolicyDecision.REQUIRE_APPROVAL,
        applies_to_tools=["issue_refund", "execute_database_query", "export_customer_data"],
        applies_to_agents=[]
    ),
    
    ExecutionGuard(
        guard_name="pii_protection_guard",
        description="Prevent PII leakage in outputs",
        check_function="check_pii_protection",
        failure_action=PolicyDecision.SANITIZE,
        applies_to_tools=[],  # All tools
        applies_to_agents=[]
    ),
    
    ExecutionGuard(
        guard_name="cross_environment_guard",
        description="Block dev agents from accessing prod resources",
        check_function="check_environment_isolation",
        failure_action=PolicyDecision.DENY,
        applies_to_tools=["restart_service", "execute_database_query"],
        applies_to_agents=[]
    ),
    
    ExecutionGuard(
        guard_name="amount_threshold_guard",
        description="Require approval for high-value transactions",
        check_function="check_amount_threshold",
        failure_action=PolicyDecision.REQUIRE_APPROVAL,
        applies_to_tools=["issue_refund"],
        applies_to_agents=["refund-agent"]
    ),
    
    ExecutionGuard(
        guard_name="prompt_injection_guard",
        description="Detect and block prompt injection attempts",
        check_function="check_prompt_injection",
        failure_action=PolicyDecision.DENY,
        applies_to_tools=[],  # All tools
        applies_to_agents=[]
    ),
    
    ExecutionGuard(
        guard_name="sequential_action_guard",
        description="Detect suspicious sequences of actions",
        check_function="check_action_sequence",
        failure_action=PolicyDecision.REQUIRE_APPROVAL,
        applies_to_tools=[],
        applies_to_agents=[]
    )
]


# ============================================================================
# DATA CLASSIFICATION RULES
# ============================================================================

DATA_CLASSIFICATION_RULES = {
    "customer_email": DataClassification.CONFIDENTIAL,
    "customer_phone": DataClassification.CONFIDENTIAL,
    "customer_name": DataClassification.CONFIDENTIAL,
    "customer_address": DataClassification.CONFIDENTIAL,
    "credit_card": DataClassification.RESTRICTED,
    "ssn": DataClassification.RESTRICTED,
    "bank_account": DataClassification.RESTRICTED,
    "order_id": DataClassification.INTERNAL,
    "order_amount": DataClassification.INTERNAL,
    "ticket_id": DataClassification.INTERNAL,
    "system_metrics": DataClassification.INTERNAL,
    "logs": DataClassification.INTERNAL,
    "api_keys": DataClassification.RESTRICTED,
    "passwords": DataClassification.RESTRICTED
}


# ============================================================================
# SENSITIVE PATTERNS (for PII detection)
# ============================================================================

SENSITIVE_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    "api_key": r'\b[A-Za-z0-9]{32,}\b',
    "jwt": r'\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b'
}


# ============================================================================
# PROMPT INJECTION PATTERNS
# ============================================================================

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now",
    r"new\s+instructions",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"<\s*script\s*>",
    r"javascript\s*:",
    r"eval\s*\(",
    r"exec\s*\(",
    r"\$\{.*\}",  # Template injection
    r"<!--.*-->",  # HTML comments
]


# ============================================================================
# APPROVAL THRESHOLDS
# ============================================================================

APPROVAL_THRESHOLDS = {
    "refund_amount": {
        "auto_approve_below": 50.0,
        "require_approval_above": 50.0,
        "require_manager_approval_above": 500.0
    },
    "data_export": {
        "auto_approve_records_below": 10,
        "require_approval_above": 10,
        "require_manager_approval_above": 100
    },
    "service_restart": {
        "auto_approve_environments": [],  # Never auto-approve
        "require_approval_environments": ["dev", "staging"],
        "forbidden_environments": ["prod", "production"]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tool_policy(tool_name: str) -> Optional[ToolPolicy]:
    """Get policy for a specific tool"""
    return TOOL_POLICIES.get(tool_name)


def requires_approval(tool_name: str, parameters: Dict[str, Any], agent_id: str) -> bool:
    """Determine if a tool call requires approval"""
    policy = get_tool_policy(tool_name)
    if not policy:
        return True  # Unknown tools require approval
    
    # Always require approval
    if policy.approval_requirement == ApprovalRequirement.ALWAYS:
        return True
    
    # Never require approval
    if policy.approval_requirement == ApprovalRequirement.NEVER:
        return False
    
    # Conditional - check specific conditions
    if tool_name == "issue_refund":
        amount = parameters.get("amount", 0)
        threshold = APPROVAL_THRESHOLDS["refund_amount"]["require_approval_above"]
        return amount > threshold
    
    if tool_name == "export_customer_data":
        customer_count = len(parameters.get("customer_ids", []))
        threshold = APPROVAL_THRESHOLDS["data_export"]["require_approval_above"]
        return customer_count > threshold
    
    return False


def get_applicable_guards(tool_name: str, agent_id: str) -> List[ExecutionGuard]:
    """Get all guards that apply to a tool/agent combination"""
    applicable = []
    for guard in EXECUTION_GUARDS:
        # Check if guard applies to this tool
        if guard.applies_to_tools and tool_name not in guard.applies_to_tools:
            continue
        
        # Check if guard applies to this agent
        if guard.applies_to_agents and agent_id not in guard.applies_to_agents:
            continue
        
        applicable.append(guard)
    
    return applicable


def get_data_classification(field_name: str) -> DataClassification:
    """Get classification level for a data field"""
    return DATA_CLASSIFICATION_RULES.get(field_name, DataClassification.INTERNAL)
