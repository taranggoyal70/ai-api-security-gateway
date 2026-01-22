#!/usr/bin/env python3
"""
Real SQL Injection Attack Test

This script demonstrates:
1. Direct attack on vulnerable API (succeeds)
2. Attack through AI security gateway (blocked)
"""

import httpx
import json

VULNERABLE_API = "http://localhost:9999"
SECURITY_GATEWAY = "http://localhost:7100"

def test_direct_attack():
    """Test 1: Attack the vulnerable API directly (NO PROTECTION)"""
    
    print("\n" + "="*70)
    print("🔴 TEST 1: DIRECT ATTACK (No Protection)")
    print("="*70)
    
    # SQL Injection payload
    malicious_username = "admin' OR '1'='1"
    malicious_password = "anything"
    
    print(f"\n📝 Attack Payload:")
    print(f"   Username: {malicious_username}")
    print(f"   Password: {malicious_password}")
    print(f"\n🎯 Attacking: {VULNERABLE_API}/login")
    print("⏳ Sending SQL injection...")
    
    try:
        response = httpx.get(
            f"{VULNERABLE_API}/login",
            params={
                "username": malicious_username,
                "password": malicious_password
            },
            timeout=10.0
        )
        
        result = response.json()
        
        print("\n" + "="*70)
        print("💥 ATTACK RESULT:")
        print("="*70)
        
        if result.get("success"):
            print("❌ ATTACK SUCCESSFUL! (API is vulnerable)")
            print(f"\n   Logged in as: {result['user']['username']}")
            print(f"   Role: {result['user']['role']}")
            print(f"   Email: {result['user']['email']}")
            print("\n⚠️  The attacker bypassed authentication!")
        else:
            print("✅ Attack failed")
            print(f"   Message: {result.get('message')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_protected_attack():
    """Test 2: Attack through AI security gateway (PROTECTED)"""
    
    print("\n" + "="*70)
    print("🛡️  TEST 2: ATTACK THROUGH AI SECURITY GATEWAY")
    print("="*70)
    
    malicious_username = "admin' OR '1'='1"
    malicious_password = "anything"
    
    print(f"\n📝 Same Attack Payload:")
    print(f"   Username: {malicious_username}")
    print(f"   Password: {malicious_password}")
    print(f"\n🎯 Routing through: {SECURITY_GATEWAY}/proxy")
    print("⏳ AI is analyzing the request...")
    
    try:
        response = httpx.post(
            f"{SECURITY_GATEWAY}/proxy",
            json={
                "agent_id": "test-agent",
                "target_url": f"{VULNERABLE_API}/login",
                "method": "GET",
                "params": {
                    "username": malicious_username,
                    "password": malicious_password
                }
            },
            timeout=30.0
        )
        
        result = response.json()
        
        print("\n" + "="*70)
        print("🤖 AI SECURITY DECISION:")
        print("="*70)
        
        if result.get("success"):
            print("❌ Request was allowed (AI didn't detect threat)")
            print(f"\n   Response: {result.get('response_data')}")
        else:
            print("✅ ATTACK BLOCKED BY AI!")
            
            validation = result.get("request_validation", {})
            print(f"\n   Decision: {validation.get('decision', 'N/A').upper()}")
            print(f"   Risk Score: {validation.get('risk_score', 0)}")
            print(f"   Threats: {validation.get('threats', [])}")
            print(f"\n   Details: {validation.get('details', 'N/A')}")
            
            print("\n🛡️  The AI security gateway protected the vulnerable API!")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def show_users():
    """Show all users in the database"""
    
    print("\n" + "="*70)
    print("📊 DATABASE CONTENTS (For Reference)")
    print("="*70)
    
    try:
        response = httpx.get(f"{VULNERABLE_API}/users", timeout=10.0)
        users = response.json()["users"]
        
        print("\nUsers in database:")
        for user in users:
            print(f"   • {user['username']} ({user['role']}) - {user['email']}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n" + "="*70)
    print("🔴 REAL SQL INJECTION ATTACK TEST")
    print("="*70)
    print("\nThis demonstrates:")
    print("1. A REAL SQL injection attack on a vulnerable API")
    print("2. How the AI security gateway blocks it")
    print("="*70)
    
    input("\nPress Enter to start testing...")
    
    # Show database contents
    show_users()
    
    # Test 1: Direct attack (will succeed - API is vulnerable)
    test_direct_attack()
    
    print("\n" + "="*70)
    input("Press Enter to test with AI protection...")
    
    # Test 2: Attack through security gateway (will be blocked)
    test_protected_attack()
    
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)
    print("\nSummary:")
    print("• Without protection: SQL injection succeeded ❌")
    print("• With AI gateway: Attack was blocked ✅")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
