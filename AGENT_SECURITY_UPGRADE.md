# 🛡️ Agent Security Gateway - Architecture Upgrade

## From Simulator to Real Security System

**Before:** OWASP API #10 Simulator  
**After:** Agent-Aware API Security Gateway

---

## 🏗️ New Architecture

```
User Prompt
     ↓
AI Agent (OpenAI/Claude)
     ↓
🛡️ Agent Security Gateway (NEW - Port 8002)
     ↓
Consumer API (Port 8001)
     ↓
Vendor API (Port 8000)
```

---

## 🔒 5 Core Security Controls

### 1️⃣ Schema & Command Validation
**File:** `agent_gateway/controls/schema_validator.py`

**What it does:**
- Blocks requests with unexpected fields
- Prevents agent hallucinated parameters
- Enforces strict API contracts

**Example:**
```python
# Agent tries to send:
{
  "user_id": "123",
  "amount": 10000,
  "override_checks": true  # ❌ NOT ALLOWED
}

# Gateway enforces:
allowed_fields = ["user_id", "amount"]
# Result: BLOCKED
```

---

### 2️⃣ Agent Identity Enforcement
**File:** `agent_gateway/controls/agent_identity.py`

**What it does:**
- Treats agent like external client
- Maps agent → allowed endpoints
- Prevents privilege explosion

**Example:**
```python
agent_permissions = {
    "support-bot": ["/tickets", "/refunds"],  # Limited access
    "finance-bot": ["/invoices"],
    "admin-agent": ["*"]  # Full access
}

# Header: X-Agent-ID: support-bot
# Request: /admin/delete → ❌ BLOCKED
```

---

### 3️⃣ Parameter Risk Guardrails
**File:** `agent_gateway/controls/parameter_guards.py`

**What it does:**
- Checks dangerous values even if schema valid
- Blocks BFLA-style abuse
- Enforces business logic limits

**Example:**
```python
guardrails = {
    "refund.amount": {"max": 500},
    "query.limit": {"max": 100},
    "export.format": {"forbidden": ["full_db"]}
}

# Agent requests: refund.amount = 5000
# Result: ❌ BLOCKED (exceeds $500 limit)
```

---

### 4️⃣ User-Input Taint Tracking (AI-Specific)
**File:** `agent_gateway/controls/taint_tracker.py`

**What it does:**
- Marks values from user prompts as TAINTED
- Applies extra checks to tainted data
- Prevents prompt injection attacks

**Example:**
```python
# User prompt: "Refund customer 123 $5000"
# Parsed:
{
    "customer_id": "123",  # TAINTED
    "amount": 5000  # TAINTED ⚠️
}

# If tainted data reaches sensitive field:
# → Extra validation required
# → Require human approval
# → Log security event
```

---

### 5️⃣ Rate & Chain Control
**File:** `agent_gateway/controls/rate_limiter.py`

**What it does:**
- Limits sensitive calls per minute
- Blocks destructive multi-step sequences
- Prevents autonomous damage cascades

**Example:**
```python
rate_limits = {
    "refund": {"max_per_minute": 3},
    "delete": {"max_per_minute": 1},
    "export": {"max_per_minute": 2}
}

# Agent makes 4 refund calls in 1 minute
# Result: 4th call → ❌ BLOCKED
```

---

## 🎨 Vue.js Security Dashboard

**File:** `client_ui/agent-dashboard.html`

### Features:
1. **Real-time Request Monitor**
   - Live stream of agent requests
   - Security decision visualization
   - Block/Allow indicators

2. **Control Panel**
   - Enable/disable each security control
   - Adjust guardrail thresholds
   - Configure agent permissions

3. **Security Logs**
   - Taint tracking events
   - Schema violations
   - Rate limit hits
   - Blocked requests

4. **Agent Playground**
   - Test prompts
   - See security checks in action
   - Compare safe vs unsafe flows

---

## 📊 Request Flow Visualization

