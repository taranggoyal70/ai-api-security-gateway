# Database Layer - Real Data Experimentation

Complete database support for experimenting with **real data** and **multiple use cases**.

---

## 🎯 **What This Gives You**

### **1. Real Data Storage**
- ✅ **100 Customers** - Realistic customer profiles
- ✅ **500 Orders** - Transaction history
- ✅ **10 Agent Types** - Different roles and permissions
- ✅ **1000+ Events** - Historical security data
- ✅ **Persistent Storage** - Survives restarts

### **2. Multiple Use Cases**
- **E-commerce** - Orders, refunds, customer support
- **SaaS** - User management, billing, support
- **Enterprise** - Multi-tenant, role-based access
- **DevOps** - System management, diagnostics
- **Fraud Detection** - Monitoring and analysis

### **3. Production-Ready**
- **PostgreSQL** for production
- **SQLite** for development/testing
- **Analytics Views** - Pre-built queries
- **Audit Trail** - Complete history
- **Scalable** - Handles millions of events

---

## 🚀 **Quick Start**

### **Option 1: SQLite (Development)**

```bash
cd database

# Initialize database with seed data
python seed_data.py

# This creates: enterprise_gateway.db
```

**Advantages:**
- ✅ No setup needed
- ✅ File-based (portable)
- ✅ Perfect for demos
- ✅ Fast for < 100K records

### **Option 2: PostgreSQL (Production)**

```bash
# 1. Install PostgreSQL
brew install postgresql  # macOS
# or: sudo apt-get install postgresql  # Linux

# 2. Create database
createdb agent_security

# 3. Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=agent_security

# 4. Initialize
python seed_data.py postgresql
```

**Advantages:**
- ✅ Production-grade
- ✅ Handles millions of records
- ✅ Advanced analytics
- ✅ Multi-user support

---

## 📊 **What Gets Created**

### **Tables:**

1. **`agents`** - Agent definitions (10 types)
   - support-agent-tier1, support-agent-tier2
   - refund-agent-basic, refund-agent-senior
   - sales-agent, analytics-agent
   - admin-agent-dev, admin-agent-prod
   - fraud-detection-agent, test-agent-restricted

2. **`tools`** - Available tools/APIs
   - create_support_ticket, lookup_order
   - issue_refund, get_customer_info
   - restart_service, export_customer_data

3. **`agent_permissions`** - Who can do what
   - Realistic permission matrix
   - Role-based access control

4. **`security_events`** - Complete audit log
   - Every request logged
   - Risk scoring
   - Decision tracking

5. **`approvals`** - Human-in-the-loop
   - Pending approvals
   - Approval history
   - Approver tracking

6. **`customers`** - 100 realistic customers
7. **`orders`** - 500 orders with amounts
8. **`tickets`** - Support tickets
9. **`refunds`** - Refund history

### **Views (Pre-built Analytics):**

- `agent_performance` - Agent statistics
- `tool_usage` - Tool usage patterns
- `high_risk_events` - Security alerts
- `pending_approvals_view` - Approval queue

---

## 🧪 **Use Cases You Can Test**

### **Use Case 1: E-Commerce Support**

```python
# Customer calls about order
agent = "support-agent-tier2"
prompt = "Customer CUST-0042 asking about order ORD-00123"

# Agent can:
✅ Look up order
✅ View customer info
✅ Create support ticket
✅ Issue small refund (< $100)
❌ Issue large refund (needs approval)
```

### **Use Case 2: Refund Processing**

```python
# Different refund agents, different limits
basic_agent = "refund-agent-basic"    # Up to $500
senior_agent = "refund-agent-senior"  # Up to $2000

# Test scenarios:
- Small refund ($50) → Auto-approved
- Medium refund ($500) → Requires approval
- Large refund ($2000) → Senior agent only
- Huge refund ($5000) → Always denied
```

### **Use Case 3: Multi-Tier Support**

```python
# Tier 1: Basic support only
tier1 = "support-agent-tier1"
# Can: Create tickets, search KB
# Cannot: Process refunds, view orders

# Tier 2: Advanced support
tier2 = "support-agent-tier2"
# Can: Everything tier1 + view orders + small refunds
# Cannot: Large refunds, admin tasks
```

### **Use Case 4: DevOps Operations**

```python
# Dev agent: Can restart dev/staging
dev_agent = "admin-agent-dev"
# ✅ Restart dev services
# ✅ View logs
# ❌ Touch production

# Prod agent: Read-only in production
prod_agent = "admin-agent-prod"
# ✅ View prod health
# ✅ View prod logs
# ❌ Restart anything
```

### **Use Case 5: Fraud Detection**

```python
# Fraud agent: Monitor only
fraud_agent = "fraud-detection-agent"
# ✅ View customer data
# ✅ Check orders
# ✅ Analyze patterns
# ❌ Modify anything
```

---

## 📈 **Analytics Queries**

### **Agent Performance**

```sql
SELECT * FROM agent_performance;
```

