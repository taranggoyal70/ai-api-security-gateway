"""
Mock Backend APIs

Simulates real backend services that agents would call.
These are the actual tool implementations that execute after passing security checks.
"""

import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class MockKnowledgeBase:
    """Mock knowledge base for support articles"""
    
    def __init__(self):
        self.articles = {
            "billing": [
                {"id": "kb001", "title": "How to update payment method", "content": "Go to Settings > Billing..."},
                {"id": "kb002", "title": "Understanding your invoice", "content": "Your invoice includes..."},
                {"id": "kb003", "title": "Refund policy", "content": "We offer refunds within 30 days..."}
            ],
            "technical": [
                {"id": "kb101", "title": "Troubleshooting login issues", "content": "If you can't log in..."},
                {"id": "kb102", "title": "API rate limits", "content": "Our API has the following limits..."}
            ],
            "account": [
                {"id": "kb201", "title": "How to close your account", "content": "To close your account..."},
                {"id": "kb202", "title": "Security best practices", "content": "Enable 2FA..."}
            ]
        }
    
    def search(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        results = []
        
        search_categories = [category] if category else self.articles.keys()
        
        for cat in search_categories:
            if cat in self.articles:
                for article in self.articles[cat]:
                    if query.lower() in article["title"].lower() or query.lower() in article["content"].lower():
                        results.append({
                            **article,
                            "category": cat,
                            "relevance_score": random.uniform(0.7, 1.0)
                        })
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)


