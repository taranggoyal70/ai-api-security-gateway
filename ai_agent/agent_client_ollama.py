"""
AI Agent Client - Ollama Integration

This agent uses Ollama (local LLM) for function calling.
No API key needed - runs completely locally!
"""

import json
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio


class OllamaSecurityAgent:
    """
    AI Agent that uses Ollama (local LLM) to make API calls 
    through the security gateway.
    """
    
    def __init__(
        self, 
        agent_id: str,
        gateway_url: str = "http://localhost:8002",
        ollama_url: str = "http://localhost:11434",
        model: str = "llama3.2"
    ):
        self.agent_id = agent_id
        self.gateway_url = gateway_url
        self.ollama_url = ollama_url
        self.model = model
        
        # Available API functions
        self.tools = [
            {
                "name": "create_support_ticket",
                "description": "Create a customer support ticket",
                "parameters": {
                    "customer_id": "string - The customer ID",
                    "subject": "string - Ticket subject/title",
                    "priority": "string - low, medium, or high"
                }
            },
            {
                "name": "process_refund",
                "description": "Process a customer refund",
                "parameters": {
                    "customer_id": "string - The customer ID",
                    "amount": "number - Refund amount in dollars",
                    "reason": "string - Reason for refund"
                }
            },
            {
                "name": "get_invoice",
                "description": "Retrieve customer invoice details",
                "parameters": {
                    "customer_id": "string - The customer ID",
                    "invoice_id": "string - Invoice ID (optional)"
                }
            },
            {
                "name": "export_data",
                "description": "Export customer data",
                "parameters": {
                    "format": "string - csv, json, or pdf",
                    "limit": "integer - Number of records to export"
                }
            }
        ]
    
    async def call_api_through_gateway(
        self,
        endpoint: str,
        params: Dict[str, Any],
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send API request through the security gateway."""
        payload = {
            "endpoint": endpoint,
            "method": "GET",
            "params": params,
            "user_prompt": user_prompt
        }
        
        headers = {
            "X-Agent-ID": self.agent_id,
            "X-Request-ID": f"agent_{datetime.utcnow().timestamp()}"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/gateway/secure",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                return response.json()
            except Exception as e:
                return {
                    "allowed": False,
                    "reason": f"Gateway error: {str(e)}",
                    "error": True
                }
    
    def map_function_to_endpoint(self, function_name: str) -> str:
        """Map function names to API endpoints"""
        mapping = {
            "create_support_ticket": "/tickets",
            "process_refund": "/refunds",
            "get_invoice": "/invoices",
            "export_data": "/export"
        }
        return mapping.get(function_name, "/unknown")
    
    async def call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Call Ollama API for LLM response"""
        
        # Build system prompt with available tools
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}\n  Parameters: {tool['parameters']}"
            for tool in self.tools
        ])
        
        system_prompt = f"""You are a {self.agent_id} that helps with customer operations.
You have access to these API functions:

{tools_description}

When a user asks you to do something, respond with a JSON object in this format:
{{
    "function": "function_name",
    "arguments": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "explanation": "Brief explanation of what you're doing"
}}

If you can't help or the request is unclear, respond with:
{{
    "function": "none",
    "explanation": "Reason why you can't help"
}}

IMPORTANT: Only output valid JSON, nothing else."""

        full_prompt = f"{system_prompt}\n\nUser request: {prompt}\n\nYour JSON response:"
        
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
                    timeout=30.0
                )
                
                result = response.json()
                return result
                
            except Exception as e:
                return {
                    "error": str(e),
                    "message": "Failed to call Ollama"
                }
    
    def parse_llm_response(self, llm_output: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        try:
            # Try to find JSON in the response
            start = llm_output.find('{')
            end = llm_output.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = llm_output[start:end]
                return json.loads(json_str)
            
            return None
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return None
    
    async def execute_function_call(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        user_prompt: str
    ) -> Dict[str, Any]:
        """Execute a function call through the security gateway"""
        
        endpoint = self.map_function_to_endpoint(function_name)
        
        print(f"\n🤖 Agent attempting: {function_name}")
        print(f"📍 Endpoint: {endpoint}")
        print(f"📦 Parameters: {arguments}")
        
        # Send through security gateway
        result = await self.call_api_through_gateway(
            endpoint=endpoint,
            params=arguments,
            user_prompt=user_prompt
        )
        
        if result.get("allowed"):
            print(f"✅ Security gateway ALLOWED the request")
        else:
            print(f"❌ Security gateway BLOCKED: {result.get('reason')}")
            print(f"🛡️ Blocked by: {result.get('blocked_by')}")
        
        return result
    
    async def process_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """Process a user prompt using Ollama"""
        
        print(f"\n{'='*60}")
        print(f"💬 User Prompt: {user_prompt}")
        print(f"🤖 Agent: {self.agent_id}")
        print(f"🦙 Using Ollama model: {self.model}")
        print(f"{'='*60}")
        
        # Call Ollama
        print("\n🦙 Calling Ollama...")
        llm_response = await self.call_ollama(user_prompt)
        
        if "error" in llm_response:
            return {
                "error": llm_response["error"],
                "message": "Failed to get LLM response"
            }
        
        # Parse LLM output
        llm_output = llm_response.get("response", "")
        print(f"\n🦙 Ollama response:\n{llm_output}\n")
        
        parsed = self.parse_llm_response(llm_output)
        
        if not parsed:
            return {
                "error": "Failed to parse LLM response",
                "raw_response": llm_output
            }
        
        # Check if LLM wants to call a function
        function_name = parsed.get("function")
        
        if function_name == "none" or not function_name:
            return {
                "agent_response": parsed.get("explanation", "I cannot help with that."),
                "tool_calls": []
            }
        
        # Execute the function call
        arguments = parsed.get("arguments", {})
        result = await self.execute_function_call(
            function_name=function_name,
            arguments=arguments,
            user_prompt=user_prompt
        )
        
        return {
            "agent_response": parsed.get("explanation", ""),
            "tool_calls": [{
                "function": function_name,
                "arguments": arguments,
                "security_result": result
            }],
            "user_prompt": user_prompt
        }


async def demo_ollama_agent():
    """Demo scenarios with Ollama"""
    
    agent = OllamaSecurityAgent(agent_id="support-bot")
    
    scenarios = [
        "Create a support ticket for customer 12345 about billing issue",
        "Process a refund of $250 for customer 12345",
        "Process a refund of $5000 for customer 12345",  # Should be blocked
    ]
    
    print("\n" + "="*60)
    print("🧪 OLLAMA AGENT SECURITY TESTING")
    print("="*60)
    
    for i, prompt in enumerate(scenarios, 1):
        print(f"\n\n📋 Scenario {i}/{len(scenarios)}")
        result = await agent.process_prompt(prompt)
        
        if result.get("tool_calls"):
            for call in result["tool_calls"]:
                security = call["security_result"]
                print(f"\n🔍 Security Decision:")
                print(f"   Allowed: {security.get('allowed')}")
                if not security.get("allowed"):
                    print(f"   Reason: {security.get('reason')}")
        
        await asyncio.sleep(1)
    
    print("\n\n" + "="*60)
    print("✅ Ollama agent testing complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(demo_ollama_agent())
