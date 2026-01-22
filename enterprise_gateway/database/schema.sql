-- Enterprise Agent Security Gateway - Database Schema
-- Supports PostgreSQL and SQLite

-- ============================================================================
-- AGENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    autonomy_level VARCHAR(50) NOT NULL,
    can_access_pii BOOLEAN DEFAULT FALSE,
    can_modify_data BOOLEAN DEFAULT FALSE,
    max_refund_amount DECIMAL(10,2),
    requires_mfa BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TOOLS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tools (
    tool_id SERIAL PRIMARY KEY,
    tool_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    risk_level VARCHAR(20) NOT NULL,
    requires_approval BOOLEAN DEFAULT FALSE,
    max_calls_per_minute INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AGENT PERMISSIONS (Many-to-Many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_permissions (
    permission_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) REFERENCES agents(agent_id) ON DELETE CASCADE,
    tool_name VARCHAR(100) REFERENCES tools(tool_name) ON DELETE CASCADE,
    is_allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, tool_name)
);

-- ============================================================================
-- POLICIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS policies (
    policy_id SERIAL PRIMARY KEY,
    policy_name VARCHAR(200) NOT NULL,
    tool_name VARCHAR(100) REFERENCES tools(tool_name),
    policy_type VARCHAR(50) NOT NULL, -- 'rate_limit', 'approval', 'parameter', 'guard'
    policy_config JSONB NOT NULL, -- Flexible JSON config
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SECURITY EVENTS (Audit Log)
-- ============================================================================
CREATE TABLE IF NOT EXISTS security_events (
    event_id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    agent_id VARCHAR(100) REFERENCES agents(agent_id),
    tool_name VARCHAR(100),
    parameters JSONB,
    user_prompt TEXT,
    decision VARCHAR(20) NOT NULL, -- 'allow', 'deny', 'require_approval'
    reason TEXT,
    blocked_by VARCHAR(100),
    risk_score INTEGER,
    risk_level VARCHAR(20),
    execution_result JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for fast querying
    INDEX idx_agent_id (agent_id),
    INDEX idx_tool_name (tool_name),
    INDEX idx_decision (decision),
    INDEX idx_timestamp (timestamp),
    INDEX idx_risk_level (risk_level)
);

-- ============================================================================
-- APPROVALS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS approvals (
    approval_id VARCHAR(100) PRIMARY KEY,
    request_id VARCHAR(100) REFERENCES security_events(request_id),
    agent_id VARCHAR(100) REFERENCES agents(agent_id),
    tool_name VARCHAR(100),
    parameters JSONB,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'denied'
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    denied_by VARCHAR(100),
    denied_at TIMESTAMP,
    denial_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- RATE LIMITING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    rate_limit_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) REFERENCES agents(agent_id),
    tool_name VARCHAR(100),
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    
    INDEX idx_agent_tool (agent_id, tool_name),
    INDEX idx_window (window_end)
);

-- ============================================================================
-- CUSTOMERS TABLE (For realistic use cases)
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    phone VARCHAR(50),
    account_status VARCHAR(20) DEFAULT 'active',
    lifetime_value DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ORDERS TABLE (For realistic use cases)
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) REFERENCES customers(customer_id),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_status VARCHAR(50) DEFAULT 'unpaid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status)
);

-- ============================================================================
-- TICKETS TABLE (For realistic use cases)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) REFERENCES customers(customer_id),
    subject VARCHAR(500) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    assigned_to VARCHAR(100),
    created_by VARCHAR(100), -- Which agent created it
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority)
);

-- ============================================================================
-- REFUNDS TABLE (For realistic use cases)
-- ============================================================================
CREATE TABLE IF NOT EXISTS refunds (
    refund_id VARCHAR(100) PRIMARY KEY,
    order_id VARCHAR(100) REFERENCES orders(order_id),
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    processed_by VARCHAR(100), -- Which agent processed it
    approved_by VARCHAR(100), -- Human approver
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_order_id (order_id),
    INDEX idx_status (status)
);

-- ============================================================================
-- AGENT SESSIONS (Track agent activity)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) REFERENCES agents(agent_id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    blocked_requests INTEGER DEFAULT 0,
    
    INDEX idx_agent_id (agent_id),
    INDEX idx_started_at (started_at)
);

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- Agent Performance View
CREATE OR REPLACE VIEW agent_performance AS
SELECT 
    agent_id,
    COUNT(*) as total_requests,
    SUM(CASE WHEN decision = 'allow' THEN 1 ELSE 0 END) as allowed,
    SUM(CASE WHEN decision = 'deny' THEN 1 ELSE 0 END) as denied,
    SUM(CASE WHEN decision = 'require_approval' THEN 1 ELSE 0 END) as approvals_needed,
    ROUND(AVG(risk_score), 2) as avg_risk_score,
    MAX(timestamp) as last_activity
FROM security_events
GROUP BY agent_id;

-- Tool Usage View
CREATE OR REPLACE VIEW tool_usage AS
SELECT 
    tool_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN decision = 'allow' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN decision = 'deny' THEN 1 ELSE 0 END) as blocked,
    COUNT(DISTINCT agent_id) as unique_agents
FROM security_events
WHERE tool_name IS NOT NULL
GROUP BY tool_name;

-- High Risk Events View
CREATE OR REPLACE VIEW high_risk_events AS
SELECT 
    event_id,
    request_id,
    agent_id,
    tool_name,
    decision,
    reason,
    risk_score,
    timestamp
FROM security_events
WHERE risk_level IN ('high', 'critical')
ORDER BY timestamp DESC;

-- Pending Approvals View
CREATE OR REPLACE VIEW pending_approvals_view AS
SELECT 
    a.approval_id,
    a.agent_id,
    a.tool_name,
    a.parameters,
    a.reason,
    a.created_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - a.created_at)) / 60 as pending_minutes
FROM approvals a
WHERE a.status = 'pending'
ORDER BY a.created_at ASC;
