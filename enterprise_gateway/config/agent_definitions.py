"""
Phase 1: Agent Use Case Definitions

Defines three enterprise-credible agent roles with bounded tool interactions:
1. Customer Support Agent - Knowledge base and ticketing
2. Refund/Billing Agent - Order lookup and refund processing
3. Admin/DevOps Assistant - Read-only diagnostics and controlled operations
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AutonomyLevel(str, Enum):
    """Agent autonomy levels per enterprise governance"""
    ASSISTIVE = "assistive"  # Suggests actions for human confirmation
    CONDITIONAL = "conditional"  # Autonomous with selective approvals
    BOUNDED = "bounded"  # Predefined tasks only, no escalation
    SUPERVISED = "supervised"  # All actions require approval


class ToolDefinition(BaseModel):
    """Definition of a tool/API that an agent can use"""
    name: str
    description: str
    parameters: Dict[str, Any]
    risk_level: str = Field(default="low", description="low, medium, high")
    requires_approval: bool = False
    max_calls_per_minute: int = 10


class AgentRole(BaseModel):
    """Complete definition of an agent role"""
    agent_id: str
    display_name: str
    description: str
    autonomy_level: AutonomyLevel
    allowed_tools: List[str]
    forbidden_tools: List[str] = []
    data_access_scope: List[str]
    max_refund_amount: Optional[float] = None
    can_access_pii: bool = False
    can_modify_data: bool = False
    requires_mfa: bool = False


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

AVAILABLE_TOOLS = {
    # Customer Support Tools
    "search_knowledge_base": ToolDefinition(
        name="search_knowledge_base",
        description="Search internal knowledge base for support articles",
        parameters={
            "query": "string - Search query",
            "category": "string - Optional category filter"
        },
        risk_level="low",
        requires_approval=False,
        max_calls_per_minute=20
    ),
    
    "create_support_ticket": ToolDefinition(
        name="create_support_ticket",
        description="Create a new customer support ticket",
        parameters={
            "customer_id": "string - Customer identifier",
            "subject": "string - Ticket subject",
            "description": "string - Detailed description",
            "priority": "string - low, medium, high"
        },
        risk_level="low",
        requires_approval=False,
        max_calls_per_minute=10
    ),
    
    "get_customer_info": ToolDefinition(
        name="get_customer_info",
        description="Retrieve customer profile information",
        parameters={
            "customer_id": "string - Customer identifier",
            "fields": "array - Specific fields to retrieve"
        },
        risk_level="medium",
        requires_approval=False,
        max_calls_per_minute=15
    ),
    
    # Refund/Billing Tools
    "lookup_order": ToolDefinition(
        name="lookup_order",
        description="Look up order details by order ID",
        parameters={
            "order_id": "string - Order identifier",
            "include_items": "boolean - Include line items"
        },
        risk_level="low",
        requires_approval=False,
        max_calls_per_minute=20
    ),
    
    "issue_refund": ToolDefinition(
        name="issue_refund",
        description="Process a refund for an order",
        parameters={
            "order_id": "string - Order identifier",
            "amount": "number - Refund amount in dollars",
            "reason": "string - Reason for refund"
        },
        risk_level="high",
        requires_approval=True,  # Always requires approval
        max_calls_per_minute=3
    ),
    
    "check_payment_status": ToolDefinition(
        name="check_payment_status",
        description="Check payment status for an order",
        parameters={
            "order_id": "string - Order identifier"
        },
        risk_level="low",
        requires_approval=False,
        max_calls_per_minute=15
    ),
    
    # Admin/DevOps Tools
    "get_system_health": ToolDefinition(
        name="get_system_health",
        description="Get current system health metrics (read-only)",
        parameters={
            "service": "string - Service name to check"
        },
        risk_level="low",
        requires_approval=False,
        max_calls_per_minute=30
    ),
    
    "restart_service": ToolDefinition(
        name="restart_service",
        description="Restart a specific service (controlled)",
        parameters={
            "service": "string - Service name",
            "environment": "string - dev, staging, prod"
        },
        risk_level="high",
        requires_approval=True,
        max_calls_per_minute=2
    ),
    
    "view_logs": ToolDefinition(
        name="view_logs",
        description="View service logs (read-only)",
        parameters={
            "service": "string - Service name",
            "lines": "integer - Number of lines to retrieve",
            "level": "string - Log level filter"
        },
        risk_level="low",
        requires_approval=False,
        max_calls_per_minute=10
    ),
    
    "run_diagnostic": ToolDefinition(
        name="run_diagnostic",
        description="Run diagnostic script in sandbox",
        parameters={
            "diagnostic_type": "string - Type of diagnostic",
            "target": "string - Target service or component"
        },
        risk_level="medium",
        requires_approval=False,
        max_calls_per_minute=5
    ),
    
    # Dangerous Tools (should be forbidden for most agents)
    "execute_database_query": ToolDefinition(
        name="execute_database_query",
        description="Execute arbitrary database query",
        parameters={
            "query": "string - SQL query",
            "database": "string - Database name"
        },
        risk_level="critical",
        requires_approval=True,
        max_calls_per_minute=1
    ),
    
    "send_email": ToolDefinition(
        name="send_email",
        description="Send email to external address",
        parameters={
            "to": "string - Recipient email",
            "subject": "string - Email subject",
            "body": "string - Email body"
        },
        risk_level="high",
        requires_approval=True,
        max_calls_per_minute=5
    ),
    
    "export_customer_data": ToolDefinition(
        name="export_customer_data",
        description="Export customer data to file",
        parameters={
            "customer_ids": "array - List of customer IDs",
            "format": "string - Export format (csv, json)",
            "include_pii": "boolean - Include PII fields"
        },
        risk_level="critical",
        requires_approval=True,
        max_calls_per_minute=1
    )
}


# ============================================================================
# AGENT ROLE DEFINITIONS
# ============================================================================

AGENT_ROLES = {
    "support-agent": AgentRole(
        agent_id="support-agent",
        display_name="Customer Support Agent",
        description="Assists customers with support inquiries, creates tickets, searches knowledge base",
        autonomy_level=AutonomyLevel.CONDITIONAL,
        allowed_tools=[
            "search_knowledge_base",
            "create_support_ticket",
            "get_customer_info",
            "lookup_order",
            "check_payment_status"
        ],
        forbidden_tools=[
            "issue_refund",
            "execute_database_query",
            "restart_service",
            "export_customer_data"
        ],
        data_access_scope=["customer_profile", "orders", "tickets", "knowledge_base"],
        can_access_pii=True,  # Can see customer names, emails
        can_modify_data=True,  # Can create tickets
        requires_mfa=False
    ),
    
    "refund-agent": AgentRole(
        agent_id="refund-agent",
        display_name="Refund & Billing Agent",
        description="Processes refunds and handles billing inquiries within defined limits",
        autonomy_level=AutonomyLevel.BOUNDED,
        allowed_tools=[
            "lookup_order",
            "check_payment_status",
            "issue_refund",
            "get_customer_info"
        ],
        forbidden_tools=[
            "execute_database_query",
            "restart_service",
            "export_customer_data",
            "send_email"
        ],
        data_access_scope=["orders", "payments", "customer_profile"],
        max_refund_amount=500.0,  # Cannot refund more than $500 without approval
        can_access_pii=True,
        can_modify_data=True,  # Can issue refunds
        requires_mfa=False
    ),
    
    "admin-agent": AgentRole(
        agent_id="admin-agent",
        display_name="Admin & DevOps Assistant",
        description="Performs system diagnostics and controlled operations in non-prod environments",
        autonomy_level=AutonomyLevel.SUPERVISED,  # All actions require approval
        allowed_tools=[
            "get_system_health",
            "view_logs",
            "run_diagnostic",
            "restart_service"  # Only in dev/staging
        ],
        forbidden_tools=[
            "execute_database_query",
            "export_customer_data",
            "issue_refund"
        ],
        data_access_scope=["system_metrics", "logs", "diagnostics"],
        can_access_pii=False,
        can_modify_data=True,  # Can restart services
        requires_mfa=True
    ),
    
    # Malicious agent for testing (should be blocked by all controls)
    "hacker-bot": AgentRole(
        agent_id="hacker-bot",
        display_name="Unauthorized Agent",
        description="Test agent with no permissions - should be blocked",
        autonomy_level=AutonomyLevel.ASSISTIVE,
        allowed_tools=[],  # No tools allowed
        forbidden_tools=list(AVAILABLE_TOOLS.keys()),  # Everything forbidden
        data_access_scope=[],
        can_access_pii=False,
        can_modify_data=False,
        requires_mfa=True
    )
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_agent_role(agent_id: str) -> Optional[AgentRole]:
    """Get agent role definition by ID"""
    return AGENT_ROLES.get(agent_id)


def get_tool_definition(tool_name: str) -> Optional[ToolDefinition]:
    """Get tool definition by name"""
    return AVAILABLE_TOOLS.get(tool_name)


def is_tool_allowed_for_agent(agent_id: str, tool_name: str) -> bool:
    """Check if a tool is allowed for an agent"""
    role = get_agent_role(agent_id)
    if not role:
        return False
    
    # Check forbidden list first
    if tool_name in role.forbidden_tools:
        return False
    
    # Check allowed list
    return tool_name in role.allowed_tools


def get_agent_summary() -> Dict[str, Any]:
    """Get summary of all agents and their capabilities"""
    return {
        agent_id: {
            "display_name": role.display_name,
            "autonomy_level": role.autonomy_level,
            "allowed_tools": role.allowed_tools,
            "data_access": role.data_access_scope,
            "can_access_pii": role.can_access_pii
        }
        for agent_id, role in AGENT_ROLES.items()
    }
