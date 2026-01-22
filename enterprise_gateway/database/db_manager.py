"""
Database Manager - Supports PostgreSQL and SQLite

Handles all database operations for the Enterprise Agent Security Gateway.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


class DatabaseManager:
    """
    Database manager supporting both PostgreSQL (production) and SQLite (development).
    """
    
    def __init__(self, db_type: DatabaseType = DatabaseType.SQLITE, connection_string: Optional[str] = None):
        self.db_type = db_type
        self.connection_string = connection_string or self._get_default_connection()
        self.conn = None
        self._connect()
    
    def _get_default_connection(self) -> str:
        """Get default connection string based on database type"""
        if self.db_type == DatabaseType.SQLITE:
            return "sqlite:///enterprise_gateway.db"
        else:
            # PostgreSQL default (use environment variables)
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "postgres")
            database = os.getenv("DB_NAME", "agent_security")
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _connect(self):
        """Establish database connection"""
        if self.db_type == DatabaseType.SQLITE:
            import sqlite3
            db_path = self.connection_string.replace("sqlite:///", "")
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        else:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            # Parse connection string
            self.conn = psycopg2.connect(
                self.connection_string.replace("postgresql://", ""),
                cursor_factory=RealDictCursor
            )
    
    def execute(self, query: str, params: tuple = None) -> Any:
        """Execute a query"""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.conn.commit()
            return cursor
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def fetchone(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch one row"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows"""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ========================================================================
    # AGENT OPERATIONS
    # ========================================================================
    
    def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """Create a new agent"""
        query = """
            INSERT INTO agents (
                agent_id, display_name, description, autonomy_level,
                can_access_pii, can_modify_data, max_refund_amount, requires_mfa
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """ if self.db_type == DatabaseType.SQLITE else """
            INSERT INTO agents (
                agent_id, display_name, description, autonomy_level,
                can_access_pii, can_modify_data, max_refund_amount, requires_mfa
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        self.execute(query, (
            agent_data['agent_id'],
            agent_data['display_name'],
            agent_data['description'],
            agent_data['autonomy_level'],
            agent_data.get('can_access_pii', False),
            agent_data.get('can_modify_data', False),
            agent_data.get('max_refund_amount'),
            agent_data.get('requires_mfa', False)
        ))
        
        return agent_data['agent_id']
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        query = "SELECT * FROM agents WHERE agent_id = ?" if self.db_type == DatabaseType.SQLITE else "SELECT * FROM agents WHERE agent_id = %s"
        return self.fetchone(query, (agent_id,))
    
    def get_all_agents(self) -> List[Dict]:
        """Get all agents"""
        return self.fetchall("SELECT * FROM agents WHERE status = 'active'")
    
    # ========================================================================
    # PERMISSION OPERATIONS
    # ========================================================================
    
    def grant_permission(self, agent_id: str, tool_name: str) -> None:
        """Grant tool permission to agent"""
        query = """
            INSERT INTO agent_permissions (agent_id, tool_name, is_allowed)
            VALUES (?, ?, TRUE)
            ON CONFLICT (agent_id, tool_name) DO UPDATE SET is_allowed = TRUE
        """ if self.db_type == DatabaseType.SQLITE else """
            INSERT INTO agent_permissions (agent_id, tool_name, is_allowed)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (agent_id, tool_name) DO UPDATE SET is_allowed = TRUE
        """
        
        self.execute(query, (agent_id, tool_name))
    
    def check_permission(self, agent_id: str, tool_name: str) -> bool:
        """Check if agent has permission for tool"""
        query = """
            SELECT is_allowed FROM agent_permissions
            WHERE agent_id = ? AND tool_name = ?
        """ if self.db_type == DatabaseType.SQLITE else """
            SELECT is_allowed FROM agent_permissions
            WHERE agent_id = %s AND tool_name = %s
        """
        
        result = self.fetchone(query, (agent_id, tool_name))
        return result['is_allowed'] if result else False
    
    # ========================================================================
    # SECURITY EVENT OPERATIONS
    # ========================================================================
    
    def log_security_event(self, event_data: Dict[str, Any]) -> int:
        """Log a security event"""
        query = """
            INSERT INTO security_events (
                request_id, event_type, agent_id, tool_name, parameters,
                user_prompt, decision, reason, blocked_by, risk_score, risk_level,
                execution_result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """ if self.db_type == DatabaseType.SQLITE else """
            INSERT INTO security_events (
                request_id, event_type, agent_id, tool_name, parameters,
                user_prompt, decision, reason, blocked_by, risk_score, risk_level,
                execution_result
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING event_id
        """
        
        cursor = self.execute(query, (
            event_data['request_id'],
            event_data['event_type'],
            event_data['agent_id'],
            event_data.get('tool_name'),
            json.dumps(event_data.get('parameters', {})),
            event_data.get('user_prompt'),
            event_data['decision'],
            event_data['reason'],
            event_data.get('blocked_by'),
            event_data.get('risk_score', 0),
            event_data.get('risk_level', 'low'),
            json.dumps(event_data.get('execution_result', {}))
        ))
        
        if self.db_type == DatabaseType.POSTGRESQL:
            return cursor.fetchone()['event_id']
        else:
            return cursor.lastrowid
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent security events"""
        query = f"""
            SELECT * FROM security_events
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        return self.fetchall(query)
    
    def get_events_by_agent(self, agent_id: str, limit: int = 50) -> List[Dict]:
        """Get events for specific agent"""
        query = """
            SELECT * FROM security_events
            WHERE agent_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """ if self.db_type == DatabaseType.SQLITE else """
            SELECT * FROM security_events
            WHERE agent_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        return self.fetchall(query, (agent_id, limit))
    
    def get_high_risk_events(self, limit: int = 50) -> List[Dict]:
        """Get high-risk events"""
        query = f"""
            SELECT * FROM high_risk_events
            LIMIT {limit}
        """
        return self.fetchall(query)
    
    # ========================================================================
    # APPROVAL OPERATIONS
    # ========================================================================
    
    def create_approval(self, approval_data: Dict[str, Any]) -> str:
        """Create approval request"""
        query = """
            INSERT INTO approvals (
                approval_id, request_id, agent_id, tool_name, parameters, reason
            ) VALUES (?, ?, ?, ?, ?, ?)
        """ if self.db_type == DatabaseType.SQLITE else """
            INSERT INTO approvals (
                approval_id, request_id, agent_id, tool_name, parameters, reason
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        self.execute(query, (
            approval_data['approval_id'],
            approval_data['request_id'],
            approval_data['agent_id'],
            approval_data['tool_name'],
            json.dumps(approval_data['parameters']),
            approval_data['reason']
        ))
        
        return approval_data['approval_id']
    
    def approve_request(self, approval_id: str, approver: str) -> None:
        """Approve a pending request"""
        query = """
            UPDATE approvals
            SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE approval_id = ?
        """ if self.db_type == DatabaseType.SQLITE else """
            UPDATE approvals
            SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP
            WHERE approval_id = %s
        """
        
        self.execute(query, (approver, approval_id))
    
    def deny_request(self, approval_id: str, approver: str, reason: str) -> None:
        """Deny a pending request"""
        query = """
            UPDATE approvals
            SET status = 'denied', denied_by = ?, denied_at = CURRENT_TIMESTAMP, denial_reason = ?
            WHERE approval_id = ?
        """ if self.db_type == DatabaseType.SQLITE else """
            UPDATE approvals
            SET status = 'denied', denied_by = %s, denied_at = CURRENT_TIMESTAMP, denial_reason = %s
            WHERE approval_id = %s
        """
        
        self.execute(query, (approver, reason, approval_id))
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approvals"""
        return self.fetchall("SELECT * FROM pending_approvals_view")
    
    # ========================================================================
    # ANALYTICS OPERATIONS
    # ========================================================================
    
    def get_agent_performance(self) -> List[Dict]:
        """Get agent performance metrics"""
        return self.fetchall("SELECT * FROM agent_performance")
    
    def get_tool_usage(self) -> List[Dict]:
        """Get tool usage statistics"""
        return self.fetchall("SELECT * FROM tool_usage")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        stats_query = """
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN decision = 'allow' THEN 1 ELSE 0 END) as allowed,
                SUM(CASE WHEN decision = 'deny' THEN 1 ELSE 0 END) as denied,
                SUM(CASE WHEN decision = 'require_approval' THEN 1 ELSE 0 END) as approval_required,
                SUM(CASE WHEN risk_level = 'low' THEN 1 ELSE 0 END) as risk_low,
                SUM(CASE WHEN risk_level = 'medium' THEN 1 ELSE 0 END) as risk_medium,
                SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) as risk_high,
                SUM(CASE WHEN risk_level = 'critical' THEN 1 ELSE 0 END) as risk_critical
            FROM security_events
        """
        
        result = self.fetchone(stats_query)
        
        if result and result['total_requests'] > 0:
            total = result['total_requests']
            result['allow_rate'] = round((result['allowed'] / total) * 100, 2)
            result['deny_rate'] = round((result['denied'] / total) * 100, 2)
            result['approval_rate'] = round((result['approval_required'] / total) * 100, 2)
        
        return result or {}
    
    # ========================================================================
    # CUSTOMER/ORDER OPERATIONS (For realistic use cases)
    # ========================================================================
    
    def create_customer(self, customer_data: Dict[str, Any]) -> str:
        """Create a customer"""
        query = """
            INSERT INTO customers (customer_id, name, email, phone, account_status, lifetime_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """ if self.db_type == DatabaseType.SQLITE else """
            INSERT INTO customers (customer_id, name, email, phone, account_status, lifetime_value)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        self.execute(query, (
            customer_data['customer_id'],
            customer_data['name'],
            customer_data['email'],
            customer_data.get('phone'),
            customer_data.get('account_status', 'active'),
            customer_data.get('lifetime_value', 0)
        ))
        
        return customer_data['customer_id']
    
    def create_order(self, order_data: Dict[str, Any]) -> str:
        """Create an order"""
        query = """
            INSERT INTO orders (order_id, customer_id, amount, status, payment_status)
            VALUES (?, ?, ?, ?, ?)
        """ if self.db_type == DatabaseType.SQLITE else """
            INSERT INTO orders (order_id, customer_id, amount, status, payment_status)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        self.execute(query, (
            order_data['order_id'],
            order_data['customer_id'],
            order_data['amount'],
            order_data.get('status', 'pending'),
            order_data.get('payment_status', 'unpaid')
        ))
        
        return order_data['order_id']
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        query = "SELECT * FROM orders WHERE order_id = ?" if self.db_type == DatabaseType.SQLITE else "SELECT * FROM orders WHERE order_id = %s"
        return self.fetchone(query, (order_id,))
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
