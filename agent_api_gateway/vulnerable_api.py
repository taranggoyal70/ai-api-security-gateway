#!/usr/bin/env python3
"""
Vulnerable Test API - INTENTIONALLY INSECURE

This API has a REAL SQL injection vulnerability.
We'll use the AI security gateway to protect it.
"""

import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Vulnerable Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a real SQLite database
def init_db():
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT,
            role TEXT
        )
    ''')
    
    # Insert test data
    cursor.execute("DELETE FROM users")  # Clear existing
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@example.com', 'admin')")
    cursor.execute("INSERT INTO users VALUES (2, 'john', 'john123', 'john@example.com', 'user')")
    cursor.execute("INSERT INTO users VALUES (3, 'jane', 'jane123', 'jane@example.com', 'user')")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with test users")

# Initialize on startup
init_db()


@app.get("/")
def root():
    return {
        "api": "Vulnerable Test API",
        "warning": "⚠️  This API is INTENTIONALLY vulnerable for testing",
        "endpoints": {
            "vulnerable": "GET /login?username=X&password=Y (SQL Injection vulnerable)",
            "users": "GET /users (List all users)"
        }
    }


@app.get("/users")
def list_users():
    """List all users (for reference)"""
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return {
        "users": [
            {"id": u[0], "username": u[1], "email": u[2], "role": u[3]}
            for u in users
        ]
    }


@app.get("/login")
def vulnerable_login(username: str, password: str):
    """
    VULNERABLE LOGIN - SQL INJECTION POSSIBLE
    
    This endpoint is INTENTIONALLY vulnerable to demonstrate
    how the AI security gateway protects it.
    """
    
    conn = sqlite3.connect('test_users.db')
    cursor = conn.cursor()
    
    # VULNERABLE: Direct string concatenation (DO NOT DO THIS IN PRODUCTION!)
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    
    print(f"\n🔴 EXECUTING QUERY: {query}\n")
    
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "success": True,
                "message": "Login successful!",
                "user": {
                    "id": result[0],
                    "username": result[1],
                    "email": result[3],
                    "role": result[4]
                },
                "warning": "⚠️  This login was successful because the API is vulnerable!"
            }
        else:
            return {
                "success": False,
                "message": "Invalid credentials"
            }
    
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "error": str(e),
            "message": "SQL error - possible injection attempt detected"
        }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("⚠️  VULNERABLE TEST API")
    print("="*70)
    print("This API is INTENTIONALLY vulnerable to SQL injection")
    print("We'll use the AI security gateway to protect it")
    print("="*70)
    print("\n🚀 Starting on http://localhost:9999")
    print("📚 Docs: http://localhost:9999/docs\n")
    
    uvicorn.run(app, host="0.0.0.0", port=9999)
