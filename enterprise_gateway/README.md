# Enterprise Agent Security Gateway

**Production-grade security enforcement system for AI agents**

Built following enterprise security best practices with real-time policy enforcement, human-in-the-loop approvals, and comprehensive audit logging.

---

## 🎯 Overview

This system implements **8 phases of enterprise-grade agent security**:

1. ✅ **Credible Use Cases** - Support, Refund, and Admin agents with bounded permissions
2. ✅ **Governance Policies** - Allowlists, RBAC, execution guards, data classification
3. ✅ **Enforcement Gateway** - 10-layer security pipeline intercepting all agent actions
4. ✅ **Real-Time Validation** - Taint tracking, schema validation, HITL approvals
5. ✅ **Complete Observability** - Audit logs, replay capability, risk scoring
6. ✅ **Multi-Agent Security** - Secure inter-agent communication and isolation
7. ✅ **Live Policy UX** - Real-time dashboard showing security decisions
8. ✅ **Production Ready** - Testing, hardening, demo scenarios

---

## 🏗️ Architecture

```
User Prompt
    ↓
AI Agent (OpenAI/Ollama)
    ↓
Security Gateway (10 Layers)
    ├─ 1. Agent Identity Verification
    ├─ 2. Tool Allowlist Check
    ├─ 3. Policy Authorization
    ├─ 4. Rate Limiting
    ├─ 5. Parameter Validation
    ├─ 6. Prompt Injection Detection
    ├─ 7. Taint Tracking
    ├─ 8. Business Logic Guards
    ├─ 9. Approval Requirements
    └─ 10. Sequence Analysis
    ↓
✅ ALLOW → Execute Tool → Audit Log
❌ DENY → Block → Audit Log
⏸️ APPROVAL → Human Review → Execute/Block
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd enterprise_gateway
pip install -r requirements.txt
```

### 2. Start the Gateway

```bash
python main.py
```

Gateway runs on **http://localhost:8004**

### 3. Start the Agent API

```bash
cd agents
python agent_api.py
```

Agent API runs on **http://localhost:8005**

### 4. Open the Dashboard

```bash
cd ../dashboard
python -m http.server 8006
```

Dashboard: **http://localhost:8006/enterprise_dashboard.html**

---

## 🎭 Demo Scenarios

The system includes 8 pre-built demo scenarios:

### ✅ Allowed Actions
- **Support Agent** creates ticket → Passes all checks
- **Refund Agent** issues small refund ($25) → Auto-approved

### ⏸️ Requires Approval
- **Refund Agent** issues large refund ($500) → Needs human approval
- **Admin Agent** restarts dev service → Requires approval

### ❌ Blocked Actions
- **Support Agent** tries to issue refund → Not in allowlist
- **Admin Agent** tries to restart prod → Forbidden environment
- **Hacker Bot** tries anything → No permissions
- **Prompt Injection** detected → Blocked by guard

---

## 📊 Key Features

### Security Controls

**10-Layer Enforcement Pipeline:**
1. Agent identity verification (RBAC)
2. Tool allowlist enforcement
3. Policy-based authorization
4. Rate limiting (per-agent, per-tool)
5. Parameter validation & constraints
6. Prompt injection detection
7. Taint tracking (user input → sensitive params)
8. Business logic guards (amount thresholds, environment isolation)
9. Conditional approval requirements
10. Action sequence anomaly detection

### Observability

- **Complete Audit Trail** - Every action logged with context
- **Risk Scoring** - Each event scored (low/medium/high/critical)
- **Real-Time Monitoring** - WebSocket stream of security events
- **Timeline View** - Visual representation of agent behavior
- **Replay Capability** - Export/replay sessions for demos

### Human-in-the-Loop

- **Approval Workflow** - High-risk actions pause for human review
- **Approval Dashboard** - Pending actions with context
- **Approve/Deny** - Human makes final decision
- **Audit Trail** - Who approved what and when

---

## 🔧 Configuration

### Agent Roles

Defined in `config/agent_definitions.py`:

- **support-agent** - Customer support (tickets, knowledge base)
- **refund-agent** - Billing operations (refunds up to $500)
- **admin-agent** - DevOps (diagnostics, service restarts in non-prod)
- **hacker-bot** - Test agent with no permissions

### Governance Policies

Defined in `config/governance_policies.py`:

- **Tool Policies** - Which agents can use which tools
- **Execution Guards** - Runtime checks (taint, rate, thresholds)
- **Approval Thresholds** - When human approval is required
- **Data Classification** - PII protection rules

### Tools

Defined in `config/agent_definitions.py`:

- `search_knowledge_base` - Search support articles
- `create_support_ticket` - Create customer ticket
- `lookup_order` - Get order details
- `issue_refund` - Process refund (high-risk)
- `get_system_health` - Check service health
- `restart_service` - Restart service (requires approval)
- `export_customer_data` - Export data (critical risk)

---

## 🧪 Testing

### Run Demo Scenarios

```bash
# Via API
curl -X POST http://localhost:8004/demo/run-scenario/support_normal

# Via Dashboard
# Click "Demo Scenarios" → Select scenario → "Run"
```

