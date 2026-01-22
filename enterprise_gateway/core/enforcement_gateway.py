"""
Phase 3: Enforcement Layer (Interception Gateway)

The core middleware that intercepts all agent tool/API calls and enforces policies.
Acts as a gateway between AI agents and real backend APIs.
"""

import re
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

import sys
sys.path.append('/Users/tarang/CascadeProjects/windsurf-project/owasp-api10-security-lab/enterprise_gateway')

from config.agent_definitions import (
    get_agent_role, get_tool_definition, is_tool_allowed_for_agent, AVAILABLE_TOOLS
)
from config.governance_policies import (
    get_tool_policy, requires_approval, get_applicable_guards,
    PolicyDecision, SENSITIVE_PATTERNS, PROMPT_INJECTION_PATTERNS,
    APPROVAL_THRESHOLDS
)


class EnforcementDecision(str, Enum):
    """Final enforcement decision"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    SANITIZE_OUTPUT = "sanitize_output"


class EnforcementResult:
    """Result of enforcement check"""
    def __init__(
        self,
        decision: EnforcementDecision,
        reason: str,
        blocked_by: Optional[str] = None,
        requires_approval: bool = False,
        sanitized_output: Optional[Any] = None,
        risk_score: int = 0,
        guard_results: Optional[Dict[str, Any]] = None
    ):
        self.decision = decision
        self.reason = reason
        self.blocked_by = blocked_by
        self.requires_approval = requires_approval
        self.sanitized_output = sanitized_output
        self.risk_score = risk_score
        self.guard_results = guard_results or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "blocked_by": self.blocked_by,
            "requires_approval": self.requires_approval,
            "risk_score": self.risk_score,
            "guard_results": self.guard_results,
            "timestamp": self.timestamp.isoformat()
        }


class EnforcementGateway:
    """
    Core enforcement gateway that intercepts and validates all agent actions.
    Implements zero-trust architecture with defense in depth.
    """
    
    def __init__(self):
        # Rate limiting tracking
        self.rate_limit_history = defaultdict(lambda: deque())
        
        # Action sequence tracking (for detecting suspicious patterns)
        self.action_sequences = defaultdict(lambda: deque(maxlen=10))
        
        # Taint tracking (user-originated data)
        self.tainted_data = {}
        
        # Pending approvals
        self.pending_approvals = {}
        
    # ========================================================================
    # MAIN ENFORCEMENT ENTRY POINT
    # ========================================================================
    
    def enforce(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        user_prompt: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> EnforcementResult:
        """
        Main enforcement function - intercepts and validates tool calls.
        
        This is the single chokepoint through which all agent actions flow.
        Implements multiple layers of security checks.
        """
        
        # Layer 1: Agent Identity Verification
        agent_role = get_agent_role(agent_id)
        if not agent_role:
            return EnforcementResult(
                decision=EnforcementDecision.DENY,
                reason=f"Unknown agent: {agent_id}",
                blocked_by="Agent Identity Verification",
                risk_score=100
            )
        
        # Layer 2: Tool Allowlist Check
        if not is_tool_allowed_for_agent(agent_id, tool_name):
            return EnforcementResult(
                decision=EnforcementDecision.DENY,
                reason=f"Tool '{tool_name}' not in allowlist for agent '{agent_id}'",
                blocked_by="Tool Allowlist",
                risk_score=90
            )
        
        # Layer 3: Tool Policy Check
        tool_policy = get_tool_policy(tool_name)
        if not tool_policy:
            return EnforcementResult(
                decision=EnforcementDecision.DENY,
                reason=f"No policy defined for tool '{tool_name}'",
                blocked_by="Policy Check",
                risk_score=85
            )
        
        if agent_id not in tool_policy.allowed_agents:
            return EnforcementResult(
                decision=EnforcementDecision.DENY,
                reason=f"Agent '{agent_id}' not authorized for tool '{tool_name}'",
                blocked_by="Policy Authorization",
                risk_score=90
            )
        
        # Layer 4: Rate Limiting
        rate_limit_result = self.check_rate_limit(agent_id, tool_name, tool_policy)
        if not rate_limit_result["passed"]:
            return EnforcementResult(
                decision=EnforcementDecision.DENY,
                reason=rate_limit_result["reason"],
                blocked_by="Rate Limiter",
                risk_score=70
            )
        
        # Layer 5: Parameter Validation
        param_validation = self.validate_parameters(tool_name, parameters, tool_policy)
        if not param_validation["passed"]:
            return EnforcementResult(
                decision=EnforcementDecision.DENY,
                reason=param_validation["reason"],
                blocked_by="Parameter Validation",
                risk_score=80
            )
        
        # Layer 6: Prompt Injection Detection
        if user_prompt:
            injection_check = self.check_prompt_injection(user_prompt)
            if not injection_check["passed"]:
                return EnforcementResult(
                    decision=EnforcementDecision.DENY,
                    reason=injection_check["reason"],
                    blocked_by="Prompt Injection Guard",
                    risk_score=95
                )
        
        # Layer 7: Taint Tracking
        if user_prompt:
            taint_result = self.check_taint_tracking(
                user_prompt, parameters, tool_name
            )
            if taint_result["requires_approval"]:
                return EnforcementResult(
                    decision=EnforcementDecision.REQUIRE_APPROVAL,
                    reason=taint_result["reason"],
                    blocked_by="Taint Tracking",
                    requires_approval=True,
                    risk_score=75
                )
        
        # Layer 8: Business Logic Guards
        guard_results = self.run_execution_guards(
            agent_id, tool_name, parameters
        )
        
        # Check if any guard failed
        for guard_name, result in guard_results.items():
            if not result["passed"]:
                if result["action"] == PolicyDecision.DENY:
                    return EnforcementResult(
                        decision=EnforcementDecision.DENY,
                        reason=result["reason"],
                        blocked_by=guard_name,
                        risk_score=result.get("risk_score", 70),
                        guard_results=guard_results
                    )
                elif result["action"] == PolicyDecision.REQUIRE_APPROVAL:
                    return EnforcementResult(
                        decision=EnforcementDecision.REQUIRE_APPROVAL,
                        reason=result["reason"],
                        blocked_by=guard_name,
                        requires_approval=True,
                        risk_score=result.get("risk_score", 60),
                        guard_results=guard_results
                    )
        
        # Layer 9: Approval Requirement Check
        if requires_approval(tool_name, parameters, agent_id):
            return EnforcementResult(
                decision=EnforcementDecision.REQUIRE_APPROVAL,
                reason=f"Tool '{tool_name}' requires approval for these parameters",
                requires_approval=True,
                risk_score=50,
                guard_results=guard_results
            )
        
        # Layer 10: Action Sequence Analysis
        sequence_check = self.check_action_sequence(agent_id, tool_name)
        if not sequence_check["passed"]:
            return EnforcementResult(
                decision=EnforcementDecision.REQUIRE_APPROVAL,
                reason=sequence_check["reason"],
                blocked_by="Sequence Analyzer",
                requires_approval=True,
                risk_score=65
            )
        
        # All checks passed - ALLOW
        # Record this action in sequence history
        self.action_sequences[agent_id].append({
            "tool": tool_name,
            "timestamp": datetime.utcnow(),
            "parameters": parameters
        })
        
        return EnforcementResult(
            decision=EnforcementDecision.ALLOW,
            reason="All security checks passed",
            risk_score=10,
            guard_results=guard_results
        )
    
    # ========================================================================
    # SECURITY CHECK IMPLEMENTATIONS
    # ========================================================================
    
    def check_rate_limit(
        self,
        agent_id: str,
        tool_name: str,
        tool_policy: Any
    ) -> Dict[str, Any]:
        """Check if agent is within rate limits"""
        key = f"{agent_id}:{tool_name}"
        now = datetime.utcnow()
        
        # Clean old entries (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        history = self.rate_limit_history[key]
        while history and history[0] < cutoff:
            history.popleft()
        
        # Check per-minute limit
        if len(history) >= tool_policy.max_calls_per_minute:
            return {
                "passed": False,
                "reason": f"Rate limit exceeded: {len(history)}/{tool_policy.max_calls_per_minute} calls per minute"
            }
        
        # Record this request
        history.append(now)
        
        return {"passed": True}
    
    def validate_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tool_policy: Any
    ) -> Dict[str, Any]:
        """Validate tool parameters against constraints"""
        constraints = tool_policy.parameter_constraints
        
        for param_name, param_value in parameters.items():
            if param_name in constraints:
                constraint = constraints[param_name]
                
                # Check min/max values
                if "min_value" in constraint:
                    if isinstance(param_value, (int, float)):
                        if param_value < constraint["min_value"]:
                            return {
                                "passed": False,
                                "reason": f"Parameter '{param_name}' below minimum: {param_value} < {constraint['min_value']}"
                            }
                
                if "max_value" in constraint:
                    if isinstance(param_value, (int, float)):
                        if param_value > constraint["max_value"]:
                            return {
                                "passed": False,
                                "reason": f"Parameter '{param_name}' exceeds maximum: {param_value} > {constraint['max_value']}"
                            }
                
                # Check allowed values
                if "allowed_values" in constraint:
                    if param_value not in constraint["allowed_values"]:
                        return {
                            "passed": False,
                            "reason": f"Parameter '{param_name}' has invalid value: {param_value}"
                        }
                
                # Check forbidden values
                if "forbidden_values" in constraint:
                    if param_value in constraint["forbidden_values"]:
                        return {
                            "passed": False,
                            "reason": f"Parameter '{param_name}' contains forbidden value: {param_value}"
                        }
                
                # Check forbidden patterns (for SQL injection, etc.)
                if "forbidden_patterns" in constraint:
                    if isinstance(param_value, str):
                        for pattern in constraint["forbidden_patterns"]:
                            if re.search(pattern, param_value, re.IGNORECASE):
                                return {
                                    "passed": False,
                                    "reason": f"Parameter '{param_name}' contains dangerous pattern"
                                }
        
        return {"passed": True}
    
    def check_prompt_injection(self, user_prompt: str) -> Dict[str, Any]:
        """Detect prompt injection attempts"""
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, user_prompt, re.IGNORECASE):
                return {
                    "passed": False,
                    "reason": "Potential prompt injection detected in user input"
                }
        
        return {"passed": True}
    
    def check_taint_tracking(
        self,
        user_prompt: str,
        parameters: Dict[str, Any],
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Track user-originated data and flag if it reaches sensitive operations.
        This prevents users from injecting malicious data through the agent.
        """
        
        # High-risk tools that should not use raw user input
        high_risk_tools = [
            "execute_database_query",
            "issue_refund",
            "export_customer_data",
            "restart_service"
        ]
        
        if tool_name not in high_risk_tools:
            return {"requires_approval": False}
        
        # Check if any parameter values appear in user prompt
        tainted_params = []
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str) and param_value in user_prompt:
                tainted_params.append(param_name)
            elif isinstance(param_value, (int, float)):
                if str(param_value) in user_prompt:
                    tainted_params.append(param_name)
        
        if tainted_params:
            return {
                "requires_approval": True,
                "reason": f"User-originated data detected in sensitive parameters: {', '.join(tainted_params)}"
            }
        
        return {"requires_approval": False}
    
    def run_execution_guards(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Run all applicable execution guards"""
        guards = get_applicable_guards(tool_name, agent_id)
        results = {}
        
        for guard in guards:
            # Call the appropriate guard function
            if guard.check_function == "check_amount_threshold":
                result = self.check_amount_threshold(parameters)
            elif guard.check_function == "check_environment_isolation":
                result = self.check_environment_isolation(parameters)
            elif guard.check_function == "check_pii_protection":
                result = self.check_pii_protection(parameters)
            else:
                result = {"passed": True}  # Unknown guard, pass by default
            
            result["action"] = guard.failure_action
            results[guard.guard_name] = result
        
        return results
    
    def check_amount_threshold(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check if refund amount exceeds threshold"""
        amount = parameters.get("amount", 0)
        threshold = APPROVAL_THRESHOLDS["refund_amount"]["require_approval_above"]
        
        if amount > threshold:
            return {
                "passed": False,
                "reason": f"Refund amount ${amount} exceeds approval threshold ${threshold}",
                "risk_score": 60
            }
        
        return {"passed": True}
    
    def check_environment_isolation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prevent production environment access"""
        environment = parameters.get("environment", "")
        
        forbidden_envs = APPROVAL_THRESHOLDS["service_restart"]["forbidden_environments"]
        
        if environment.lower() in forbidden_envs:
            return {
                "passed": False,
                "reason": f"Access to '{environment}' environment is forbidden",
                "risk_score": 95
            }
        
        return {"passed": True}
    
    def check_pii_protection(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check for PII in parameters"""
        # This is a simplified check - real implementation would be more sophisticated
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                # Check for email patterns
                if re.search(SENSITIVE_PATTERNS["email"], param_value):
                    return {
                        "passed": True,  # Don't block, but flag for sanitization
                        "reason": "PII detected in parameters",
                        "sanitize": True
                    }
        
        return {"passed": True}
    
    def check_action_sequence(
        self,
        agent_id: str,
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Analyze recent action sequence for suspicious patterns.
        E.g., rapid succession of high-risk operations.
        """
        sequence = self.action_sequences[agent_id]
        
        if len(sequence) < 3:
            return {"passed": True}
        
        # Check for rapid high-risk operations
        high_risk_tools = ["issue_refund", "export_customer_data", "restart_service"]
        recent_high_risk = [
            action for action in list(sequence)[-3:]
            if action["tool"] in high_risk_tools
        ]
        
        if len(recent_high_risk) >= 2:
            return {
                "passed": False,
                "reason": "Multiple high-risk operations in quick succession - requires approval"
            }
        
        return {"passed": True}
    
    # ========================================================================
    # OUTPUT SANITIZATION
    # ========================================================================
    
    def sanitize_output(self, output: Any) -> Any:
        """
        Sanitize output to remove PII and sensitive data.
        Used when decision is SANITIZE_OUTPUT.
        """
        if isinstance(output, str):
            sanitized = output
            
            # Mask emails
            sanitized = re.sub(
                SENSITIVE_PATTERNS["email"],
                "***@***.***",
                sanitized
            )
            
            # Mask phone numbers
            sanitized = re.sub(
                SENSITIVE_PATTERNS["phone"],
                "***-***-****",
                sanitized
            )
            
            # Mask SSN
            sanitized = re.sub(
                SENSITIVE_PATTERNS["ssn"],
                "***-**-****",
                sanitized
            )
            
            # Mask credit cards
            sanitized = re.sub(
                SENSITIVE_PATTERNS["credit_card"],
                "****-****-****-****",
                sanitized
            )
            
            return sanitized
        
        elif isinstance(output, dict):
            return {k: self.sanitize_output(v) for k, v in output.items()}
        
        elif isinstance(output, list):
            return [self.sanitize_output(item) for item in output]
        
        return output
    
    # ========================================================================
    # APPROVAL MANAGEMENT
    # ========================================================================
    
    def request_approval(
        self,
        request_id: str,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        reason: str
    ) -> str:
        """Create an approval request"""
        approval_id = f"approval_{request_id}_{datetime.utcnow().timestamp()}"
        
        self.pending_approvals[approval_id] = {
            "request_id": request_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "approved_by": None,
            "approved_at": None
        }
        
        return approval_id
    
    def approve_request(self, approval_id: str, approver: str) -> bool:
        """Approve a pending request"""
        if approval_id not in self.pending_approvals:
            return False
        
        self.pending_approvals[approval_id]["status"] = "approved"
        self.pending_approvals[approval_id]["approved_by"] = approver
        self.pending_approvals[approval_id]["approved_at"] = datetime.utcnow()
        
        return True
    
    def deny_request(self, approval_id: str, approver: str, reason: str) -> bool:
        """Deny a pending request"""
        if approval_id not in self.pending_approvals:
            return False
        
        self.pending_approvals[approval_id]["status"] = "denied"
        self.pending_approvals[approval_id]["denied_by"] = approver
        self.pending_approvals[approval_id]["denied_at"] = datetime.utcnow()
        self.pending_approvals[approval_id]["denial_reason"] = reason
        
        return True
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        return [
            {**approval, "approval_id": approval_id}
            for approval_id, approval in self.pending_approvals.items()
            if approval["status"] == "pending"
        ]