class MockTicketingSystem:
    """Mock ticketing system"""
    
    def __init__(self):
        self.tickets = {}
        self.ticket_counter = 1000
    
    def create_ticket(
        self,
        customer_id: str,
        subject: str,
        description: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Create a support ticket"""
        self.ticket_counter += 1
        ticket_id = f"TKT-{self.ticket_counter}"
        
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "subject": subject,
            "description": description,
            "priority": priority,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "assigned_to": None,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        self.tickets[ticket_id] = ticket
        return ticket
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        return self.tickets.get(ticket_id)


class MockCustomerDatabase:
    """Mock customer database"""
    
    def __init__(self):
        self.customers = {
            "CUST-001": {
                "customer_id": "CUST-001",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "555-123-4567",
                "account_status": "active",
                "created_at": "2023-01-15",
                "lifetime_value": 1250.00
            },
            "CUST-002": {
                "customer_id": "CUST-002",
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "555-987-6543",
                "account_status": "active",
                "created_at": "2023-03-20",
                "lifetime_value": 3400.00
            },
            "12345": {
                "customer_id": "12345",
                "name": "Alice Johnson",
                "email": "alice.j@example.com",
                "phone": "555-456-7890",
                "account_status": "active",
                "created_at": "2023-06-10",
                "lifetime_value": 850.00
            }
        }
    
    def get_customer(self, customer_id: str, fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get customer information"""
        customer = self.customers.get(customer_id)
        if not customer:
            return None
        
        if fields:
            return {k: v for k, v in customer.items() if k in fields}
        
        return customer.copy()


class MockOrderSystem:
    """Mock order/billing system"""
    
    def __init__(self):
        self.orders = {
            "ORD-001": {
                "order_id": "ORD-001",
                "customer_id": "CUST-001",
                "amount": 99.99,
                "status": "completed",
                "payment_status": "paid",
                "created_at": "2024-01-10",
                "items": [
                    {"sku": "PROD-A", "name": "Product A", "price": 99.99, "quantity": 1}
                ]
            },
            "ORD-002": {
                "order_id": "ORD-002",
                "customer_id": "12345",
                "amount": 249.99,
                "status": "completed",
                "payment_status": "paid",
                "created_at": "2024-01-15",
                "items": [
                    {"sku": "PROD-B", "name": "Product B", "price": 249.99, "quantity": 1}
                ]
            },
            "12345": {
                "order_id": "12345",
                "customer_id": "12345",
                "amount": 150.00,
                "status": "completed",
                "payment_status": "paid",
                "created_at": "2024-01-20",
                "items": [
                    {"sku": "PROD-C", "name": "Product C", "price": 150.00, "quantity": 1}
                ]
            }
        }
        
        self.refunds = {}
        self.refund_counter = 5000
    
    def lookup_order(self, order_id: str, include_items: bool = True) -> Optional[Dict[str, Any]]:
        """Look up order details"""
        order = self.orders.get(order_id)
        if not order:
            return None
        
        result = order.copy()
        if not include_items:
            result.pop("items", None)
        
        return result
    
    def check_payment_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Check payment status"""
        order = self.orders.get(order_id)
        if not order:
            return None
        
        return {
            "order_id": order_id,
            "payment_status": order["payment_status"],
            "amount": order["amount"],
            "payment_method": "credit_card",
            "last_four": "4242"
        }
    
    def issue_refund(self, order_id: str, amount: float, reason: str) -> Dict[str, Any]:
        """Issue a refund"""
        order = self.orders.get(order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if order["payment_status"] != "paid":
            return {"success": False, "error": "Order not paid"}
        
        if amount > order["amount"]:
            return {"success": False, "error": "Refund amount exceeds order amount"}
        
        self.refund_counter += 1
        refund_id = f"REF-{self.refund_counter}"
        
        refund = {
            "refund_id": refund_id,
            "order_id": order_id,
            "amount": amount,
            "reason": reason,
            "status": "processed",
            "processed_at": datetime.utcnow().isoformat(),
            "estimated_arrival": (datetime.utcnow() + timedelta(days=5)).isoformat()
        }
        
        self.refunds[refund_id] = refund
        
        # Update order status
        order["payment_status"] = "refunded"
        order["refund_id"] = refund_id
        
        return {"success": True, "refund": refund}


class MockSystemMonitoring:
    """Mock system monitoring/DevOps tools"""
    
    def __init__(self):
        self.services = {
            "api-gateway": {"status": "healthy", "uptime": "99.9%", "response_time": "45ms"},
            "database": {"status": "healthy", "uptime": "99.99%", "response_time": "12ms"},
            "cache": {"status": "healthy", "uptime": "99.95%", "response_time": "3ms"},
            "worker": {"status": "degraded", "uptime": "98.5%", "response_time": "120ms"}
        }
        
        self.logs = {
            "api-gateway": [
                "[INFO] Request processed successfully",
                "[INFO] Cache hit for key: user_123",
                "[WARN] Slow query detected: 450ms"
            ],
            "database": [
                "[INFO] Connection pool: 45/100 active",
                "[INFO] Query executed in 8ms",
                "[INFO] Backup completed successfully"
            ]
        }
    
    def get_system_health(self, service: str) -> Dict[str, Any]:
        """Get system health metrics"""
        if service not in self.services:
            return {"error": "Service not found"}
        
        return {
            "service": service,
            "timestamp": datetime.utcnow().isoformat(),
            **self.services[service]
        }
    
    def view_logs(self, service: str, lines: int = 10, level: Optional[str] = None) -> Dict[str, Any]:
        """View service logs"""
        if service not in self.logs:
            return {"error": "Service not found"}
        
        logs = self.logs[service]
        
        if level:
            logs = [log for log in logs if f"[{level.upper()}]" in log]
        
        return {
            "service": service,
            "logs": logs[-lines:],
            "total_lines": len(logs)
        }
    
    def restart_service(self, service: str, environment: str) -> Dict[str, Any]:
        """Restart a service (simulated)"""
        if environment.lower() in ["prod", "production"]:
            return {"success": False, "error": "Production restarts require special approval"}
        
        if service not in self.services:
            return {"success": False, "error": "Service not found"}
        
        # Simulate restart
        time.sleep(0.5)
        
        return {
            "success": True,
            "service": service,
            "environment": environment,
            "status": "restarted",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def run_diagnostic(self, diagnostic_type: str, target: str) -> Dict[str, Any]:
        """Run diagnostic script"""
        diagnostics = {
            "connectivity": f"Testing connectivity to {target}... OK",
            "performance": f"Performance metrics for {target}: CPU 45%, Memory 62%",
            "health": f"Health check for {target}: All systems operational"
        }
        
        result = diagnostics.get(diagnostic_type, "Unknown diagnostic type")
        
        return {
            "diagnostic_type": diagnostic_type,
            "target": target,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================================================
# TOOL EXECUTOR
# ============================================================================

class ToolExecutor:
    """
    Executes actual tool calls after they pass security checks.
    This is what runs AFTER the enforcement gateway allows the action.
    """
    
    def __init__(self):
        self.knowledge_base = MockKnowledgeBase()
        self.ticketing = MockTicketingSystem()
        self.customers = MockCustomerDatabase()
        self.orders = MockOrderSystem()
        self.monitoring = MockSystemMonitoring()
    
    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        
        try:
            if tool_name == "search_knowledge_base":
                results = self.knowledge_base.search(
                    query=parameters.get("query", ""),
                    category=parameters.get("category")
                )
                return {"success": True, "results": results}
            
            elif tool_name == "create_support_ticket":
                ticket = self.ticketing.create_ticket(
                    customer_id=parameters["customer_id"],
                    subject=parameters["subject"],
                    description=parameters.get("description", ""),
                    priority=parameters.get("priority", "medium")
                )
                return {"success": True, "ticket": ticket}
            
            elif tool_name == "get_customer_info":
                customer = self.customers.get_customer(
                    customer_id=parameters["customer_id"],
                    fields=parameters.get("fields")
                )
                if customer:
                    return {"success": True, "customer": customer}
                return {"success": False, "error": "Customer not found"}
            
            elif tool_name == "lookup_order":
                order = self.orders.lookup_order(
                    order_id=parameters["order_id"],
                    include_items=parameters.get("include_items", True)
                )
                if order:
                    return {"success": True, "order": order}
                return {"success": False, "error": "Order not found"}
            
            elif tool_name == "check_payment_status":
                status = self.orders.check_payment_status(
                    order_id=parameters["order_id"]
                )
                if status:
                    return {"success": True, "payment": status}
                return {"success": False, "error": "Order not found"}
            
            elif tool_name == "issue_refund":
                result = self.orders.issue_refund(
                    order_id=parameters["order_id"],
                    amount=parameters["amount"],
                    reason=parameters.get("reason", "Customer request")
                )
                return result
            
            elif tool_name == "get_system_health":
                health = self.monitoring.get_system_health(
                    service=parameters["service"]
                )
                return {"success": True, "health": health}
            
            elif tool_name == "view_logs":
                logs = self.monitoring.view_logs(
                    service=parameters["service"],
                    lines=parameters.get("lines", 10),
                    level=parameters.get("level")
                )
                return {"success": True, "logs": logs}
            
            elif tool_name == "restart_service":
                result = self.monitoring.restart_service(
                    service=parameters["service"],
                    environment=parameters["environment"]
                )
                return result
            
            elif tool_name == "run_diagnostic":
                result = self.monitoring.run_diagnostic(
                    diagnostic_type=parameters["diagnostic_type"],
                    target=parameters["target"]
                )
                return {"success": True, "diagnostic": result}
            
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
