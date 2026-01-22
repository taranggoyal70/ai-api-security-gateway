#!/usr/bin/env python3
"""
Real AI Security Testing - Uses Actual Ollama LLM

This script sends REAL SQL injection attacks to the AI agent
and shows you the actual AI reasoning (not simulated).
"""

import httpx
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_real_ai(prompt):
    """Call Ollama LLM for real AI analysis"""
    
    print("🤖 Calling REAL AI (Ollama/Llama3.2)...")
    print("⏳ This takes 5-10 seconds for actual AI reasoning...\n")
    
    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        },
        timeout=60.0
    )
    
    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error: {response.status_code}"


def test_sql_injection():
    """Test REAL SQL injection with AI analysis"""
    
    print("\n" + "="*70)
    print("🔴 TEST 1: REAL SQL INJECTION ATTACK")
    print("="*70)
    
    malicious_query = "admin' OR '1'='1"
    
    print(f"\n📝 Malicious Input: {malicious_query}")
    print("\n🎯 Sending to AI for analysis...")
    
    prompt = f"""You are a cybersecurity expert analyzing an API request for security threats.

REQUEST DETAILS:
- API: https://api.example.com/users/login
- Parameter: username = "{malicious_query}"

ANALYZE THIS REQUEST:
1. Is this request safe or dangerous?
2. What type of attack is this?
3. What is the attacker trying to do?
4. What is the risk level?
5. Should this be allowed or blocked?

Respond in JSON format:
{{
    "decision": "allow or block",
    "attack_type": "type of attack",
    "risk_level": "low, medium, high, or critical",
    "explanation": "detailed explanation of what you detected",
    "attacker_intent": "what the attacker is trying to achieve"
}}
"""
    
    ai_response = call_real_ai(prompt)
    
    print("\n" + "="*70)
    print("🤖 REAL AI ANALYSIS (from Ollama/Llama3.2):")
    print("="*70)
    
    try:
        analysis = json.loads(ai_response)
        print(f"\n✅ Decision: {analysis.get('decision', 'N/A').upper()}")
        print(f"⚠️  Attack Type: {analysis.get('attack_type', 'N/A')}")
        print(f"🔥 Risk Level: {analysis.get('risk_level', 'N/A').upper()}")
        print(f"\n📊 AI Explanation:")
        print(f"   {analysis.get('explanation', 'N/A')}")
        print(f"\n🎯 Attacker Intent:")
        print(f"   {analysis.get('attacker_intent', 'N/A')}")
    except:
        print(ai_response)


def test_normal_request():
    """Test normal request with AI analysis"""
    
    print("\n" + "="*70)
    print("✅ TEST 2: NORMAL SAFE REQUEST")
    print("="*70)
    
    normal_query = "john.doe@example.com"
    
    print(f"\n📝 Normal Input: {normal_query}")
    print("\n🎯 Sending to AI for analysis...")
    
    prompt = f"""You are a cybersecurity expert analyzing an API request for security threats.

REQUEST DETAILS:
- API: https://api.example.com/users/login
- Parameter: username = "{normal_query}"

ANALYZE THIS REQUEST:
1. Is this request safe or dangerous?
2. Are there any security concerns?
3. What is the risk level?
4. Should this be allowed or blocked?

Respond in JSON format:
{{
    "decision": "allow or block",
    "risk_level": "low, medium, high, or critical",
    "explanation": "detailed explanation",
    "concerns": "any security concerns or 'none'"
}}
"""
    
    ai_response = call_real_ai(prompt)
    
    print("\n" + "="*70)
    print("🤖 REAL AI ANALYSIS (from Ollama/Llama3.2):")
    print("="*70)
    
    try:
        analysis = json.loads(ai_response)
        print(f"\n✅ Decision: {analysis.get('decision', 'N/A').upper()}")
        print(f"🔥 Risk Level: {analysis.get('risk_level', 'N/A').upper()}")
        print(f"\n📊 AI Explanation:")
        print(f"   {analysis.get('explanation', 'N/A')}")
        print(f"\n⚠️  Concerns:")
        print(f"   {analysis.get('concerns', 'N/A')}")
    except:
        print(ai_response)


def test_xss_attack():
    """Test XSS attack with AI analysis"""
    
    print("\n" + "="*70)
    print("🔴 TEST 3: XSS ATTACK")
    print("="*70)
    
    xss_payload = "<script>alert('XSS')</script>"
    
    print(f"\n📝 Malicious Input: {xss_payload}")
    print("\n🎯 Sending to AI for analysis...")
    
    prompt = f"""You are a cybersecurity expert analyzing an API request for security threats.

REQUEST DETAILS:
- API: https://api.example.com/comments/create
- Parameter: comment = "{xss_payload}"

ANALYZE THIS REQUEST:
1. Is this request safe or dangerous?
2. What type of attack is this?
3. What could happen if this is executed?
4. What is the risk level?
5. Should this be allowed or blocked?

Respond in JSON format:
{{
    "decision": "allow or block",
    "attack_type": "type of attack",
    "risk_level": "low, medium, high, or critical",
    "explanation": "detailed explanation",
    "potential_impact": "what could happen if executed"
}}
"""
    
    ai_response = call_real_ai(prompt)
    
    print("\n" + "="*70)
    print("🤖 REAL AI ANALYSIS (from Ollama/Llama3.2):")
    print("="*70)
    
    try:
        analysis = json.loads(ai_response)
        print(f"\n✅ Decision: {analysis.get('decision', 'N/A').upper()}")
        print(f"⚠️  Attack Type: {analysis.get('attack_type', 'N/A')}")
        print(f"🔥 Risk Level: {analysis.get('risk_level', 'N/A').upper()}")
        print(f"\n📊 AI Explanation:")
        print(f"   {analysis.get('explanation', 'N/A')}")
        print(f"\n💥 Potential Impact:")
        print(f"   {analysis.get('potential_impact', 'N/A')}")
    except:
        print(ai_response)


def main():
    print("\n" + "="*70)
    print("🤖 REAL AI SECURITY TESTING")
    print("Using Ollama/Llama3.2 for ACTUAL AI Analysis")
    print("="*70)
    print("\nThis is NOT simulated - the AI will actually analyze each attack!")
    print("Each test takes 5-10 seconds for real AI reasoning...\n")
    
    input("Press Enter to start testing...")
    
    # Test 1: SQL Injection
    test_sql_injection()
    
    time.sleep(2)
    
    # Test 2: Normal Request
    test_normal_request()
    
    time.sleep(2)
    
    # Test 3: XSS Attack
    test_xss_attack()
    
    print("\n" + "="*70)
    print("✅ REAL AI TESTING COMPLETE")
    print("="*70)
    print("\nYou just saw REAL AI analysis using Ollama/Llama3.2!")
    print("The AI actually reasoned about each attack and provided explanations.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