Output:
```
agent_id              | total_requests | allowed | denied | avg_risk_score
----------------------|----------------|---------|--------|---------------
support-agent-tier1   | 150            | 145     | 5      | 15.2
refund-agent-basic    | 200            | 180     | 20     | 35.8
```

### **Tool Usage**

```sql
SELECT * FROM tool_usage;
```

Output:
```
tool_name              | total_calls | successful | blocked | unique_agents
-----------------------|-------------|------------|---------|---------------
create_support_ticket  | 300         | 295        | 5       | 3
issue_refund           | 150         | 120        | 30      | 2
```

### **High Risk Events**

```sql
SELECT * FROM high_risk_events LIMIT 10;
```

### **Custom Queries**

```sql
-- Find agents with high block rates
SELECT 
    agent_id,
    COUNT(*) as total,
    SUM(CASE WHEN decision = 'deny' THEN 1 ELSE 0 END) as blocked,
    ROUND(100.0 * SUM(CASE WHEN decision = 'deny' THEN 1 ELSE 0 END) / COUNT(*), 2) as block_rate
FROM security_events
GROUP BY agent_id
HAVING block_rate > 20
ORDER BY block_rate DESC;

-- Find most dangerous tools
SELECT 
    tool_name,
    AVG(risk_score) as avg_risk,
    COUNT(*) as usage_count
FROM security_events
WHERE tool_name IS NOT NULL
GROUP BY tool_name
ORDER BY avg_risk DESC;

-- Approval response time
SELECT 
    approval_id,
    agent_id,
    tool_name,
    EXTRACT(EPOCH FROM (approved_at - created_at)) / 60 as approval_time_minutes
FROM approvals
WHERE status = 'approved'
ORDER BY approval_time_minutes DESC;
```

---

## 🔧 **Integration with Gateway**

Update `main.py` to use database:

```python
from database.db_manager import DatabaseManager, DatabaseType

# Initialize database
db = DatabaseManager(db_type=DatabaseType.SQLITE)

# Use in enforcement
@app.post("/gateway/execute")
async def execute_tool_call(request: ToolCallRequest):
    # ... existing code ...
    
    # Log to database instead of memory
    db.log_security_event({
        'request_id': request_id,
        'event_type': event_type,
        'agent_id': request.agent_id,
        'tool_name': request.tool_name,
        'parameters': request.parameters,
        'decision': enforcement_result.decision,
        'reason': enforcement_result.reason,
        'risk_score': enforcement_result.risk_score,
        'risk_level': risk_level
    })
    
    # ... rest of code ...
```

---

## 📊 **Database Schema Overview**

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   agents    │──────▶│ permissions  │◀──────│    tools    │
└─────────────┘       └──────────────┘       └─────────────┘
       │                                              │
       │                                              │
       ▼                                              ▼
┌─────────────────┐                          ┌──────────────┐
│ security_events │                          │   policies   │
└─────────────────┘                          └──────────────┘
       │
       │
       ▼
┌─────────────┐
│  approvals  │
└─────────────┘

┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│  customers  │──────▶│    orders    │──────▶│   refunds   │
└─────────────┘       └──────────────┘       └─────────────┘
       │
       │
       ▼
┌─────────────┐
│   tickets   │
└─────────────┘
```

---

## 🎯 **Benefits for Experimentation**

### **1. Real Data Patterns**
- Test with realistic customer behavior
- Analyze actual usage patterns
- Identify edge cases

### **2. Historical Analysis**
- 1000+ events to analyze
- Trend analysis over time
- Pattern recognition

### **3. Multi-Agent Testing**
- 10 different agent types
- Different permission levels
- Role-based scenarios

### **4. Production Simulation**
- Realistic data volumes
- Complex relationships
- Real-world constraints

### **5. Analytics & Reporting**
- Pre-built views
- Custom queries
- Performance metrics

---

## 🔐 **Security Features**

- ✅ **Audit Trail** - Every action logged
- ✅ **Permission Tracking** - Who can do what
- ✅ **Approval History** - Human oversight
- ✅ **Risk Scoring** - Threat detection
- ✅ **Data Classification** - PII protection

---

## 📝 **Example Workflow**

```bash
# 1. Initialize database
python seed_data.py

# 2. Start gateway with database
python main.py

# 3. Test with real data
curl -X POST http://localhost:8004/gateway/execute \
  -d '{"agent_id":"support-agent-tier2","tool_name":"lookup_order","parameters":{"order_id":"ORD-00123"}}'

# 4. Query results
sqlite3 enterprise_gateway.db "SELECT * FROM security_events ORDER BY timestamp DESC LIMIT 10;"

# 5. Analyze patterns
sqlite3 enterprise_gateway.db "SELECT * FROM agent_performance;"
```

---

## 🚀 **Next Steps**

1. ✅ Initialize database: `python seed_data.py`
2. ✅ Explore data: `sqlite3 enterprise_gateway.db`
3. ✅ Run queries: Use SQL examples above
4. ✅ Integrate with gateway: Update `main.py`
5. ✅ Test use cases: Try different agents/scenarios
6. ✅ Analyze results: Use analytics views

---

**Now you have a production-ready database with real data for comprehensive experimentation!** 🎉
