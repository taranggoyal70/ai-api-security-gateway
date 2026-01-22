"""
Agent Identity Enforcement - Control #2

REAL-TIME ENFORCEMENT:
- Treats agent like external client
- Maps agent → allowed endpoints
- Prevents privilege explosion

This is NOT a simulator - actual access control happens here.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class IdentityResult(BaseModel):
    allowed: bool
    message: str
    agent_id: str
    endpoint: str


class AgentIdentityEnforcer:
    """
    Agent identity and permission enforcement
    
    Prevents:
    - Unauthorized endpoint access
    - Privilege escalation
    - Agent impersonation
    """
    
    def __init__(self):
        # Define agent permissions (like RBAC)
        self.agent_permissions = {
            "support-bot": {
                "allowed_endpoints": ["/tickets", "/refunds"],
                "allowed_methods": ["GET", "POST"],
                "max_refund_amount": 500,
                "description": "Customer support agent - limited access"
            },
            "finance-bot": {
                "allowed_endpoints": ["/invoices", "/refunds", "/export"],
                "allowed_methods": ["GET", "POST"],
                "max_refund_amount": 5000,
                "description": "Finance agent - invoice and refund access"
            },
            "admin-agent": {
                "allowed_endpoints": ["*"],  # All endpoints
                "allowed_methods": ["*"],  # All methods
                "max_refund_amount": 999999,
                "description": "Admin agent - full access"
            },
            "read-only-bot": {
                "allowed_endpoints": ["*"],
                "allowed_methods": ["GET"],  # Read-only
                "max_refund_amount": 0,
                "description": "Read-only agent - no mutations"
            },
            "demo-agent": {
                "allowed_endpoints": ["/sync/safe", "/sync/unsafe"],
                "allowed_methods": ["GET"],
                "max_refund_amount": 0,
                "description": "Demo agent for testing"
            }
        }
    
    def check_permission(
        self,
        agent_id: str,
        endpoint: str,
        method: str = "GET"
    ) -> IdentityResult:
        """
        Check if agent has permission to access endpoint
        
        Returns:
            IdentityResult with allow/deny decision
        """
        
        # Check if agent exists
        if agent_id not in self.agent_permissions:
            return IdentityResult(
                allowed=False,
                message=f"Unknown agent ID: '{agent_id}' - access denied",
                agent_id=agent_id,
                endpoint=endpoint
            )
        
        permissions = self.agent_permissions[agent_id]
        allowed_endpoints = permissions["allowed_endpoints"]
        allowed_methods = permissions["allowed_methods"]
        
        # Check endpoint permission
        endpoint_allowed = False
        if "*" in allowed_endpoints:
            endpoint_allowed = True
        elif endpoint in allowed_endpoints:
            endpoint_allowed = True
        elif any(endpoint.startswith(ep) for ep in allowed_endpoints):
            endpoint_allowed = True
        
        if not endpoint_allowed:
            return IdentityResult(
                allowed=False,
                message=f"Agent '{agent_id}' not authorized for endpoint '{endpoint}'. Allowed: {allowed_endpoints}",
                agent_id=agent_id,
                endpoint=endpoint
            )
        
        # Check method permission
        method_allowed = False
        if "*" in allowed_methods:
            method_allowed = True
        elif method in allowed_methods:
            method_allowed = True
        
        if not method_allowed:
            return IdentityResult(
                allowed=False,
                message=f"Agent '{agent_id}' not authorized for method '{method}'. Allowed: {allowed_methods}",
                agent_id=agent_id,
                endpoint=endpoint
            )
        
        # All checks passed
        return IdentityResult(
            allowed=True,
            message=f"Agent '{agent_id}' authorized for {method} {endpoint}",
            agent_id=agent_id,
            endpoint=endpoint
        )
    
    def get_agent_max_refund(self, agent_id: str) -> int:
        """Get maximum refund amount for agent"""
        if agent_id in self.agent_permissions:
            return self.agent_permissions[agent_id].get("max_refund_amount", 0)
        return 0
    
    def add_agent(
        self,
        agent_id: str,
        allowed_endpoints: List[str],
        allowed_methods: List[str],
        max_refund_amount: int = 0,
        description: str = ""
    ):
        """Add or update agent permissions"""
        self.agent_permissions[agent_id] = {
            "allowed_endpoints": allowed_endpoints,
            "allowed_methods": allowed_methods,
            "max_refund_amount": max_refund_amount,
            "description": description
        }
    
    def list_agents(self) -> Dict[str, Dict]:
        """List all registered agents and their permissions"""
        return self.agent_permissions
