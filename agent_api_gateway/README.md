# Agent-to-API Security Gateway

**Real-time bidirectional validation for AI agents calling third-party APIs**

---

## 🎯 **Problem Statement**

**Scenario:** You have an AI agent (like a Canva AI design tool) that calls third-party APIs:
- Unsplash (stock photos)
- DALL-E (image generation)
- Remove.bg (background removal)
- Cloudinary (image processing)
- Google Fonts (typography)

**Risks:**
1. **Outgoing:** Agent could be tricked into calling malicious APIs or leaking data
2. **Incoming:** Third-party API could be compromised and return malicious content
3. **No visibility:** No audit trail of what APIs are being called
4. **No control:** Can't block or sanitize dangerous responses

---

## 🛡️ **Solution: Security Gateway**

A **real-time proxy** that sits between your AI agent and third-party APIs:

```
AI Agent → Security Gateway → Third-Party API
                ↓
         Validates both:
         1. Outgoing request
         2. Incoming response
```

---

## 🏗️ **Architecture**

```
┌──────────────────────────────────────┐
│  AI Design Agent (Open-Source)       │
│  - Generate images                   │
│  - Search photos                     │
│  - Remove backgrounds                │
│  - Apply filters                     │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│  🛡️ Security Gateway (Port 7000)     │
│                                       │
│  REQUEST VALIDATION:                 │
│  ✓ API allowlist check               │
│  ✓ Endpoint validation               │
│  ✓ SQL injection detection           │
│  ✓ Command injection detection       │
│  ✓ API key leak detection            │
│                                       │
│  RESPONSE VALIDATION:                │
│  ✓ XSS detection                     │
│  ✓ Malicious redirect detection      │
│  ✓ PII exposure detection            │
│  ✓ Schema validation                 │
│  ✓ Data sanitization                 │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│  Third-Party APIs                     │
│  - Unsplash                           │
│  - OpenAI DALL-E                      │
│  - Remove.bg                          │
│  - Cloudinary                         │
│  - Google Fonts                       │
└──────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **1. Start the Gateway**

```bash
cd agent_api_gateway
python3 gateway_api.py
```

Gateway runs on **http://localhost:7000**

### **2. Run the AI Agent Demo**

```bash
python3 ai_design_agent.py
```

This will:
- Search Unsplash for photos ✅
- Generate images with DALL-E ✅
- Get font suggestions ✅
- Test security (SQL injection, malicious APIs) ❌ (blocked)

---

## 🎨 **Canva-like AI Agent Example**

```python
from ai_design_agent import AIDesignAgent

# Initialize agent
agent = AIDesignAgent(agent_id="design-agent-001")

# 1. Search for stock photos
result = agent.search_stock_photos("mountain landscape")
# Gateway validates: ✓ Unsplash is trusted
#                    ✓ No injection in query
#                    ✓ Response is safe

# 2. Generate AI image
result = agent.generate_ai_image("futuristic city")
# Gateway validates: ✓ OpenAI is trusted
#                    ✓ Prompt is safe
#                    ✓ Response contains no XSS

