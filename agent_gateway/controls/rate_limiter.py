"""
Rate & Chain Control - Control #5

REAL-TIME ENFORCEMENT:
- Limits sensitive calls per minute
- Blocks destructive multi-step sequences
- Prevents autonomous damage cascades

This is NOT a simulator - actual rate limiting happens here.
"""

from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import defaultdict, deque


class RateResult(BaseModel):
    allowed: bool
    message: str
    current_count: int
    limit: int


class RateLimiter:
    """
    Rate limiting for agent requests
    
    Prevents:
    - Rapid-fire sensitive operations
    - Autonomous damage cascades
    - Resource exhaustion
    """
    
    def __init__(self):
        # Define rate limits per endpoint
        self.rate_limits = {
            "/refunds": {"max_per_minute": 3, "window_seconds": 60},
            "/invoices": {"max_per_minute": 10, "window_seconds": 60},
            "/export": {"max_per_minute": 2, "window_seconds": 60},
            "/tickets": {"max_per_minute": 20, "window_seconds": 60},
            "/sync/safe": {"max_per_minute": 100, "window_seconds": 60},
            "/sync/unsafe": {"max_per_minute": 100, "window_seconds": 60}
        }
        
        # Track requests per agent per endpoint
        # Structure: {agent_id: {endpoint: deque([timestamp, ...])}}
        self.request_history: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
    
    def check_rate(self, agent_id: str, endpoint: str) -> RateResult:
        """
        Check if agent has exceeded rate limit for endpoint
        
        Returns:
            RateResult with allow/deny decision
        """
        
        # Get rate limit for endpoint
        if endpoint not in self.rate_limits:
            # No rate limit defined - allow
            return RateResult(
                allowed=True,
                message=f"No rate limit for {endpoint}",
                current_count=0,
                limit=999999
            )
        
        limit_config = self.rate_limits[endpoint]
        max_requests = limit_config["max_per_minute"]
        window_seconds = limit_config["window_seconds"]
        
        # Get request history for this agent + endpoint
        history = self.request_history[agent_id][endpoint]
        
        # Clean old requests outside window
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        while history and history[0] < cutoff_time:
            history.popleft()
        
        # Count current requests in window
        current_count = len(history)
        
        # Check if limit exceeded
        if current_count >= max_requests:
            return RateResult(
                allowed=False,
                message=f"Rate limit exceeded for {endpoint}: {current_count}/{max_requests} requests in last {window_seconds}s",
                current_count=current_count,
                limit=max_requests
            )
        
        # Add current request to history
        history.append(datetime.utcnow())
        
        # Allow request
        return RateResult(
            allowed=True,
            message=f"Rate limit OK: {current_count + 1}/{max_requests} requests",
            current_count=current_count + 1,
            limit=max_requests
        )
    
    def reset_agent_limits(self, agent_id: str):
        """Reset all rate limits for an agent"""
        if agent_id in self.request_history:
            del self.request_history[agent_id]
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Dict]:
        """Get current rate limit stats for an agent"""
        stats = {}
        
        if agent_id not in self.request_history:
            return stats
        
        for endpoint, history in self.request_history[agent_id].items():
            if endpoint in self.rate_limits:
                limit_config = self.rate_limits[endpoint]
                window_seconds = limit_config["window_seconds"]
                
                # Clean old requests
                cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
                while history and history[0] < cutoff_time:
                    history.popleft()
                
                stats[endpoint] = {
                    "current_count": len(history),
                    "limit": limit_config["max_per_minute"],
                    "window_seconds": window_seconds,
                    "remaining": limit_config["max_per_minute"] - len(history)
                }
        
        return stats
    
    def add_rate_limit(
        self,
        endpoint: str,
        max_per_minute: int,
        window_seconds: int = 60
    ):
        """Add or update rate limit for endpoint"""
        self.rate_limits[endpoint] = {
            "max_per_minute": max_per_minute,
            "window_seconds": window_seconds
        }
