"""
Seed Data Generator - Populate database with realistic test data

Creates multiple use cases with real-world scenarios for experimentation.
"""

import random
from datetime import datetime, timedelta
from db_manager import DatabaseManager, DatabaseType


def generate_seed_data(db: DatabaseManager):
    """Generate comprehensive seed data for testing"""
    
    print("🌱 Seeding database with realistic data...")
    
    # ========================================================================
    # 1. CREATE CUSTOMERS (100 realistic customers)
    # ========================================================================
    print("\n📊 Creating 100 customers...")
    
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "James", "Emma", 
                   "Robert", "Olivia", "William", "Ava", "Richard", "Isabella", "Thomas"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez"]
    
    customers = []
    for i in range(1, 101):
        customer_id = f"CUST-{i:04d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        lifetime_value = round(random.uniform(50, 5000), 2)
        
        db.create_customer({
            'customer_id': customer_id,
            'name': name,
            'email': email,
            'phone': phone,
            'account_status': random.choice(['active', 'active', 'active', 'inactive']),
            'lifetime_value': lifetime_value
        })
        
        customers.append(customer_id)
    
    print(f"✅ Created {len(customers)} customers")
    
    # ========================================================================
    # 2. CREATE ORDERS (500 orders across customers)
    # ========================================================================
    print("\n📦 Creating 500 orders...")
    
    orders = []
    for i in range(1, 501):
        order_id = f"ORD-{i:05d}"
        customer_id = random.choice(customers)
        amount = round(random.uniform(10, 1000), 2)
        status = random.choice(['completed', 'completed', 'completed', 'pending', 'cancelled'])
        payment_status = 'paid' if status == 'completed' else random.choice(['paid', 'unpaid', 'refunded'])
        
        db.create_order({
            'order_id': order_id,
            'customer_id': customer_id,
            'amount': amount,
            'status': status,
            'payment_status': payment_status
        })
        
        orders.append(order_id)
    
    print(f"✅ Created {len(orders)} orders")
    
    # ========================================================================
    # 3. CREATE AGENTS (10 different agent types)
    # ========================================================================
    print("\n🤖 Creating 10 agent types...")
    
    agents_config = [
        {
            'agent_id': 'support-agent-tier1',
            'display_name': 'Tier 1 Support Agent',
            'description': 'Basic customer support - tickets and knowledge base only',
            'autonomy_level': 'conditional',
            'can_access_pii': True,
            'can_modify_data': True,
            'max_refund_amount': None,
            'requires_mfa': False
        },
        {
            'agent_id': 'support-agent-tier2',
            'display_name': 'Tier 2 Support Agent',
            'description': 'Advanced support - can view orders and process small refunds',
            'autonomy_level': 'conditional',
            'can_access_pii': True,
            'can_modify_data': True,
            'max_refund_amount': 100.0,
            'requires_mfa': False
        },
        {
            'agent_id': 'refund-agent-basic',
            'display_name': 'Basic Refund Agent',
            'description': 'Processes refunds up to $500',
            'autonomy_level': 'bounded',
            'can_access_pii': True,
            'can_modify_data': True,
            'max_refund_amount': 500.0,
            'requires_mfa': False
        },
        {
            'agent_id': 'refund-agent-senior',
            'display_name': 'Senior Refund Agent',
            'description': 'Processes refunds up to $2000',
            'autonomy_level': 'conditional',
            'can_access_pii': True,
            'can_modify_data': True,
            'max_refund_amount': 2000.0,
            'requires_mfa': True
        },
        {
            'agent_id': 'sales-agent',
            'display_name': 'Sales Agent',
            'description': 'Can view customer data and orders, create quotes',
            'autonomy_level': 'conditional',
            'can_access_pii': True,
            'can_modify_data': False,
            'max_refund_amount': None,
            'requires_mfa': False
        },
        {
            'agent_id': 'analytics-agent',
            'display_name': 'Analytics Agent',
            'description': 'Read-only access for reporting and analytics',
            'autonomy_level': 'assistive',
            'can_access_pii': False,
            'can_modify_data': False,
            'max_refund_amount': None,
            'requires_mfa': False
        },
        {
            'agent_id': 'admin-agent-dev',
            'display_name': 'DevOps Agent (Dev)',
            'description': 'Can manage dev/staging environments',
            'autonomy_level': 'supervised',
            'can_access_pii': False,
            'can_modify_data': True,
            'max_refund_amount': None,
            'requires_mfa': True
        },
        {
            'agent_id': 'admin-agent-prod',
            'display_name': 'DevOps Agent (Production)',
            'description': 'Limited production access - read-only',
            'autonomy_level': 'supervised',
            'can_access_pii': False,
            'can_modify_data': False,
            'max_refund_amount': None,
            'requires_mfa': True
        },
        {
            'agent_id': 'fraud-detection-agent',
            'display_name': 'Fraud Detection Agent',
            'description': 'Monitors for fraudulent activity',
            'autonomy_level': 'conditional',
            'can_access_pii': True,
            'can_modify_data': False,
            'max_refund_amount': None,
            'requires_mfa': False
        },
        {
            'agent_id': 'test-agent-restricted',
            'display_name': 'Test Agent (Restricted)',
            'description': 'For testing - no real permissions',
            'autonomy_level': 'assistive',
            'can_access_pii': False,
            'can_modify_data': False,
            'max_refund_amount': None,
            'requires_mfa': False
        }
    ]
    
    for agent_config in agents_config:
        db.create_agent(agent_config)
    
    print(f"✅ Created {len(agents_config)} agents")
    
    # ========================================================================
    # 4. GRANT PERMISSIONS (Realistic permission matrix)
    # ========================================================================
    print("\n🔐 Setting up permissions...")
    
    permissions = [
        # Tier 1 Support
        ('support-agent-tier1', 'search_knowledge_base'),
        ('support-agent-tier1', 'create_support_ticket'),
        ('support-agent-tier1', 'get_customer_info'),
        
        # Tier 2 Support
        ('support-agent-tier2', 'search_knowledge_base'),
        ('support-agent-tier2', 'create_support_ticket'),
        ('support-agent-tier2', 'get_customer_info'),
        ('support-agent-tier2', 'lookup_order'),
        ('support-agent-tier2', 'issue_refund'),  # Small amounts only
        
        # Basic Refund Agent
        ('refund-agent-basic', 'lookup_order'),
        ('refund-agent-basic', 'check_payment_status'),
        ('refund-agent-basic', 'issue_refund'),
        ('refund-agent-basic', 'get_customer_info'),
        
        # Senior Refund Agent
        ('refund-agent-senior', 'lookup_order'),
        ('refund-agent-senior', 'check_payment_status'),
        ('refund-agent-senior', 'issue_refund'),
        ('refund-agent-senior', 'get_customer_info'),
        ('refund-agent-senior', 'export_customer_data'),
        
        # Sales Agent
        ('sales-agent', 'get_customer_info'),
        ('sales-agent', 'lookup_order'),
        ('sales-agent', 'search_knowledge_base'),
        
        # Analytics Agent
        ('analytics-agent', 'get_system_health'),
        ('analytics-agent', 'view_logs'),
        
        # DevOps Agents
        ('admin-agent-dev', 'get_system_health'),
        ('admin-agent-dev', 'view_logs'),
        ('admin-agent-dev', 'run_diagnostic'),
        ('admin-agent-dev', 'restart_service'),
        
        ('admin-agent-prod', 'get_system_health'),
        ('admin-agent-prod', 'view_logs'),
        
        # Fraud Detection
        ('fraud-detection-agent', 'get_customer_info'),
        ('fraud-detection-agent', 'lookup_order'),
        ('fraud-detection-agent', 'check_payment_status'),
    ]
    
    for agent_id, tool_name in permissions:
        db.grant_permission(agent_id, tool_name)
    
    print(f"✅ Granted {len(permissions)} permissions")
    
    # ========================================================================
    # 5. GENERATE HISTORICAL SECURITY EVENTS (1000 events)
    # ========================================================================
    print("\n📊 Generating 1000 historical security events...")
    
    event_types = ['tool_call_allowed', 'tool_call_denied', 'approval_required']
    decisions = ['allow', 'deny', 'require_approval']
    risk_levels = ['low', 'medium', 'high', 'critical']
    tools = ['create_support_ticket', 'lookup_order', 'issue_refund', 'get_customer_info', 
             'restart_service', 'export_customer_data']
    
    agent_ids = [a['agent_id'] for a in agents_config]
    
    for i in range(1, 1001):
        # Generate realistic event
        agent_id = random.choice(agent_ids)
        tool_name = random.choice(tools)
        
        # Determine if this should be allowed based on permissions
        has_permission = db.check_permission(agent_id, tool_name)
        
        if has_permission:
            decision = random.choice(['allow', 'allow', 'allow', 'require_approval'])
            event_type = 'tool_call_allowed' if decision == 'allow' else 'approval_required'
            risk_score = random.randint(10, 60)
            risk_level = 'low' if risk_score < 40 else 'medium'
            blocked_by = None
        else:
            decision = 'deny'
            event_type = 'tool_call_denied'
            risk_score = random.randint(70, 95)
            risk_level = random.choice(['high', 'critical'])
            blocked_by = random.choice(['Tool Allowlist', 'Policy Check', 'Parameter Validation'])
        
        # Create event
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30), 
                                                   hours=random.randint(0, 23))
        
        event_data = {
            'request_id': f'req_{i}_{timestamp.timestamp()}',
            'event_type': event_type,
            'agent_id': agent_id,
            'tool_name': tool_name,
            'parameters': {
                'customer_id': random.choice(customers),
                'order_id': random.choice(orders) if random.random() > 0.5 else None
            },
            'user_prompt': f'Test prompt {i}',
            'decision': decision,
            'reason': f'Test reason for {decision}',
            'blocked_by': blocked_by,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'execution_result': {'success': decision == 'allow'}
        }
        
        db.log_security_event(event_data)
    
    print(f"✅ Generated 1000 historical events")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*60)
    print("✅ DATABASE SEEDED SUCCESSFULLY!")
    print("="*60)
    print(f"📊 Customers: 100")
    print(f"📦 Orders: 500")
    print(f"🤖 Agents: 10")
    print(f"🔐 Permissions: {len(permissions)}")
    print(f"📈 Historical Events: 1000")
    print("="*60)
    
    # Show statistics
    stats = db.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total Requests: {stats.get('total_requests', 0)}")
    print(f"   Allowed: {stats.get('allowed', 0)} ({stats.get('allow_rate', 0)}%)")
    print(f"   Denied: {stats.get('denied', 0)} ({stats.get('deny_rate', 0)}%)")
    print(f"   Approvals: {stats.get('approval_required', 0)} ({stats.get('approval_rate', 0)}%)")
    print("\n")


def initialize_database(db_type: DatabaseType = DatabaseType.SQLITE):
    """Initialize database with schema and seed data"""
    
    print(f"\n🚀 Initializing {db_type.value.upper()} database...")
    
    # Create database manager
    db = DatabaseManager(db_type=db_type)
    
    # Load and execute schema
    print("\n📋 Creating database schema...")
    with open('schema.sql', 'r') as f:
        schema = f.read()
        
        # Split into individual statements
        statements = [s.strip() for s in schema.split(';') if s.strip()]
        
        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    db.execute(statement)
                except Exception as e:
                    # Skip errors for views and other optional items
                    if 'already exists' not in str(e).lower():
                        print(f"⚠️  Warning: {e}")
    
    print("✅ Schema created")
    
    # Generate seed data
    generate_seed_data(db)
    
    db.close()
    
    print("\n✅ Database initialization complete!")
    return True


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    db_type = DatabaseType.SQLITE
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'postgresql':
            db_type = DatabaseType.POSTGRESQL
    
    print(f"\n{'='*60}")
    print(f"🗄️  DATABASE INITIALIZATION")
    print(f"{'='*60}")
    print(f"Database Type: {db_type.value.upper()}")
    print(f"{'='*60}\n")
    
    initialize_database(db_type)