# 3. Remove background
result = agent.remove_background("https://example.com/photo.jpg")
# Gateway validates: ✓ Remove.bg is trusted
#                    ✓ URL is safe (not localhost/internal)
#                    ✓ Response is sanitized
```

---

## 🔒 **Security Features**

### **Request Validation (Outgoing)**

1. **API Allowlist**
   ```python
   # Only these APIs are allowed
   trusted_apis = {
       "unsplash.com": {...},
       "api.openai.com": {...},
       "api.remove.bg": {...},
       "api.cloudinary.com": {...},
       "fonts.googleapis.com": {...}
   }
   ```

2. **Endpoint Validation**
   ```python
   # Only specific endpoints allowed per API
   "unsplash.com": {
       "allowed_endpoints": ["/photos", "/search/photos"]
   }
   ```

3. **Injection Detection**
   - SQL injection: `' OR '1'='1`
   - Command injection: `; rm -rf /`
   - Path traversal: `../../etc/passwd`

4. **API Key Leak Detection**
   - Detects API keys in parameters
   - Prevents accidental exposure

### **Response Validation (Incoming)**

1. **XSS Detection**
   ```python
   # Detects malicious scripts in response
   <script>stealCookies()</script>
   javascript:alert(1)
   onerror=malicious()
   ```

2. **Malicious Redirect Detection**
   ```python
   # Blocks dangerous redirects
   http://localhost/admin
   http://169.254.169.254/metadata  # AWS
   file:///etc/passwd
   ```

3. **PII Exposure Detection**
   ```python
   # Detects and masks PII in responses
   - Email addresses
   - Phone numbers
   - SSN
   - Credit cards
   - API keys
   ```

4. **Data Sanitization**
   - Automatically masks detected PII
   - Removes XSS patterns
   - Cleans malicious content

---

## 🧪 **Testing Scenarios**

### **Test 1: Normal Operation** ✅

```python
agent.search_stock_photos("landscape")
```

**Expected:**
- Request validated ✅
- Forwarded to Unsplash ✅
- Response validated ✅
- Returned to agent ✅

### **Test 2: Untrusted API** ❌

```python
agent._call_api_through_gateway(
    target_url="https://evil-api.com/steal-data"
)
```

**Expected:**
- Request validation: BLOCKED
- Reason: "Untrusted API domain"
- Not forwarded to API

### **Test 3: SQL Injection** ❌

```python
agent.search_stock_photos("test' OR '1'='1")
```

**Expected:**
- Request validation: BLOCKED
- Reason: "SQL injection pattern detected"
- Not forwarded to API

### **Test 4: API Key Leak** ❌

```python
agent._call_api_through_gateway(
    target_url="https://api.unsplash.com/photos",
    params={"api_key": "sk-1234567890abcdef"}
)
```

**Expected:**
- Request validation: BLOCKED
- Reason: "API key detected in parameter"
- Not forwarded to API

### **Test 5: XSS in Response** 🧹

```python
# Simulated: API returns malicious content
response = {
    "title": "Photo",
    "description": "<script>alert(1)</script>"
}
```

**Expected:**
- Response validation: SANITIZE
- XSS removed from response
- Clean data returned to agent

### **Test 6: PII in Response** 🧹

```python
# Simulated: API leaks PII
response = {
    "user": "john@example.com",
    "phone": "555-123-4567"
}
```

**Expected:**
- Response validation: SANITIZE
- PII masked: `***EMAIL***`, `***PHONE***`
- Sanitized data returned

---

## 📡 **API Endpoints**

### **POST /proxy**
Main proxy endpoint - intercepts agent API calls

**Request:**
```json
{
  "agent_id": "design-agent-001",
  "target_url": "https://api.unsplash.com/search/photos",
  "method": "GET",
  "headers": {"Authorization": "Client-ID ..."},
  "params": {"query": "landscape"}
}
```

**Response:**
```json
{
  "success": true,
  "request_validation": {
    "decision": "allow",
    "threats": [],
    "risk_score": 0
  },
  "response_validation": {
    "decision": "allow",
    "threats": [],
    "risk_score": 0
  },
  "response_data": {...},
  "threats_detected": [],
  "sanitized": false
}
```

### **GET /trusted-apis**
List all trusted third-party APIs

### **POST /trusted-apis/add**
Add new API to allowlist

### **GET /audit-log**
View audit log of all API calls

### **GET /audit-log/agent/{agent_id}**
View audit log for specific agent

### **GET /threats**
Get threat detection statistics

---

## 📊 **Monitoring & Audit**

### **Audit Log**

Every API call is logged:
```json
{
  "agent_id": "design-agent-001",
  "target_url": "https://api.unsplash.com/search/photos",
  "timestamp": "2026-01-22T08:00:00Z",
  "success": true,
  "threats": [],
  "sanitized": false
}
```

### **Statistics**

```bash
curl http://localhost:7000/audit-log
```

Returns:
```json
{
  "statistics": {
    "total_requests": 150,
    "successful": 145,
    "blocked": 5,
    "threats_detected": 8,
    "sanitized": 3
  }
}
```

---

## 🎯 **Use Cases**

### **1. AI Design Tools (Canva-like)**
- Generate images
- Search stock photos
- Remove backgrounds
- Apply filters

### **2. AI Content Creation**
- Generate text (GPT)
- Create videos (Runway)
- Generate music (Suno)
- Edit images (Midjourney)

### **3. AI Automation Tools**
- Zapier-like workflows
- n8n automation
- Make.com integrations

### **4. AI Research Assistants**
- Search papers (Semantic Scholar)
- Fetch data (APIs)
- Generate summaries (GPT)

---

## 🔧 **Configuration**

### **Add New Trusted API**

```python
# In gateway_core.py
self.trusted_apis["new-api.com"] = {
    "name": "New API",
    "risk_level": "medium",
    "allowed_endpoints": ["/v1/endpoint"],
    "rate_limit": 100
}
```

Or via API:
```bash
curl -X POST http://localhost:7000/trusted-apis/add \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "new-api.com",
    "name": "New API",
    "risk_level": "medium",
    "allowed_endpoints": ["/v1/endpoint"],
    "rate_limit": 100
  }'
```

---

## 📁 **Files**

- `gateway_core.py` - Core gateway logic (600+ lines)
- `gateway_api.py` - FastAPI service
- `ai_design_agent.py` - Demo AI agent (Canva-like)
- `README.md` - This file

---

## ✅ **Benefits**

1. **Bidirectional Security** - Validates both requests and responses
2. **Real-time Protection** - Blocks threats before they execute
3. **Zero Trust** - Never trust third-party APIs
4. **Complete Audit Trail** - Every API call logged
5. **PII Protection** - Automatically sanitizes sensitive data
6. **Easy Integration** - Drop-in proxy for any AI agent
7. **Open Source Friendly** - Works with any open-source agent

---

## 🚀 **Production Deployment**

### **Docker**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn httpx
EXPOSE 7000
CMD ["python", "gateway_api.py"]
```

### **Environment Variables**

```bash
export GATEWAY_PORT=7000
export LOG_LEVEL=INFO
export RATE_LIMIT_ENABLED=true
```

---

**This is the correct solution: A security gateway that protects AI agents from compromised third-party APIs!** 🛡️
