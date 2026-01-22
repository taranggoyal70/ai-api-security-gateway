"""
Phase 6: Multi-Agent Collaboration System

Implements secure multi-agent collaboration with:
- Agent role isolation
- Secure communication protocol
- Inter-agent data permissions
- Monitored exchanges
"""

import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class AgentProvider(str, Enum):
    """LLM provider for agents"""
    OPENAI = "openai"
    OLLAMA = "ollama"


class SecureAgent:
    """
    Base class for secure AI agents.
    All agents must go through the security gateway.
    """
    
    def __init__(
        self,
        agent_id: str,
        provider: AgentProvider,
        gateway_url: str = "http://localhost:8004",
        model: str = "gpt-4o-mini"
    ):
        self.agent_id = agent_id
        self.provider = provider
        self.gateway_url = gateway_url
        self.model = model
        self.conversation_history = []
    
    async def call_tool_through_gateway(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call a tool through the security gateway.
        This is the ONLY way agents should execute actions.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/gateway/execute",
                    json={
                        "agent_id": self.agent_id,
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "user_prompt": user_prompt,
                        "request_id": f"{self.agent_id}_{datetime.utcnow().timestamp()}"
                    },
                    timeout=30.0
                )
                return response.json()
            except Exception as e:
                return {
                    "success": False,
                    "decision": "error",
                    "reason": f"Gateway communication error: {str(e)}"
                }
    
    def sanitize_inter_agent_message(self, message: str) -> str:
        """
        Sanitize messages between agents to prevent prompt injection.
        Strips out suspicious instructions.
        """
        # Remove common prompt injection patterns
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all",
            "forget everything",
            "you are now",
            "new instructions",
            "system:",
            "assistant:"
        ]
        
        sanitized = message
        for pattern in dangerous_patterns:
            if pattern.lower() in sanitized.lower():
                # Replace with safe placeholder
                sanitized = sanitized.replace(pattern, "[FILTERED]")
        
        return sanitized
    
    def format_structured_message(
        self,
        message_type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format inter-agent messages in structured format.
        Prevents free-form text that could carry hidden instructions.
        """
        return {
            "from_agent": self.agent_id,
            "message_type": message_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }


class OpenAIAgent(SecureAgent):
    """Agent powered by OpenAI"""
    
    def __init__(
        self,
        agent_id: str,
        gateway_url: str = "http://localhost:8004",
        openai_api_key: Optional[str] = None
    ):
        super().__init__(agent_id, AgentProvider.OPENAI, gateway_url, "gpt-4o-mini")
        self.openai_api_key = openai_api_key
        
        # Define available tools based on agent role
        self.tools = self._get_tools_for_agent()
    
    def _get_tools_for_agent(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for this agent's allowed tools"""
        
        # This would be populated from the agent's role definition
        # For now, returning common tools
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search internal knowledge base for support articles",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "category": {"type": "string", "description": "Optional category filter"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_support_ticket",
                    "description": "Create a customer support ticket",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "subject": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["customer_id", "subject"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_order",
                    "description": "Look up order details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string"},
                            "include_items": {"type": "boolean"}
                        },
                        "required": ["order_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "issue_refund",
                    "description": "Process a customer refund",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string"},
                            "amount": {"type": "number"},
                            "reason": {"type": "string"}
                        },
                        "required": ["order_id", "amount"]
                    }
                }
            }
        ]
    
    async def process_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """Process user prompt using OpenAI"""
        
        if not self.openai_api_key:
            return {
                "error": "OpenAI API key not configured",
                "agent_id": self.agent_id
            }
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            messages = [
                {
                    "role": "system",
                    "content": f"""You are {self.agent_id}. You help users by calling appropriate tools.
Always use the tools provided - never make up information.
Be helpful but follow all security policies."""
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
            
            # Call OpenAI
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if agent wants to call tools
            if message.tool_calls:
                results = []
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Call through security gateway
                    result = await self.call_tool_through_gateway(
                        tool_name=function_name,
                        parameters=arguments,
                        user_prompt=user_prompt
                    )
                    
                    results.append({
                        "function": function_name,
                        "arguments": arguments,
                        "gateway_result": result
                    })
                
                return {
                    "agent_id": self.agent_id,
                    "provider": "openai",
                    "agent_response": message.content,
                    "tool_calls": results,
                    "user_prompt": user_prompt
                }
            else:
                return {
                    "agent_id": self.agent_id,
                    "provider": "openai",
                    "agent_response": message.content,
                    "tool_calls": [],
                    "user_prompt": user_prompt
                }
        
        except Exception as e:
            return {
                "error": str(e),
                "agent_id": self.agent_id
            }


class OllamaAgent(SecureAgent):
    """Agent powered by Ollama (local LLM)"""
    
    def __init__(
        self,
        agent_id: str,
        gateway_url: str = "http://localhost:8004",
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3.2"
    ):
        super().__init__(agent_id, AgentProvider.OLLAMA, gateway_url, model)
        self.ollama_url = ollama_url
    
    async def process_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """Process user prompt using Ollama"""
        
        # Build system prompt with tools
        tools_description = """
Available tools:
- search_knowledge_base(query, category): Search knowledge base
- create_support_ticket(customer_id, subject, description, priority): Create ticket
- lookup_order(order_id, include_items): Look up order
- issue_refund(order_id, amount, reason): Process refund

Respond with JSON in this format:
{
  "function": "function_name",
  "arguments": {"param": "value"},
  "explanation": "Why you're calling this"
}

If you can't help, respond: {"function": "none", "explanation": "reason"}
"""
        
        system_prompt = f"You are {self.agent_id}. {tools_description}"
        full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\n\nYour JSON response:"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "temperature": 0.3
                    },
                    timeout=60.0
                )
                
                result = response.json()
                llm_output = result.get("response", "")
                
                # Parse JSON from output
                parsed = self._parse_json_response(llm_output)
                
                if not parsed or parsed.get("function") == "none":
                    return {
                        "agent_id": self.agent_id,
                        "provider": "ollama",
                        "agent_response": parsed.get("explanation", "I cannot help with that."),
                        "tool_calls": []
                    }
                
                # Call tool through gateway
                function_name = parsed["function"]
                arguments = parsed.get("arguments", {})
                
                gateway_result = await self.call_tool_through_gateway(
                    tool_name=function_name,
                    parameters=arguments,
                    user_prompt=user_prompt
                )
                
                return {
                    "agent_id": self.agent_id,
                    "provider": "ollama",
                    "agent_response": parsed.get("explanation", ""),
                    "tool_calls": [{
                        "function": function_name,
                        "arguments": arguments,
                        "gateway_result": gateway_result
                    }],
                    "user_prompt": user_prompt
                }
            
            except Exception as e:
                return {
                    "error": str(e),
                    "agent_id": self.agent_id
                }
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        try:
            # Find JSON in text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        return None


