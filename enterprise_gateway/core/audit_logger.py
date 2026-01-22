"""
Phase 5: Observability - Logging and Audit Trail

Complete logging system with audit trails, replay capability, and risk scoring.
Every agent action is recorded for compliance and debugging.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from enum import Enum


class EventType(str, Enum):
    """Types of security events"""
    TOOL_CALL_ALLOWED = "tool_call_allowed"
    TOOL_CALL_DENIED = "tool_call_denied"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    TAINT_DETECTED = "taint_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    AGENT_ERROR = "agent_error"


class RiskLevel(str, Enum):
    """Risk levels for events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent:
    """Single audit event"""
    
    def __init__(
        self,
        event_type: EventType,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        decision: str,
        reason: str,
        risk_level: RiskLevel,
        user_prompt: Optional[str] = None,
        blocked_by: Optional[str] = None,
        request_id: Optional[str] = None,
        execution_result: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_id = f"evt_{datetime.utcnow().timestamp()}"
        self.event_type = event_type
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.parameters = self._sanitize_parameters(parameters)
        self.decision = decision
        self.reason = reason
        self.risk_level = risk_level
        self.user_prompt = self._sanitize_prompt(user_prompt)
        self.blocked_by = blocked_by
        self.request_id = request_id or self.event_id
        self.execution_result = execution_result
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data in parameters for logging"""
        sanitized = {}
        sensitive_fields = ["password", "api_key", "token", "secret", "ssn", "credit_card"]
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_prompt(self, prompt: Optional[str]) -> Optional[str]:
        """Sanitize user prompt (truncate if too long, mask PII)"""
        if not prompt:
            return None
        
        # Truncate long prompts
        if len(prompt) > 500:
            prompt = prompt[:500] + "... [truncated]"
        
        # Basic PII masking (email, phone)
        import re
        prompt = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***', prompt)
        prompt = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '***-***-****', prompt)
        
        return prompt
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "decision": self.decision,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "user_prompt": self.user_prompt,
            "blocked_by": self.blocked_by,
            "request_id": self.request_id,
            "execution_result": self.execution_result,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Centralized audit logging system.
    Records all agent actions, decisions, and outcomes.
    """
    
    def __init__(self, max_events: int = 1000):
        self.events = deque(maxlen=max_events)
        self.events_by_agent = {}
        self.events_by_type = {}
        self.risk_events = deque(maxlen=100)  # High-risk events only
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "allowed": 0,
            "denied": 0,
            "approval_required": 0,
            "high_risk_events": 0,
            "by_agent": {},
            "by_tool": {},
            "by_risk_level": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
        }
    
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event"""
        # Add to main event log
        self.events.append(event)
        
        # Index by agent
        if event.agent_id not in self.events_by_agent:
            self.events_by_agent[event.agent_id] = deque(maxlen=100)
        self.events_by_agent[event.agent_id].append(event)
        
        # Index by event type
        if event.event_type not in self.events_by_type:
            self.events_by_type[event.event_type] = deque(maxlen=100)
        self.events_by_type[event.event_type].append(event)
        
        # Track high-risk events separately
        if event.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.risk_events.append(event)
            self.stats["high_risk_events"] += 1
        
        # Update statistics
        self.stats["total_requests"] += 1
        
        if event.decision == "allow":
            self.stats["allowed"] += 1
        elif event.decision == "deny":
            self.stats["denied"] += 1
        elif event.decision == "require_approval":
            self.stats["approval_required"] += 1
        
        # Agent stats
        if event.agent_id not in self.stats["by_agent"]:
            self.stats["by_agent"][event.agent_id] = {"total": 0, "allowed": 0, "denied": 0}
        self.stats["by_agent"][event.agent_id]["total"] += 1
        if event.decision == "allow":
            self.stats["by_agent"][event.agent_id]["allowed"] += 1
        elif event.decision == "deny":
            self.stats["by_agent"][event.agent_id]["denied"] += 1
        
        # Tool stats
        if event.tool_name not in self.stats["by_tool"]:
            self.stats["by_tool"][event.tool_name] = {"total": 0, "allowed": 0, "denied": 0}
        self.stats["by_tool"][event.tool_name]["total"] += 1
        if event.decision == "allow":
            self.stats["by_tool"][event.tool_name]["allowed"] += 1
        elif event.decision == "deny":
            self.stats["by_tool"][event.tool_name]["denied"] += 1
        
        # Risk level stats
        self.stats["by_risk_level"][event.risk_level] += 1
    
    def log_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        enforcement_result: Any,
        user_prompt: Optional[str] = None,
        request_id: Optional[str] = None,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a tool call with enforcement decision"""
        
        # Determine event type
        if enforcement_result.decision == "allow":
            event_type = EventType.TOOL_CALL_ALLOWED
        elif enforcement_result.decision == "deny":
            event_type = EventType.TOOL_CALL_DENIED
        elif enforcement_result.decision == "require_approval":
            event_type = EventType.APPROVAL_REQUIRED
        else:
            event_type = EventType.TOOL_CALL_ALLOWED
        
        # Determine risk level from risk score
        risk_score = enforcement_result.risk_score
        if risk_score >= 90:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 70:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        event = AuditEvent(
            event_type=event_type,
            agent_id=agent_id,
            tool_name=tool_name,
            parameters=parameters,
            decision=enforcement_result.decision,
            reason=enforcement_result.reason,
            risk_level=risk_level,
            user_prompt=user_prompt,
            blocked_by=enforcement_result.blocked_by,
            request_id=request_id,
            execution_result=execution_result,
            metadata={"guard_results": enforcement_result.guard_results}
        )
        
        self.log_event(event)
    
    def log_approval(
        self,
        approval_id: str,
        agent_id: str,
        tool_name: str,
        approved: bool,
        approver: str,
        reason: Optional[str] = None
    ) -> None:
        """Log an approval decision"""
        event_type = EventType.APPROVAL_GRANTED if approved else EventType.APPROVAL_DENIED
        
        event = AuditEvent(
            event_type=event_type,
            agent_id=agent_id,
            tool_name=tool_name,
            parameters={},
            decision="approved" if approved else "denied",
            reason=reason or ("Approved by human" if approved else "Denied by human"),
            risk_level=RiskLevel.MEDIUM,
            metadata={"approval_id": approval_id, "approver": approver}
        )
        
        self.log_event(event)
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events"""
        return [event.to_dict() for event in list(self.events)[-limit:]]
    
    def get_events_by_agent(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events for a specific agent"""
        if agent_id not in self.events_by_agent:
            return []
        
        return [event.to_dict() for event in list(self.events_by_agent[agent_id])[-limit:]]
    
    def get_high_risk_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get high-risk events"""
        return [event.to_dict() for event in list(self.risk_events)[-limit:]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        stats = self.stats.copy()
        
        # Calculate percentages
        total = stats["total_requests"]
        if total > 0:
            stats["allow_rate"] = round((stats["allowed"] / total) * 100, 2)
            stats["deny_rate"] = round((stats["denied"] / total) * 100, 2)
            stats["approval_rate"] = round((stats["approval_required"] / total) * 100, 2)
        else:
            stats["allow_rate"] = 0
            stats["deny_rate"] = 0
            stats["approval_rate"] = 0
        
        return stats
    
    def search_events(
        self,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        event_type: Optional[EventType] = None,
        risk_level: Optional[RiskLevel] = None,
        decision: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search events with filters"""
        results = []
        
        for event in self.events:
            # Apply filters
            if agent_id and event.agent_id != agent_id:
                continue
            if tool_name and event.tool_name != tool_name:
                continue
            if event_type and event.event_type != event_type:
                continue
            if risk_level and event.risk_level != risk_level:
                continue
            if decision and event.decision != decision:
                continue
            
            results.append(event.to_dict())
            
            if len(results) >= limit:
                break
        
        return results
    
    def export_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Export a session for replay.
        This allows demonstrating the system with pre-recorded scenarios.
        """
        events = self.get_recent_events(limit=1000)
        
        return {
            "session_id": session_id or f"session_{datetime.utcnow().timestamp()}",
            "exported_at": datetime.utcnow().isoformat(),
            "event_count": len(events),
            "events": events,
            "statistics": self.get_statistics()
        }
    
    def generate_timeline(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate a timeline view of events for visualization.
        Useful for demo dashboards.
        """
        events = self.get_events_by_agent(agent_id, limit=100) if agent_id else self.get_recent_events(limit=100)
        
        timeline = []
        for event in events:
            timeline_entry = {
                "timestamp": event["timestamp"],
                "agent": event["agent_id"],
                "action": f"{event['tool_name']}",
                "decision": event["decision"],
                "risk": event["risk_level"],
                "reason": event["reason"],
                "icon": self._get_icon_for_event(event)
            }
            timeline.append(timeline_entry)
        
        return timeline
    
    def _get_icon_for_event(self, event: Dict[str, Any]) -> str:
        """Get emoji icon for event type"""
        if event["decision"] == "allow":
            return "✅"
        elif event["decision"] == "deny":
            return "❌"
        elif event["decision"] == "require_approval":
            return "⏸️"
        elif event["risk_level"] == "critical":
            return "🚨"
        elif event["risk_level"] == "high":
            return "⚠️"
        else:
            return "ℹ️"
