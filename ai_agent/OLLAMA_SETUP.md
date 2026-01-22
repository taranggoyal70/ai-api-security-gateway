# Ollama Setup Guide

Use Ollama for **free, local LLM** - no API key needed!

---

## ✅ Step 1: Install Ollama

Ollama is already installed on your system at `/usr/local/bin/ollama`

If you need to install it elsewhere:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com/download
```

---

## 📥 Step 2: Pull a Model

You need to download a model first. Recommended options:

### **Option 1: Llama 3.2 (Recommended - Fast & Good)**
```bash
ollama pull llama3.2
```
- Size: ~2GB
- Speed: Fast
- Quality: Excellent for function calling

### **Option 2: Llama 3.1 (More Capable)**
```bash
ollama pull llama3.1
```
- Size: ~4.7GB
- Speed: Medium
- Quality: Better reasoning

### **Option 3: Mistral (Alternative)**
```bash
ollama pull mistral
```
- Size: ~4.1GB
- Speed: Fast
- Quality: Good for tasks

---

## 🚀 Step 3: Start Ollama Server

Ollama runs as a background service:

```bash
# Check if running
ollama list

# If not running, start it
ollama serve
```

The server runs on `http://localhost:11434` by default.

---

## 🧪 Step 4: Test Ollama

Quick test:
```bash
ollama run llama3.2 "Hello, how are you?"
```

You should see a response from the model.

---

## 🔗 Step 5: Use with Agent Security Gateway

### **Option A: Command Line Test**

```bash
cd ai_agent
python agent_client_ollama.py
```

This will run demo scenarios using Ollama.

### **Option B: Via API**

The agent API now supports Ollama:

```bash
curl -X POST http://localhost:8003/agent/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a support ticket for customer 123",
    "agent_id": "support-bot",
    "use_ollama": true,
    "ollama_model": "llama3.2"
  }'
```

### **Option C: Via Dashboard**

Update the dashboard to use Ollama by modifying the request:

```javascript
const res = await fetch(`${AGENT_API_URL}/agent/prompt`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        prompt: prompt,
        agent_id: document.getElementById('agentId').value,
        use_ollama: true,  // ← Enable Ollama
        ollama_model: "llama3.2"
    })
});
```

---

## 📊 Comparison: OpenAI vs Ollama

| Feature | OpenAI | Ollama |
|---------|--------|--------|
| **Cost** | $0.15-$5 per 1M tokens | Free |
| **Speed** | Fast (cloud) | Medium (local) |
| **Quality** | Excellent | Good |
| **Privacy** | Data sent to OpenAI | 100% local |
| **Setup** | API key needed | Download model |
| **Internet** | Required | Not required |

---

## 🔧 Troubleshooting

### **"Connection refused" error**

Ollama server not running:
```bash
ollama serve
```

### **"Model not found" error**

Pull the model first:
```bash
ollama pull llama3.2
```

### **Slow responses**

- Use smaller model (llama3.2 instead of llama3.1)
- Ensure you have enough RAM (8GB minimum)
- Close other applications

### **Check Ollama status**

```bash
# List installed models
ollama list

# Check if server is running
curl http://localhost:11434/api/tags

# View logs
ollama logs
```

---

## 🎯 Recommended Models by Use Case

### **Best for Agent Security Gateway:**
```bash
ollama pull llama3.2
```
- Fast function calling
- Good JSON output
- Low resource usage

### **Best for Complex Reasoning:**
```bash
ollama pull llama3.1:70b
```
- Better at understanding context
- More accurate function selection
- Requires more RAM (32GB+)

### **Best for Speed:**
```bash
ollama pull phi3
```
- Very fast
- Smaller size (2.3GB)
- Good for simple tasks

---

## 🔐 Security Benefits of Ollama

✅ **No data leaves your machine**  
✅ **No API keys to manage**  
✅ **No rate limits**  
✅ **No internet required**  
✅ **Full control over model**  

---

## 📝 Example Usage

```python
from agent_client_ollama import OllamaSecurityAgent

# Create agent
agent = OllamaSecurityAgent(
    agent_id="support-bot",
    model="llama3.2"
)

# Process prompt
result = await agent.process_prompt(
    "Create a support ticket for customer 123 about billing"
)

print(result)
```

---

## 🚀 Next Steps

1. ✅ Pull a model: `ollama pull llama3.2`
2. ✅ Test it: `python agent_client_ollama.py`
3. ✅ Integrate with dashboard
4. ✅ Compare with OpenAI results

**You're now running AI agents completely locally with no API costs!** 🎉