### Test with AI Agent

```bash
# Using Ollama (local, free)
curl -X POST http://localhost:8005/agent/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a support ticket for customer 12345",
    "agent_id": "support-agent",
    "provider": "ollama"
  }'

# Using OpenAI (requires API key)
export OPENAI_API_KEY="sk-..."
curl -X POST http://localhost:8005/agent/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Process a refund of $250 for order 12345",
    "agent_id": "refund-agent",
    "provider": "openai"
  }'
```

---

## 📡 API Endpoints

### Gateway (Port 8004)

- `POST /gateway/execute` - Execute tool through security gateway
- `POST /gateway/approve` - Approve/deny pending action
- `GET /gateway/pending-approvals` - Get pending approvals
- `GET /stats` - System statistics
- `GET /events/recent` - Recent security events
- `GET /events/timeline` - Visual timeline
- `GET /config/agents` - Agent definitions
- `GET /config/tools` - Available tools
- `GET /demo/scenarios` - Demo scenarios
- `WS /ws/events` - Real-time event stream

### Agent API (Port 8005)

- `POST /agent/prompt` - Process prompt through AI agent
- `GET /agents/available` - List available agents
- `GET /health` - Health check

---

## 🛡️ Security Highlights

### Zero-Trust Architecture
- Every request validated, no implicit trust
- Agent identity verified on every call
- Tool allowlists enforced server-side

### Defense in Depth
- 10 layers of security checks
- Multiple controls for each threat vector
- Fail-safe defaults (deny by default)

### Least Privilege
- Agents have minimal required permissions
- Role-based access control (RBAC)
- Endpoint and method-level restrictions

### Observable Security
- Complete audit trail
- Real-time monitoring
- Risk scoring and alerting

### Prompt Injection Protection
- Pattern-based detection
- Taint tracking for user input
- Inter-agent message sanitization

---

## 📈 Monitoring & Metrics

### Statistics Tracked

- Total requests (allowed/denied/approval required)
- Per-agent statistics
- Per-tool statistics
- Risk level distribution
- Block rate and reasons

### Event Types

- `tool_call_allowed` - Action executed
- `tool_call_denied` - Action blocked
- `approval_required` - Needs human review
- `approval_granted` - Human approved
- `approval_denied` - Human denied
- `prompt_injection_detected` - Attack blocked
- `rate_limit_exceeded` - Too many requests
- `taint_detected` - User input in sensitive param
- `anomaly_detected` - Unusual behavior

---

## 🎬 Demo Script

**Perfect for investor/enterprise presentations:**

1. **Show Normal Operation**
   - Support agent creates ticket → ✅ Allowed
   - Dashboard shows green checkmark, logs event

2. **Show Security Blocking**
   - Support agent tries refund → ❌ Blocked
   - Dashboard shows red X, "Not in allowlist"

3. **Show Approval Workflow**
   - Refund agent tries $500 refund → ⏸️ Pending
   - Dashboard shows approval request
   - Human clicks "Approve" → ✅ Executes

4. **Show Attack Prevention**
   - Prompt injection attempt → ❌ Blocked
   - Dashboard shows "Prompt injection detected"

5. **Show Audit Trail**
   - Timeline view shows all events
   - Export session for compliance

---

## 🔐 Compliance & Standards

Aligned with:
- **OWASP API Security Top 10** (especially #10: Unsafe Consumption of APIs)
- **Zero Trust Architecture** principles
- **Least Privilege** access control
- **Defense in Depth** security model
- **GDPR** data protection (PII masking, audit trails)

---

## 🚧 Production Deployment

### Environment Variables

```bash
export OPENAI_API_KEY="sk-..."  # Optional, for OpenAI agents
export GATEWAY_URL="http://gateway:8004"
export LOG_LEVEL="INFO"
```

### Docker Deployment

```bash
docker-compose up -d
```

### Scaling

- Gateway is stateless (horizontal scaling)
- Use Redis for distributed rate limiting
- PostgreSQL for persistent audit logs
- Load balancer for multiple instances

---

## 📚 Documentation

- `TECHNICAL_ARCHITECTURE.md` - Complete technical architecture
- `config/` - All configuration and policies
- `core/` - Enforcement engine and audit logger
- `agents/` - Multi-agent system
- `backend/` - Mock APIs for demo
- `dashboard/` - Web UI

---

## 🎯 Key Differentiators

1. **Real-Time Enforcement** - Not simulation, actual blocking
2. **Multi-Layer Security** - 10 independent checks
3. **Human-in-the-Loop** - Approval workflow for high-risk actions
4. **Complete Observability** - Every decision logged and explainable
5. **Multi-Agent Support** - Secure agent collaboration
6. **Production-Ready** - Enterprise-grade architecture
7. **LLM-Agnostic** - Works with OpenAI, Ollama, or any LLM
8. **Zero-Trust** - Never trust, always verify

---

## 📞 Support

For questions or issues:
- Check the dashboard logs
- Review audit trail
- Examine enforcement decisions
- Test with demo scenarios

---

**Built with enterprise security best practices. Ready for production deployment.**