```
┌─────────────────────────────────────────────────────────┐
│  User Prompt: "Refund customer 123 $5000"              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  AI Agent (GPT-4)                                       │
│  Parses → {customer_id: 123, amount: 5000}             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  🛡️ Agent Security Gateway                              │
│                                                         │
│  ✅ 1. Schema Valid (user_id, amount allowed)          │
│  ✅ 2. Agent ID: support-bot → /refunds allowed        │
│  ❌ 3. Guardrail: amount=5000 > max=500 → BLOCK        │
│  ⚠️  4. Taint: amount=TAINTED → extra check            │
│  ✅ 5. Rate: 2/3 calls this minute                     │
│                                                         │
│  DECISION: ❌ BLOCKED (Guardrail violation)            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Response to Agent:                                     │
│  {                                                      │
│    "blocked": true,                                     │
│    "reason": "Refund amount exceeds $500 limit",       │
│    "max_allowed": 500,                                  │
│    "requested": 5000                                    │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Tech Stack

### Backend (Python)
- **FastAPI** - Agent Gateway API
- **Pydantic** - Schema validation
- **Redis** - Rate limiting (optional)
- **SQLite** - Security event logging

### Frontend (Vue.js)
- **Vue 3** - Reactive UI
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Chart.js** - Security metrics visualization
- **WebSocket** - Real-time updates

---

## 📁 New Project Structure

```
owasp-api10-security-lab/
├── vendor_api/              # Existing
├── consumer_api/            # Existing
├── agent_gateway/           # 🆕 NEW
│   ├── app.py              # Main gateway server
│   ├── controls/
│   │   ├── schema_validator.py
│   │   ├── agent_identity.py
│   │   ├── parameter_guards.py
│   │   ├── taint_tracker.py
│   │   └── rate_limiter.py
│   ├── models/
│   │   ├── request.py
│   │   └── security_event.py
│   └── logs/
│       └── security-events.db
├── client_ui/
│   ├── index.html          # Existing hub
│   ├── agent-dashboard.html # 🆕 NEW Vue.js dashboard
│   └── src/                # 🆕 NEW Vue components
│       ├── components/
│       │   ├── RequestMonitor.vue
│       │   ├── ControlPanel.vue
│       │   ├── SecurityLogs.vue
│       │   └── AgentPlayground.vue
│       ├── App.vue
│       └── main.js
└── README.md
```

---

## 🎯 What Makes This Real

This is NOT a toy simulator. You're building:

✅ **Real API Security Gateway**
- Inspects live requests
- Enforces security rules
- Blocks malicious calls
- Logs all decisions

✅ **Production-Grade Controls**
- Schema validation (like API firewalls)
- Identity enforcement (like service meshes)
- Rate limiting (like cloud WAFs)
- Taint tracking (AI-specific innovation)

✅ **Industry-Standard Architecture**
- Gateway pattern (used by Kong, Envoy, Istio)
- Zero-trust principles
- Defense in depth
- Security event logging

---

## 📈 Coverage Matrix

| Security Area | You Cover |
|--------------|-----------|
| API Security | Schema, validation, rate limits |
| AI Security | Tainted prompt flow, agent identity |
| AppSec | Authorization logic |
| CloudSec | Service-to-service trust |

---

## 🎓 Learning Outcomes

After building this, you can say:

> "I built a security gateway that protects APIs from AI agents making unsafe autonomous calls. It implements schema validation, agent identity enforcement, parameter guardrails, taint tracking, and rate limiting - the same controls used in production API gateways."

**This is a real security system, not a paper project.**

---

## 🚀 Next Steps

1. ✅ Architecture defined (this file)
2. ⏳ Build Agent Gateway (5 controls)
3. ⏳ Create Vue.js dashboard
4. ⏳ Wire Prompt → Agent → Gateway → API
5. ⏳ Add real-time monitoring
6. ⏳ Deploy and demo

---

**Ready to build a real AI security system? Let's go! 🛡️**
