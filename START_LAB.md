# 🚀 Quick Start Guide

## Step-by-Step Instructions

### 1️⃣ Install Dependencies

```bash
pip install fastapi uvicorn httpx
```

Or with virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Open 3 Terminal Windows

#### Terminal 1: Vendor API
```bash
cd vendor_api
python app.py
```
Wait for: `Running on http://localhost:8000`

#### Terminal 2: Consumer API
```bash
cd consumer_api
python app.py
```
Wait for: `Running on http://localhost:8001`

#### Terminal 3: Client UI
```bash
cd client_ui
python -m http.server 8080
```
Wait for: `Serving HTTP on 0.0.0.0 port 8080`

### 3️⃣ Open Browser

Navigate to: **http://localhost:8080**

Click: **"Launch XSS Demo"**

### 4️⃣ Test the Lab

1. Select an XSS variant (try "Image onerror" first)
2. Click **"Run UNSAFE Flow"** → See XSS execute! ⚠️
3. Click **"Run SAFE Flow"** → See XSS blocked! ✅
4. Compare the outputs side-by-side

## 🎯 What to Observe

### UNSAFE Flow (Red)
- Alert popup appears
- Malicious code executes
- No security controls applied

### SAFE Flow (Green)
- No alert popup
- HTML encoded and displayed as text
- Security logs generated
- Controls applied successfully

## 🛑 Stop the Lab

Press `Ctrl+C` in each terminal to stop the servers.

## ✅ Success Indicators

- ✅ All 3 servers running without errors
- ✅ Browser loads UI at localhost:8080
- ✅ UNSAFE flow triggers alert popup
- ✅ SAFE flow displays encoded text
- ✅ Security logs appear in evidence panel

Enjoy learning! 🎓
