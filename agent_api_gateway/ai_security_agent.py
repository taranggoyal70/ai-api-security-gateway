"""
AI Security Agent - Real Intelligence for API Validation

Uses LLM (GPT/Ollama) to intelligently analyze API requests and responses.
Not just pattern matching - actual reasoning about security threats.
"""

import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


class AISecurityAgent:
    """
    Real AI agent that uses LLM to validate API security.
    
    Capabilities:
    - Analyzes requests for suspicious behavior
    - Learns from past attacks
    - Detects novel/zero-day threats
    - Provides reasoning for decisions
    - Adapts to new attack patterns
    """
    
    def __init__(
        self,
        llm_provider: str = "ollama",  # or "openai"
        model: str = "llama3.2",
        gateway_url: str = "http://localhost:7100"
    ):
        self.llm_provider = llm_provider
        self.model = model
        self.gateway_url = gateway_url
        self.client = httpx.Client(timeout=30.0)
        
        # Learning database - stores past threats
        self.threat_memory = []
        self.api_behavior_profiles = defaultdict(list)
        
        # LLM endpoints
        if llm_provider == "ollama":
            self.llm_url = "http://localhost:11434/api/generate"
        else:
            self.llm_url = "https://api.openai.com/v1/chat/completions"
    
    # ========================================================================
    # AI-POWERED VALIDATION
    # ========================================================================
    
    def analyze_request_with_ai(
        self,
        agent_id: str,
        target_url: str,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze if a request is safe.
        
        The AI considers:
        - Is this API known to be safe?
        - Do the parameters look suspicious?
        - Is this similar to past attacks?
        - What's the intent behind this request?
        """
        
        print(f"\n🤖 AI Agent analyzing request...")
        print(f"   Target: {target_url}")
        print(f"   Params: {params}")
        
        # Build context for AI
        context = self._build_request_context(agent_id, target_url, method, params)
        
        # Ask AI to analyze
        prompt = f"""You are a cybersecurity expert analyzing an API request.

REQUEST DETAILS:
- Agent ID: {agent_id}
- Target URL: {target_url}
- Method: {method}
- Parameters: {json.dumps(params, indent=2)}

CONTEXT:
{context}

ANALYZE THIS REQUEST:
1. Is this API call safe or suspicious?
2. Are there any security concerns in the parameters?
3. Could this be an attack attempt? What type?
4. What's the risk level (low/medium/high/critical)?
5. Should this request be allowed, blocked, or require human review?

Provide your analysis in JSON format:
{{
    "decision": "allow|block|review",
    "risk_level": "low|medium|high|critical",
    "threats_detected": ["list of threats"],
    "reasoning": "detailed explanation",
    "confidence": 0.0-1.0
}}
"""
        
        # Get AI response
        ai_response = self._call_llm(prompt)
        
        # Parse AI decision
        try:
            decision = json.loads(ai_response)
        except:
            # If AI response isn't valid JSON, extract key info
            decision = {
                "decision": "review",
                "risk_level": "medium",
                "threats_detected": [],
                "reasoning": ai_response,
                "confidence": 0.5
            }
        
        print(f"\n   AI Decision: {decision['decision'].upper()}")
        print(f"   Risk Level: {decision['risk_level']}")
        print(f"   Reasoning: {decision['reasoning'][:100]}...")
        
        # Learn from this decision
        self._learn_from_request(target_url, params, decision)
        
        return decision
    
    def analyze_response_with_ai(
        self,
        target_url: str,
        response_data: Any
    ) -> Dict[str, Any]:
        """
        Use AI to analyze if a response is safe.
        
        The AI considers:
        - Does the response contain malicious content?
        - Is there suspicious data in the response?
        - Does this match known attack patterns?
        - Is PII being leaked?
        """
        
        print(f"\n🤖 AI Agent analyzing response...")
        
        # Build context
        context = self._build_response_context(target_url, response_data)
        
        # Ask AI to analyze
        prompt = f"""You are a cybersecurity expert analyzing an API response.

RESPONSE DETAILS:
- API: {target_url}
- Response Data: {json.dumps(response_data, indent=2)[:1000]}

CONTEXT:
{context}

ANALYZE THIS RESPONSE:
1. Does this response contain malicious content (XSS, scripts, etc.)?
2. Is there sensitive data (PII, API keys, passwords) being leaked?
3. Are there suspicious redirects or URLs?
4. Does this look like a compromised API response?
5. Should this response be allowed, sanitized, or blocked?

Provide your analysis in JSON format:
{{
    "decision": "allow|sanitize|block",
    "risk_level": "low|medium|high|critical",
    "threats_detected": ["list of threats"],
    "pii_found": ["list of PII types"],
    "reasoning": "detailed explanation",
    "confidence": 0.0-1.0
}}
"""
        
        # Get AI response
        ai_response = self._call_llm(prompt)
        
        # Parse AI decision
        try:
            decision = json.loads(ai_response)
        except:
            decision = {
                "decision": "allow",
                "risk_level": "low",
                "threats_detected": [],
                "pii_found": [],
                "reasoning": ai_response,
                "confidence": 0.5
            }
        
        print(f"\n   AI Decision: {decision['decision'].upper()}")
        print(f"   Risk Level: {decision['risk_level']}")
        print(f"   Threats: {decision['threats_detected']}")
        
        # Learn from this response
        self._learn_from_response(target_url, response_data, decision)
        
        return decision
    
    def detect_anomaly_with_ai(
        self,
        agent_id: str,
        target_url: str,
        current_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to detect if this request is anomalous compared to normal behavior.
        
        The AI considers:
        - Is this different from normal requests to this API?
        - Is the agent behaving unusually?
        - Could this be a compromised agent?
        """
        
        # Get historical behavior
        past_requests = self.api_behavior_profiles[target_url][-10:]
        
        if len(past_requests) < 3:
            return {"anomaly": False, "reasoning": "Not enough historical data"}
        
        prompt = f"""You are a cybersecurity expert analyzing API usage patterns.

CURRENT REQUEST:
{json.dumps(current_request, indent=2)}

PAST NORMAL REQUESTS TO THIS API:
{json.dumps(past_requests, indent=2)}

ANALYZE:
1. Is this current request significantly different from past requests?
2. What patterns do you see in the normal requests?
3. Is this current request anomalous or suspicious?
4. Could this indicate a compromised agent or attack?

Provide your analysis in JSON format:
{{
    "anomaly": true|false,
    "anomaly_score": 0.0-1.0,
    "differences": ["list of differences"],
    "reasoning": "detailed explanation"
}}
"""
        
        ai_response = self._call_llm(prompt)
        
        try:
            decision = json.loads(ai_response)
        except:
            decision = {
                "anomaly": False,
                "anomaly_score": 0.0,
                "differences": [],
                "reasoning": ai_response
            }
        
        return decision
    
    # ========================================================================
    # LLM INTEGRATION
    # ========================================================================
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM (Ollama or OpenAI) for analysis"""
        
        if self.llm_provider == "ollama":
            response = self.client.post(
                self.llm_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return '{"decision": "review", "reasoning": "LLM unavailable"}'
        
        else:  # OpenAI
            # Implement OpenAI call
            pass
    
    # ========================================================================
    # LEARNING & MEMORY
    # ========================================================================
    
    def _learn_from_request(
        self,
        target_url: str,
        params: Dict[str, Any],
        decision: Dict[str, Any]
    ):
        """Learn from this request for future analysis"""
        
        # Store in threat memory if it was blocked
        if decision["decision"] == "block":
            self.threat_memory.append({
                "timestamp": datetime.utcnow().isoformat(),
                "url": target_url,
                "params": params,
                "threats": decision["threats_detected"],
                "reasoning": decision["reasoning"]
            })
        
        # Store in behavior profile
        self.api_behavior_profiles[target_url].append({
            "timestamp": datetime.utcnow().isoformat(),
            "params": params,
            "decision": decision["decision"]
        })
        
        # Keep only last 100 entries per API
        if len(self.api_behavior_profiles[target_url]) > 100:
            self.api_behavior_profiles[target_url] = \
                self.api_behavior_profiles[target_url][-100:]
    
    def _learn_from_response(
        self,
        target_url: str,
        response_data: Any,
        decision: Dict[str, Any]
    ):
        """Learn from this response for future analysis"""
        
        if decision["threats_detected"]:
            self.threat_memory.append({
                "timestamp": datetime.utcnow().isoformat(),
                "url": target_url,
                "response_threats": decision["threats_detected"],
                "pii_found": decision.get("pii_found", []),
                "reasoning": decision["reasoning"]
            })
    
    def _build_request_context(
        self,
        agent_id: str,
        target_url: str,
        method: str,
        params: Dict[str, Any]
    ) -> str:
        """Build context for AI analysis"""
        
        context_parts = []
        
        # Past threats
        recent_threats = self.threat_memory[-5:]
        if recent_threats:
            context_parts.append(f"Recent threats detected: {len(recent_threats)}")
            context_parts.append(f"Common threat types: {set([t for threat in recent_threats for t in threat.get('threats', [])])}")
        
        # API behavior
        past_requests = self.api_behavior_profiles[target_url]
        if past_requests:
            context_parts.append(f"This API has been called {len(past_requests)} times before")
            blocked_count = sum(1 for r in past_requests if r.get("decision") == "block")
            if blocked_count > 0:
                context_parts.append(f"WARNING: {blocked_count} requests to this API were blocked before")
        
        return "\n".join(context_parts) if context_parts else "No historical context available"
    
    def _build_response_context(
        self,
        target_url: str,
        response_data: Any
    ) -> str:
        """Build context for response analysis"""
        
        context_parts = []
        
        # Check if this API has had issues before
        api_threats = [t for t in self.threat_memory if t.get("url") == target_url]
        if api_threats:
            context_parts.append(f"WARNING: This API has had {len(api_threats)} security issues before")
            threat_types = set([t for threat in api_threats for t in threat.get("response_threats", [])])
            context_parts.append(f"Past threat types: {threat_types}")
        
        return "\n".join(context_parts) if context_parts else "No historical issues with this API"
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def get_threat_report(self) -> Dict[str, Any]:
        """Get summary of threats detected"""
        
        return {
            "total_threats": len(self.threat_memory),
            "recent_threats": self.threat_memory[-10:],
            "apis_monitored": len(self.api_behavior_profiles),
            "threat_types": self._get_threat_type_distribution()
        }
    
    def _get_threat_type_distribution(self) -> Dict[str, int]:
        """Get distribution of threat types"""
        
        distribution = defaultdict(int)
        for threat in self.threat_memory:
            for threat_type in threat.get("threats", []):
                distribution[threat_type] += 1
        
        return dict(distribution)


# ============================================================================
# DEMO
# ============================================================================

def run_ai_agent_demo():
    """Demonstrate AI security agent in action"""
    
    print("\n" + "="*60)
    print("🤖 AI Security Agent - Real Intelligence Demo")
    print("="*60)
    
    agent = AISecurityAgent()
    
    print("\n" + "="*60)
    print("TEST 1: Normal Request - AI Analysis")
    print("="*60)
    
    decision = agent.analyze_request_with_ai(
        agent_id="design-agent-001",
        target_url="https://api.unsplash.com/search/photos",
        method="GET",
        params={"query": "mountain landscape", "per_page": 10}
    )
    
    print("\n" + "="*60)
    print("TEST 2: Suspicious Request - AI Analysis")
    print("="*60)
    
    decision = agent.analyze_request_with_ai(
        agent_id="design-agent-001",
        target_url="https://api.unsplash.com/search/photos",
        method="GET",
        params={"query": "test' OR '1'='1", "per_page": 10}
    )
    
    print("\n" + "="*60)
    print("TEST 3: Response Analysis - AI Checks for XSS")
    print("="*60)
    
    decision = agent.analyze_response_with_ai(
        target_url="https://api.unsplash.com/photos",
        response_data={
            "photos": [
                {
                    "id": "123",
                    "description": "Beautiful mountain <script>alert('xss')</script>",
                    "url": "https://images.unsplash.com/photo-123"
                }
            ]
        }
    )
    
    print("\n" + "="*60)
    print("TEST 4: Anomaly Detection - Unusual Behavior")
    print("="*60)
    
    # Simulate normal requests
    for i in range(5):
        agent.api_behavior_profiles["https://api.unsplash.com/search/photos"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "params": {"query": f"landscape{i}", "per_page": 10},
            "decision": "allow"
        })
    
    # Now test anomalous request
    decision = agent.detect_anomaly_with_ai(
        agent_id="design-agent-001",
        target_url="https://api.unsplash.com/search/photos",
        current_request={
            "query": "test' UNION SELECT * FROM users--",
            "per_page": 10000  # Unusual high number
        }
    )
    
    print(f"\n   Anomaly Detected: {decision.get('anomaly', False)}")
    print(f"   Anomaly Score: {decision.get('anomaly_score', 0)}")
    print(f"   Reasoning: {decision.get('reasoning', '')[:200]}...")
    
    print("\n" + "="*60)
    print("THREAT REPORT")
    print("="*60)
    
    report = agent.get_threat_report()
    print(f"\n   Total Threats Detected: {report['total_threats']}")
    print(f"   APIs Monitored: {report['apis_monitored']}")
    print(f"   Threat Distribution: {report['threat_types']}")
    
    print("\n" + "="*60)
    print("✅ AI Security Agent Demo Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_ai_agent_demo()
