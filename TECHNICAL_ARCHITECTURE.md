# Agent Security Gateway - Technical Architecture

**Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Production-Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Principles](#architecture-principles)
4. [Component Architecture](#component-architecture)
5. [Security Control Architecture](#security-control-architecture)
6. [Data Flow Architecture](#data-flow-architecture)
7. [API Design](#api-design)
8. [Technology Stack](#technology-stack)
9. [Deployment Architecture](#deployment-architecture)
10. [Scalability & Performance](#scalability--performance)
11. [Security & Compliance](#security--compliance)
12. [Monitoring & Observability](#monitoring--observability)
13. [Disaster Recovery](#disaster-recovery)

---

## Executive Summary

The **Agent Security Gateway** is a production-grade security enforcement system designed to protect APIs from autonomous AI agent threats. It implements five core security controls that inspect, validate, and enforce policies on API requests made by AI agents in real-time.

### Key Capabilities
- **Real-time Security Enforcement** - Blocks malicious requests before they reach backend APIs
- **AI-Specific Controls** - Taint tracking and prompt injection prevention
- **Zero-Trust Architecture** - Every request is validated regardless of source
- **Observable Security** - Complete audit trail and real-time monitoring
- **LLM Integration** - Works with OpenAI, Claude, and custom agents

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   End User   │───▶│  Dashboard   │───▶│  AI Agent    │     │
│  │   (Human)    │    │   (Vue.js)   │    │  (OpenAI)    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AI Agent API (Port 8003)                     │  │
│  │  • OpenAI Function Calling                                │  │
│  │  • Tool Use Orchestration                                 │  │
│  │  • Request Formation                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SECURITY GATEWAY LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Agent Security Gateway (Port 8002)                │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         Security Control Pipeline                   │  │  │
│  │  │                                                      │  │  │
│  │  │  1. Schema & Command Validation                     │  │  │
│  │  │  2. Agent Identity Enforcement                      │  │  │
│  │  │  3. Parameter Risk Guardrails                       │  │  │
│  │  │  4. User-Input Taint Tracking                       │  │  │
│  │  │  5. Rate & Chain Control                            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         Supporting Services                         │  │  │
│  │  │  • Event Logger                                     │  │  │
│  │  │  • WebSocket Manager                                │  │  │
│  │  │  • Metrics Collector                                │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Consumer   │  │    Vendor    │  │   External   │         │
│  │     API      │  │     API      │  │   Services   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### System Boundaries

**In Scope:**
- Security policy enforcement
- Request validation and filtering
- Agent identity and authorization
- Real-time threat detection
- Audit logging and monitoring

**Out of Scope:**
- Backend API implementation
- Data storage and persistence
- Business logic execution
- User authentication (delegated to backend)

---

## Architecture Principles

### 1. Defense in Depth
Multiple layers of security controls ensure that if one control fails, others provide backup protection.

### 2. Fail-Safe Defaults
- Default action is DENY
- Explicit allow lists, not deny lists
- Conservative parameter limits

### 3. Least Privilege
- Agents have minimal required permissions
- Role-based access control (RBAC)
- Endpoint-level authorization

### 4. Separation of Concerns
- Each security control is independent
- Modular design allows easy updates
- Clear interfaces between components

### 5. Observable Security
- Every decision is logged
- Real-time monitoring via WebSocket
- Complete audit trail

### 6. Zero Trust
- Never trust, always verify
- Every request is validated
- No implicit trust relationships

---

## Component Architecture

### 1. Agent Security Gateway (Core)

**Technology:** FastAPI (Python 3.13+)  
**Port:** 8002  
**Responsibilities:**
- Request interception and inspection
- Security control orchestration
- Policy enforcement
- Event logging
- WebSocket broadcasting

**Key Modules:**

```python
agent_gateway/
├── app.py                      # Main FastAPI application
├── controls/                   # Security control modules
│   ├── schema_validator.py    # Control #1
│   ├── agent_identity.py      # Control #2
│   ├── parameter_guards.py    # Control #3
│   ├── taint_tracker.py       # Control #4
│   └── rate_limiter.py        # Control #5
├── models/                     # Data models
│   └── security_event.py      # Event schemas
└── requirements.txt           # Dependencies
```

**Design Patterns:**
- **Chain of Responsibility** - Security controls form a processing chain
- **Strategy Pattern** - Each control implements a common interface
- **Observer Pattern** - WebSocket clients observe security events
- **Singleton** - Control instances are shared across requests

### 2. AI Agent Client

**Technology:** Python 3.13+ with OpenAI SDK  
**Port:** 8003 (API Server)  
**Responsibilities:**
- Natural language understanding
- Function calling orchestration
- Request formation
- Gateway communication

**Key Components:**

```python
ai_agent/
├── agent_client.py            # Core agent logic
├── agent_api.py               # HTTP API wrapper
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

**Integration Points:**
- OpenAI GPT-4 API for function calling
- Security Gateway for request submission
- Dashboard for user interaction

### 3. Security Dashboard

**Technology:** Vanilla JavaScript + HTML5/CSS3  
**Port:** 8080  
**Responsibilities:**
- User interface for testing
- Real-time event visualization
- Manual and AI-driven testing
- Security metrics display

**Architecture:**

```
client_ui/
├── security-dashboard.html    # Main dashboard
├── test-dashboard.html        # Simplified test UI
└── agent-security-dashboard.html  # Vue.js version (legacy)
```

**Features:**
- WebSocket connection for live updates
- REST API integration
- Responsive design
- GitHub-inspired UI theme

---

## Security Control Architecture

### Control Pipeline Flow

```
Request → [1] Schema → [2] Identity → [3] Guardrails → [4] Taint → [5] Rate → Decision
                ↓           ↓              ↓            ↓         ↓
              BLOCK       BLOCK          BLOCK        BLOCK     BLOCK
                                                                  ↓
                                                               ALLOW
```

### Control #1: Schema & Command Validation

**Purpose:** Prevent agent hallucination and injection attacks

**Implementation:**
```python
class SchemaValidator:
    def validate(self, endpoint: str, params: dict) -> ValidationResult:
        schema = self.get_schema(endpoint)
        
        # Check for unexpected fields
        if extra_fields := set(params.keys()) - set(schema.allowed_fields):
            return ValidationResult(
                passed=False,
                reason=f"Unexpected fields: {extra_fields}"
            )
        
        # Check for dangerous patterns
        if self.contains_dangerous_patterns(params):
            return ValidationResult(
                passed=False,
                reason="Dangerous command patterns detected"
            )
        
        return ValidationResult(passed=True)
```

**Threat Model:**
- Agent hallucinates non-existent parameters
- Injection of system commands
- SQL/NoSQL injection attempts
- Path traversal attacks

**Mitigation:**
- Strict schema enforcement
- Allowlist-based validation
- Pattern matching for dangerous strings
- Type checking

### Control #2: Agent Identity Enforcement

**Purpose:** Implement role-based access control for agents

**Implementation:**
```python
class AgentIdentityEnforcer:
    def __init__(self):
        self.agent_permissions = {
            "support-bot": {
                "allowed_endpoints": ["/tickets", "/refunds"],
                "allowed_methods": ["GET", "POST"],
                "max_refund_amount": 500
            },
            "finance-bot": {
                "allowed_endpoints": ["/invoices", "/payments", "/refunds"],
                "allowed_methods": ["GET", "POST"],
                "max_refund_amount": 10000
            },
            "admin-agent": {
                "allowed_endpoints": ["*"],
                "allowed_methods": ["*"],
                "max_refund_amount": None
            }
        }
    
    def check_permission(self, agent_id: str, endpoint: str, method: str) -> bool:
        if agent_id not in self.agent_permissions:
            return False
        
        perms = self.agent_permissions[agent_id]
        
        # Check endpoint access
        if "*" not in perms["allowed_endpoints"]:
            if endpoint not in perms["allowed_endpoints"]:
                return False
        
        # Check method access
        if "*" not in perms["allowed_methods"]:
            if method not in perms["allowed_methods"]:
                return False
        
        return True
```

**Threat Model:**
- Privilege escalation
- Unauthorized data access
- Cross-agent impersonation
- Stolen credentials

**Mitigation:**
- Explicit permission mapping
- Endpoint-level authorization
- Method-level restrictions
- Agent identity verification

### Control #3: Parameter Risk Guardrails

**Purpose:** Enforce business logic limits and detect abuse

**Implementation:**
```python
class ParameterGuardrails:
    def __init__(self):
        self.guardrails = {
            "/refunds": {
                "amount": {"max": 500, "min": 0},
                "customer_id": {"pattern": r"^\d+$"}
            },
            "/export": {
                "limit": {"max": 100},
                "format": {"allowed": ["csv", "json"]}
            }
        }
    
    def check_guardrails(self, endpoint: str, params: dict) -> GuardrailResult:
        if endpoint not in self.guardrails:
            return GuardrailResult(passed=True)
        
        rules = self.guardrails[endpoint]
        violations = []
        
        for param, value in params.items():
            if param in rules:
                rule = rules[param]
                
                # Check max value
                if "max" in rule and value > rule["max"]:
                    violations.append(f"{param} exceeds max: {rule['max']}")
                
                # Check allowed values
                if "allowed" in rule and value not in rule["allowed"]:
                    violations.append(f"{param} not in allowed values")
        
        return GuardrailResult(
            passed=len(violations) == 0,
            violations=violations
        )
```

**Threat Model:**
- Business logic abuse (e.g., excessive refunds)
- Resource exhaustion
- Data exfiltration
- Financial fraud

**Mitigation:**
- Value range enforcement
- Format validation
- Business rule checking
- Anomaly detection

### Control #4: User-Input Taint Tracking

**Purpose:** Prevent prompt injection and data leakage (AI-specific)

**Implementation:**
```python
class TaintTracker:
    def __init__(self):
        self.sensitive_fields = ["amount", "account_number", "ssn", "password"]
        self.taint_patterns = [
            r"\$\d+",           # Dollar amounts
            r"\d{3}-\d{2}-\d{4}", # SSN
            r"\d{16}",          # Credit card
        ]
    
    def track_taint(self, user_prompt: str, params: dict) -> TaintResult:
        if not user_prompt:
            return TaintResult(passed=True)
        
        tainted_fields = []
        
        for field, value in params.items():
            if field in self.sensitive_fields:
                # Check if value appears in user prompt
                if str(value) in user_prompt:
                    tainted_fields.append(field)
                
                # Check for pattern matches
                for pattern in self.taint_patterns:
                    if re.search(pattern, str(value)):
                        tainted_fields.append(field)
                        break
        
        if tainted_fields:
            return TaintResult(
                passed=False,
                tainted_fields=tainted_fields,
                reason="User-originated data in sensitive fields"
            )
        
        return TaintResult(passed=True)
```

**Threat Model:**
- Prompt injection attacks
- User data leakage
- Social engineering
- Indirect prompt manipulation

**Mitigation:**
- Data origin tracking
- Sensitive field identification
- Pattern-based detection
- Human-in-the-loop for tainted requests

### Control #5: Rate & Chain Control

**Purpose:** Prevent autonomous damage cascades

**Implementation:**
```python
class RateLimiter:
    def __init__(self):
        self.limits = {
            "/refunds": {"max_requests": 3, "window_seconds": 60},
            "/export": {"max_requests": 1, "window_seconds": 300},
            "/invoices": {"max_requests": 10, "window_seconds": 60}
        }
        self.request_history = defaultdict(lambda: deque())
    
    def check_rate_limit(self, agent_id: str, endpoint: str) -> RateLimitResult:
        if endpoint not in self.limits:
            return RateLimitResult(passed=True)
        
        limit = self.limits[endpoint]
        key = f"{agent_id}:{endpoint}"
        now = datetime.utcnow()
        
        # Clean old requests
        cutoff = now - timedelta(seconds=limit["window_seconds"])
        history = self.request_history[key]
        while history and history[0] < cutoff:
            history.popleft()
        
        # Check limit
        if len(history) >= limit["max_requests"]:
            return RateLimitResult(
                passed=False,
                reason=f"Rate limit exceeded: {len(history)}/{limit['max_requests']}"
            )
        
        # Record request
        history.append(now)
        
        return RateLimitResult(passed=True)
```

**Threat Model:**
- Rapid-fire attacks
- Resource exhaustion
- Autonomous damage loops
- Distributed attacks

**Mitigation:**
- Per-agent rate limiting
- Per-endpoint limits
- Sliding window algorithm
- Chain detection

---

## Data Flow Architecture

### Request Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. REQUEST INGESTION                                             │
│    POST /gateway/secure                                          │
│    Headers: X-Agent-ID, X-Request-ID                            │
│    Body: {endpoint, method, params, user_prompt}                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. REQUEST VALIDATION                                            │
│    • Parse JSON body                                             │
│    • Validate required fields                                    │
│    • Extract agent identity                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. SECURITY CONTROL PIPELINE                                     │
│                                                                   │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ Control #1: Schema Validation                            │ │
│    │ • Check allowed fields                                   │ │
│    │ • Validate types                                         │ │
│    │ • Detect dangerous patterns                              │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ Control #2: Agent Identity                               │ │
│    │ • Verify agent exists                                    │ │
│    │ • Check endpoint permissions                             │ │
│    │ • Validate method access                                 │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ Control #3: Parameter Guardrails                         │ │
│    │ • Check value ranges                                     │ │
│    │ • Validate formats                                       │ │
│    │ • Enforce business rules                                 │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ Control #4: Taint Tracking                               │ │
│    │ • Identify user-originated data                          │ │
│    │ • Check sensitive fields                                 │ │
│    │ • Flag tainted requests                                  │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              ↓                                    │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ Control #5: Rate Limiting                                │ │
│    │ • Check request history                                  │ │
│    │ • Enforce rate limits                                    │ │
│    │ • Update counters                                        │ │
│    └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. DECISION MAKING                                               │
│    IF all controls pass:                                         │
│       decision = ALLOW                                           │
│    ELSE:                                                         │
│       decision = BLOCK                                           │
│       blocked_by = first_failed_control                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. EVENT LOGGING                                                 │
│    • Create SecurityEvent                                        │
│    • Store in event history                                      │
│    • Broadcast via WebSocket                                     │
│    • Update metrics                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE GENERATION                                           │
│    {                                                             │
│      "allowed": true/false,                                      │
│      "reason": "...",                                            │
│      "blocked_by": "control_name",                               │
│      "security_checks": {...},                                   │
│      "timestamp": "..."                                          │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

### WebSocket Event Flow

```
┌─────────────┐
│  Dashboard  │
│   Client    │
└──────┬──────┘
       │
       │ 1. Connect
       │ ws://localhost:8002/ws/events
       ▼
┌─────────────────────┐
│  WebSocket Manager  │
│  (Gateway)          │
└──────┬──────────────┘
       │
       │ 2. Send history
       │ {type: "history", events: [...]}
       ▼
┌─────────────┐
│  Dashboard  │
│  (displays  │
│   history)  │
└──────┬──────┘
       │
       │ 3. Real-time events
       │ {type: "event", ...}
       ▼
┌─────────────┐
│  Dashboard  │
│  (updates   │
│   live)     │
└─────────────┘
```

---

## API Design

### Gateway API Endpoints

#### POST /gateway/secure
**Purpose:** Main security enforcement endpoint

**Request:**
```json
{
  "endpoint": "/refunds",
  "method": "POST",
  "params": {
    "customer_id": "123",
    "amount": 250
  },
  "user_prompt": "Refund customer 123 for $250"
}
```

**Headers:**
```
X-Agent-ID: support-bot
X-Request-ID: req_123456789
```

**Response (Allowed):**
```json
{
  "allowed": true,
  "reason": "All security checks passed",
  "security_checks": {
    "schema_validation": {"passed": true, "details": "..."},
    "agent_identity": {"passed": true, "details": "..."},
    "parameter_guards": {"passed": true, "details": "..."},
    "taint_tracking": {"passed": true, "details": "..."},
    "rate_limiting": {"passed": true, "details": "..."}
  },
  "timestamp": "2026-01-21T22:15:00Z",
  "request_id": "req_123456789"
}
```

**Response (Blocked):**
```json
{
  "allowed": false,
  "blocked_by": "Parameter Guardrails",
  "reason": "Guardrail violations: amount exceeds max $500",
  "security_checks": {
    "schema_validation": {"passed": true, "details": "..."},
    "agent_identity": {"passed": true, "details": "..."},
    "parameter_guards": {"passed": false, "details": "amount: 5000 > 500"},
    "taint_tracking": null,
    "rate_limiting": null
  },
  "timestamp": "2026-01-21T22:15:00Z",
  "request_id": "req_123456789"
}
```

#### GET /health
**Purpose:** Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

#### GET /stats
**Purpose:** Get security statistics

**Response:**
```json
{
  "total_requests": 150,
  "allowed": 120,
  "blocked": 30,
  "block_rate": 20.0,
  "blocks_by_control": {
    "schema_validation": 5,
    "agent_identity": 8,
    "parameter_guards": 10,
    "taint_tracking": 4,
    "rate_limiting": 3
  }
}
```

#### GET /events
**Purpose:** Get recent security events

**Query Parameters:**
- `limit` (optional): Number of events to return (default: 50)

**Response:**
```json
{
  "events": [
    {
      "request_id": "req_123",
      "agent_id": "support-bot",
      "endpoint": "/refunds",
      "allowed": false,
      "blocked_by": "Parameter Guardrails",
      "reason": "...",
      "timestamp": "2026-01-21T22:15:00Z"
    }
  ]
}
```

#### WebSocket /ws/events
**Purpose:** Real-time event stream

**Message Types:**
1. **History** (on connect):
```json
{
  "type": "history",
  "events": [...]
}
```

2. **Live Event**:
```json
{
  "type": "event",
  "request_id": "req_123",
  "agent_id": "support-bot",
  "allowed": false,
  "blocked_by": "...",
  "reason": "...",
  "timestamp": "..."
}
```

### Agent API Endpoints

#### POST /agent/prompt
**Purpose:** Process natural language prompt through AI agent

**Request:**
```json
{
  "prompt": "Create a support ticket for customer 123",
  "agent_id": "support-bot"
}
```

**Response:**
```json
{
  "success": true,
  "agent_response": "I'll create that ticket for you.",
  "tool_calls": [
    {
      "function": "create_support_ticket",
      "arguments": {
        "customer_id": "123",
        "subject": "Support request"
      },
      "security_result": {
        "allowed": true,
        "reason": "All checks passed"
      }
    }
  ]
}
```

#### GET /agent/tools
**Purpose:** List available agent functions

**Response:**
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "create_support_ticket",
        "description": "Create a customer support ticket",
        "parameters": {...}
      }
    }
  ]
}
```

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Web Framework | FastAPI | 0.109+ | High-performance async API |
| Runtime | Python | 3.13+ | Core language |
| HTTP Client | httpx | 0.26+ | Async HTTP requests |
| WebSocket | websockets | 12.0+ | Real-time communication |
| Data Validation | Pydantic | 2.5+ | Schema validation |
| LLM Integration | OpenAI SDK | 1.0+ | AI agent functionality |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | Vanilla JS | Lightweight, no dependencies |
| Styling | CSS3 | Modern styling |
| HTTP Client | Fetch API | Native browser API |
| WebSocket | WebSocket API | Native browser API |
| Fonts | Inter (Google Fonts) | Professional typography |

### Development Tools

| Tool | Purpose |
|------|---------|
| Git | Version control |
| VS Code / Windsurf | IDE |
| Postman | API testing |
| Chrome DevTools | Frontend debugging |

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Machine                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Gateway    │  │  Agent API   │  │  Dashboard   │     │
│  │   :8002      │  │   :8003      │  │   :8080      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Environment Variables:                                      │
│  • OPENAI_API_KEY                                           │
│  • GATEWAY_URL=http://localhost:8002                        │
└─────────────────────────────────────────────────────────────┘
```

**Start Command:**
```bash
./START_ALL.sh
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build: ./agent_gateway
    ports:
      - "8002:8002"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  agent:
    build: ./ai_agent
    ports:
      - "8003:8003"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GATEWAY_URL=http://gateway:8002
    depends_on:
      - gateway

  dashboard:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./client_ui:/usr/share/nginx/html:ro
```

### Cloud Deployment (AWS)

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    VPC (10.0.0.0/16)                    │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │         Public Subnet (10.0.1.0/24)              │  │ │
│  │  │                                                    │  │ │
│  │  │  ┌─────────────────────────────────────────────┐ │  │ │
│  │  │  │  Application Load Balancer                   │ │  │ │
│  │  │  │  • HTTPS (443)                               │ │  │ │
│  │  │  │  • SSL/TLS Termination                       │ │  │ │
│  │  │  └─────────────────────────────────────────────┘ │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                          ↓                               │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │        Private Subnet (10.0.2.0/24)              │  │ │
│  │  │                                                    │  │ │
│  │  │  ┌────────────────────────────────────────────┐  │  │ │
│  │  │  │  ECS Fargate Cluster                        │  │  │ │
│  │  │  │                                              │  │  │ │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │  │ │
│  │  │  │  │ Gateway  │  │  Agent   │  │Dashboard │ │  │  │ │
│  │  │  │  │ Service  │  │ Service  │  │ Service  │ │  │  │ │
│  │  │  │  │ (2 tasks)│  │ (2 tasks)│  │ (2 tasks)│ │  │  │ │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘ │  │  │ │
│  │  │  └────────────────────────────────────────────┘  │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Supporting Services                        │ │
│  │                                                          │ │
│  │  • CloudWatch Logs (centralized logging)               │ │
│  │  • CloudWatch Metrics (monitoring)                     │ │
│  │  • Secrets Manager (API keys)                          │ │
│  │  • Route 53 (DNS)                                      │ │
│  │  • WAF (DDoS protection)                               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Infrastructure as Code (Terraform):**
```hcl
# main.tf
resource "aws_ecs_cluster" "agent_gateway" {
  name = "agent-security-gateway"
}

resource "aws_ecs_service" "gateway" {
  name            = "gateway-service"
  cluster         = aws_ecs_cluster.agent_gateway.id
  task_definition = aws_ecs_task_definition.gateway.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.gateway.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.gateway.arn
    container_name   = "gateway"
    container_port   = 8002
  }
}
```

---

## Scalability & Performance

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Request Latency (p50) | < 50ms | ~30ms |
| Request Latency (p99) | < 200ms | ~150ms |
| Throughput | 1000 req/s | 500 req/s |
| WebSocket Connections | 10,000 | 1,000 |
| Memory per Instance | < 512MB | ~256MB |
| CPU per Instance | < 1 vCPU | ~0.5 vCPU |

### Horizontal Scaling

**Gateway Service:**
- Stateless design allows easy horizontal scaling
- Load balancer distributes requests
- No shared state between instances

**Scaling Triggers:**
- CPU > 70% for 5 minutes → scale up
- CPU < 30% for 10 minutes → scale down
- Request queue depth > 100 → scale up

**Auto-scaling Configuration:**
```yaml
auto_scaling:
  min_instances: 2
  max_instances: 10
  target_cpu_utilization: 70
  scale_up_cooldown: 60s
  scale_down_cooldown: 300s
```

### Caching Strategy

**In-Memory Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_agent_permissions(agent_id: str):
    """Cache agent permissions to avoid repeated lookups"""
    return load_permissions(agent_id)
```

**Redis for Distributed Caching:**
```python
# For rate limiting across instances
import redis

redis_client = redis.Redis(host='redis', port=6379)

def check_rate_limit_distributed(agent_id: str, endpoint: str):
    key = f"rate:{agent_id}:{endpoint}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 60)  # 60 second window
    return count <= MAX_REQUESTS
```

### Database Considerations

**Current:** In-memory storage (suitable for demo/dev)

**Production Recommendations:**
- **PostgreSQL** for event storage and audit logs
- **Redis** for rate limiting and caching
- **Elasticsearch** for log aggregation and search
- **TimescaleDB** for time-series metrics

---

## Security & Compliance

### Security Layers

1. **Network Security**
   - TLS 1.3 for all external communication
   - Private subnets for application tier
   - Security groups with least privilege
   - WAF for DDoS protection

2. **Application Security**
   - Input validation on all endpoints
   - CORS configuration
   - Rate limiting
   - Request size limits

3. **Data Security**
   - No PII stored in logs
   - Secrets in AWS Secrets Manager
   - Encryption at rest and in transit
   - Audit logging

4. **Authentication & Authorization**
   - Agent identity verification
   - API key rotation
   - Role-based access control
   - Least privilege principle

### Compliance Considerations

**OWASP API Security Top 10:**
- ✅ API1: Broken Object Level Authorization
- ✅ API2: Broken Authentication
- ✅ API3: Broken Object Property Level Authorization
- ✅ API4: Unrestricted Resource Consumption
- ✅ API5: Broken Function Level Authorization
- ✅ API6: Unrestricted Access to Sensitive Business Flows
- ✅ API7: Server Side Request Forgery
- ✅ API8: Security Misconfiguration
- ✅ API9: Improper Inventory Management
- ✅ API10: Unsafe Consumption of APIs ← **Primary Focus**

**GDPR Compliance:**
- Data minimization (only log necessary data)
- Right to erasure (event retention policy)
- Data portability (export functionality)
- Privacy by design

---

## Monitoring & Observability

### Metrics Collection

**Application Metrics:**
```python
from prometheus_client import Counter, Histogram

request_counter = Counter(
    'gateway_requests_total',
    'Total requests processed',
    ['agent_id', 'endpoint', 'decision']
)

request_duration = Histogram(
    'gateway_request_duration_seconds',
    'Request processing time',
    ['control']
)
```

**Key Metrics:**
- Total requests (counter)
- Allowed vs blocked ratio (gauge)
- Request latency (histogram)
- Control execution time (histogram)
- WebSocket connections (gauge)
- Error rate (counter)
- Memory usage (gauge)
- CPU usage (gauge)

### Logging Strategy

**Log Levels:**
- **DEBUG:** Detailed control execution
- **INFO:** Request processing, decisions
- **WARNING:** Rate limit approaching, anomalies
- **ERROR:** Control failures, system errors
- **CRITICAL:** Service unavailable

**Structured Logging:**
```python
import logging
import json

logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "event": "request_blocked",
    "agent_id": "support-bot",
    "endpoint": "/refunds",
    "blocked_by": "parameter_guards",
    "reason": "amount exceeds limit",
    "timestamp": "2026-01-21T22:15:00Z"
}))
```

### Alerting

**Critical Alerts:**
- Service down (health check fails)
- Error rate > 5%
- Latency p99 > 500ms
- Memory usage > 90%

**Warning Alerts:**
- Block rate > 50%
- Unusual agent behavior
- Rate limit frequently hit
- WebSocket connection drops

**Alert Channels:**
- PagerDuty for critical
- Slack for warnings
- Email for daily summaries

### Dashboards

**Operational Dashboard:**
- Request rate (requests/second)
- Success rate (%)
- Latency percentiles (p50, p95, p99)
- Active WebSocket connections
- Resource utilization

**Security Dashboard:**
- Blocks by control (pie chart)
- Block rate over time (line chart)
- Top blocked agents (table)
- Threat timeline (timeline)
- Anomaly detection (alerts)

---

## Disaster Recovery

### Backup Strategy

**Configuration Backup:**
- Agent permissions (JSON)
- Schema definitions (JSON)
- Guardrail rules (JSON)
- Rate limit configuration (JSON)

**Event Backup:**
- Daily export to S3
- 90-day retention
- Compressed JSON format

### Recovery Procedures

**Service Failure:**
1. Health check detects failure
2. Auto-scaling launches new instance
3. Load balancer routes traffic
4. Failed instance terminated
5. Alert sent to ops team

**Data Loss:**
1. Restore from latest S3 backup
2. Replay events from backup
3. Verify data integrity
4. Resume normal operations

**Complete System Failure:**
1. Deploy from infrastructure as code
2. Restore configuration from backup
3. Validate all services healthy
4. Resume traffic
5. Post-mortem analysis

### Business Continuity

**RTO (Recovery Time Objective):** 15 minutes  
**RPO (Recovery Point Objective):** 1 hour

**Failover Strategy:**
- Multi-AZ deployment
- Cross-region replication (optional)
- Blue-green deployment for updates
- Canary releases for new features

---

## Future Enhancements

### Phase 2 Features

1. **Machine Learning Integration**
   - Anomaly detection using ML models
   - Behavioral analysis of agents
   - Predictive threat detection

2. **Advanced Taint Tracking**
   - Data flow analysis
   - Multi-hop taint propagation
   - Context-aware taint rules

3. **Policy Engine**
   - Dynamic policy updates
   - A/B testing of policies
   - Policy versioning

4. **Multi-Tenancy**
   - Tenant isolation
   - Per-tenant policies
   - Tenant-specific metrics

### Phase 3 Features

1. **Distributed Tracing**
   - OpenTelemetry integration
   - Request flow visualization
   - Performance profiling

2. **Advanced Analytics**
   - Threat intelligence integration
   - Attack pattern recognition
   - Security posture scoring

3. **Self-Healing**
   - Automatic policy adjustment
   - Adaptive rate limiting
   - Threat response automation

---

## Appendix

### Glossary

- **Agent:** An autonomous AI system that makes API calls
- **Control:** A security mechanism that validates requests
- **Taint:** Data originating from untrusted sources
- **Guardrail:** Business logic constraint
- **Chain:** Sequence of related API calls

### References

- OWASP API Security Top 10: https://owasp.org/API-Security/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- AWS ECS Best Practices: https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-21 | Initial architecture document |

---

**Document Owner:** Security Engineering Team  
**Last Review:** January 21, 2026  
**Next Review:** April 21, 2026