class MultiAgentCoordinator:
    """
    Coordinates multiple agents working together.
    Ensures secure communication and prevents cross-agent attacks.
    """
    
    def __init__(self, gateway_url: str = "http://localhost:8004"):
        self.gateway_url = gateway_url
        self.agents: Dict[str, SecureAgent] = {}
        self.conversation_log = []
    
    def register_agent(self, agent: SecureAgent):
        """Register an agent with the coordinator"""
        self.agents[agent.agent_id] = agent
    
    async def send_message_between_agents(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send message from one agent to another with security checks.
        Implements secure inter-agent communication protocol.
        """
        
        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            return {"error": "Agent not found"}
        
        from_agent = self.agents[from_agent_id]
        to_agent = self.agents[to_agent_id]
        
        # Sanitize message to prevent prompt injection
        sanitized_message = from_agent.sanitize_inter_agent_message(message)
        
        # Format as structured message
        structured_msg = from_agent.format_structured_message(
            message_type="agent_communication",
            content=sanitized_message,
            metadata={"original_length": len(message)}
        )
        
        # Log the exchange
        self.conversation_log.append({
            "from": from_agent_id,
            "to": to_agent_id,
            "message": structured_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "sanitized": sanitized_message != message,
            "message": structured_msg
        }
    
    def get_conversation_log(self) -> List[Dict[str, Any]]:
        """Get full conversation log for audit"""
        return self.conversation_log
