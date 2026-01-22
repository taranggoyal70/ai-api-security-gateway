# AI Agent Client

Real LLM integration for the Agent Security Gateway.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="sk-..."
```

## Usage

### Run Demo Scenarios
```bash
python agent_client.py
```

This will run 5 test scenarios showing:
- ✅ Valid requests that pass security
- ❌ Requests blocked by security controls

### Use in Your Code
```python
from agent_client import SecurityAwareAgent

agent = SecurityAwareAgent(agent_id="support-bot")
result = await agent.process_prompt("Create a ticket for customer 123")
```

## How It Works

1. **User gives natural language prompt**
   - "Refund customer 123 for $250"

2. **OpenAI decides which function to call**
   - Uses function calling to map to API operations

3. **Agent sends request through security gateway**
   - Gateway enforces 5 security controls

4. **Security decision returned**
   - Allowed or blocked with reason

## Available Agent IDs

- `support-bot` - Limited to tickets and refunds
- `finance-bot` - Access to invoices and financial data
- `admin-agent` - Full access to all endpoints

## Example Output

```
💬 User Prompt: Process a refund of $5000 for customer 12345
🤖 Agent: support-bot

🤖 Agent attempting: process_refund
📍 Endpoint: /refunds
📦 Parameters: {'customer_id': '12345', 'amount': 5000}

❌ Security gateway BLOCKED: Guardrail violations: 1 issue(s)
🛡️ Blocked by: Parameter Guardrails
```

## Integration with Dashboard

The dashboard can call the agent via API:

```javascript
const response = await fetch('http://localhost:8003/agent/prompt', {
    method: 'POST',
    body: JSON.stringify({
        prompt: "Create a ticket for customer 123",
        agent_id: "support-bot"
    })
});
```
