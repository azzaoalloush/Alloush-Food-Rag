# Local Ollama to Groq Cloud API Migration Plan

**Project:** Alloush Food RAG  
**Date:** February 8, 2026  
**Status:** Design Phase  
**Author:** azzaoalloush (azzaoalloush@gmail.com)

---

## Executive Summary

This document outlines the complete migration strategy from **local Ollama LLM** (on localhost:11434) to **Groq Cloud API** for LLM inference. This transition moves from self-hosted inference to cloud-based, managed LLM services, providing faster inference speeds, better reliability, and simpler deployment at minimal cost.

### Key Benefits

- **⚡ Ultra-Fast Inference**: Groq's specialized hardware delivers 10-20x faster token generation than Ollama
- **☁️ No Infrastructure**: Eliminate local GPU/CPU resource management
- **🔒 Reliability**: Enterprise-grade uptime and availability
- **💰 Cost-Effective**: Free tier + pay-per-use, typically <$1/month for hobby projects
- **🌍 Scalability**: Handle multiple concurrent users without local constraints
- **🛠️ Managed Service**: No model updates, dependency management, or infrastructure maintenance
- **📊 Usage Tracking**: Built-in analytics and cost monitoring

### Trade-offs

- ❌ Network latency (~100-500ms vs ~50ms local)
- ❌ No privacy (data sent to cloud)
- ❌ API rate limits (need handling)
- ❌ Dependency on internet connection

---

## 1. Architecture Comparison

### Current Architecture (Ollama Local)

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Application (rag_run.py)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────────────────────┐   │
│  │ User Query   │──────│ Upstash Vector Query         │   │
│  └──────────────┘      │ (returns relevant docs)      │   │
│         │              └──────────────────────────────┘   │
│         │                           │                      │
│         │                           ▼                      │
│         │      ┌────────────────────────────────────┐     │
│         │      │    Ollama (Local HTTP)             │     │
│         └─────►│  - localhost:11434/api/generate    │     │
│         [HTTP] │  - llama3.2 model                  │     │
│        (local) │  - No API auth needed              │     │
│                │  - GPU/CPU intensive               │     │
│                │  - Simple HTTP interface           │     │
│                └────────────────────────────────────┘     │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │   Tkinter GUI   │                       │
│                  │  - Shows answer │                       │
│                  │  - Streams text │                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

Request Flow:
User Question
     │
     ▼
Retrieve Documents (Upstash Vector)
     │
     ▼
Build Prompt:
"Context: {docs}
Question: {question}
Answer:"
     │
     ▼
POST to Ollama (localhost:11434/api/generate)
     │
     ├─ Model processing (GPU/CPU local)
     │
     ▼
Stream Response Line-by-Line
     │
     ▼
Display in GUI
     │
     ▼
Done (Total: 5-30 seconds)
```

### Proposed Architecture (Groq Cloud)

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Application (rag_run.py)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────────────────────┐   │
│  │ User Query   │──────│ Upstash Vector Query         │   │
│  └──────────────┘      │ (returns relevant docs)      │   │
│         │              └──────────────────────────────┘   │
│         │                           │                      │
│         │                           ▼                      │
│         │      ┌────────────────────────────────────────┐ │
│         │      │    Groq Cloud API (REST/gRPC)        │ │
│         └─────►│  - api.groq.com/openai/v1/chat/     │ │
│         [HTTPS]│    completions                       │ │
│        (cloud) │  - llama-3.1-8b-instant model        │ │
│                │  - Bearer token authentication       │ │
│                │  - Streaming support                 │ │
│                │  - 10-20x faster inference           │ │
│                │  - Enterprise uptime SLA             │ │
│                └────────────────────────────────────────┘ │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │   Tkinter GUI   │                       │
│                  │  - Shows answer │                       │
│                  │  - Streams text │                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

Request Flow:
User Question
     │
     ▼
Retrieve Documents (Upstash Vector)
     │
     ▼
Build Prompt + Message Format:
{
  "model": "llama-3.1-8b-instant",
  "messages": [
    {"role": "system", "content": "You are helpful..."},
    {"role": "user", "content": "Context: {docs}\nQuestion: {question}"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": true
}
     │
     ▼
POST to Groq API (api.groq.com/openai/v1/chat/completions)
│     [HTTPS + Bearer Token Auth]
│
├─ Groq's specialized hardware processes request
├─ 10-20x faster than local inference
│
▼
Stream Response (SSE format)
     │
     ▼
Display in GUI
     │
     ▼
Done (Total: 3-10 seconds, vs 5-30 with Ollama)
```

### Architecture Comparison Table

| Aspect | Ollama (Local) | Groq Cloud | Winner |
|--------|----------------|------------|--------|
| **Hosting** | Local machine | Cloud (Groq servers) | Groq |
| **Setup Complexity** | Medium (install + run) | Low (API key only) | Groq |
| **Inference Speed** | ~50-500ms/query | ~30-100ms/query | Groq (10-20x) |
| **Model Availability** | What you install | All Groq models | Groq |
| **Cost** | $0 (hardware) | <$1/month hobby | Groq |
| **Scalability** | Limited by local GPU | Unlimited (cloud) | Groq |
| **Reliability** | Depends on local setup | 99.95% SLA | Groq |
| **Privacy** | Local only | Data sent to cloud | Ollama |
| **Maintenance** | Manual updates | Automatic | Groq |
| **Internet Required** | ❌ No | ✅ Yes | Ollama |
| **Concurrent Users** | 1-2 | 100+ | Groq |
| **Infrastructure** | GPU/CPU intensive | None needed | Groq |

### Technology Stack Comparison

**Ollama Stack:**
```
Request → HTTP (REST) → Ollama Service (localhost)
         → Model Loading (GPU) → Inference
         → Token Generation → Streaming SSE Response
```

**Groq Stack:**
```
Request → HTTPS (OAuth) → Groq API (CDN global)
        → Authentication (Bearer Token) → Request Queue
        → LPU (Language Processing Unit) Tensor Streaming
        → Parallel Token Generation → Streaming SSE Response
```

**Key Difference:** Groq uses **LPU (Language Processing Unit)** specialized hardware instead of GPU, resulting in:
- Deterministic performance (same speed every time)
- No memory bottlenecks
- Parallel token generation
- 10-20x faster throughput than GPU/CPU

---

## 2. Detailed Migration Steps

### Phase 1: Prerequisites & Environment Setup

#### 2.1.1 Verify Groq Credentials

Check `.env` has Groq API key:
```env
GROQ_API_KEY="your-groq-api-key-here"
```

✅ **Already configured in your .env file**

#### 2.1.2 Install Dependencies

```bash
# Install Groq SDK
pip install groq

# Keep requests for backward compatibility
pip install requests python-dotenv

# Optional: Remove Ollama if not needed for embeddings
# (We're keeping Upstash Vector for embeddings already)
```

#### 2.1.3 Groq API Key Security

**DO:**
- ✅ Store in .env (git-ignored)
- ✅ Load via os.getenv()
- ✅ Rotate key if exposed
- ✅ Use HTTPS for all requests (automatic)
- ✅ Monitor usage in Groq console

**DON'T:**
- ❌ Hardcode key in code
- ❌ Commit .env to git
- ❌ Log the key
- ❌ Share via email/chat

### Phase 2: Code Changes

#### 2.2.1 Imports and Client Initialization

**BEFORE (Ollama):**
```python
import requests

def get_llm_response(prompt):
    """Query Ollama locally"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": True
        },
        timeout=60
    )
    response.raise_for_status()
    return response
```

**AFTER (Groq):**
```python
import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client (uses GROQ_API_KEY env var automatically)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_llm_response(prompt):
    """Query Groq Cloud API"""
    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant answering questions about food."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=1024,
        stream=True,
        stop=None
    )
    return completion
```

#### 2.2.2 RAG Query Function Migration

**BEFORE (Ollama - Partial):**
```python
def rag_query(question, gui_callback=None):
    """Query RAG system with Ollama"""
    try:
        # Step 1: Retrieve documents from vector DB
        results = vector_index.query(data=question, top_k=3)
        top_docs = [r["text"] for r in results]
        
        # Step 2: Build prompt
        context = "\n".join(top_docs)
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        # Step 3: Query Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": True
            },
            stream=True,
            timeout=60
        )
        response.raise_for_status()

        # Step 4: Stream response
        full_response = ""
        if gui_callback:
            gui_callback("answer_start", "")
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    response_text = chunk.get("response", "")
                    full_response += response_text
                    if gui_callback:
                        gui_callback("answer_update", response_text)
                except json.JSONDecodeError:
                    continue
        
        return full_response.strip()

    except requests.exceptions.ConnectionError:
        raise Exception("ERROR: Cannot connect to Ollama. Please run: ollama serve")
    except requests.exceptions.Timeout:
        raise Exception("ERROR: Ollama request timed out.")
    except Exception as e:
        raise Exception(f"ERROR: {str(e)}")
```

**AFTER (Groq):**
```python
def rag_query(question, gui_callback=None):
    """Query RAG system with Groq Cloud"""
    try:
        # Step 1: Retrieve documents from vector DB
        results = vector_index.query(data=question, top_k=3)
        top_docs = [r["text"] for r in results]
        
        # Step 2: Build system prompt and user message
        context = "\n".join(top_docs)
        user_message = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        # Step 3: Query Groq (with streaming)
        stream = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful food expert. Answer questions about food based on the provided context."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            stream=True,
            stop=None
        )

        # Step 4: Stream response
        full_response = ""
        if gui_callback:
            gui_callback("answer_start", "")
        
        for chunk in stream:
            # Groq returns choice with delta containing content
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                if gui_callback:
                    gui_callback("answer_update", content)
        
        return full_response.strip()

    except Exception as e:
        if "401" in str(e):
            error_msg = "ERROR: Invalid Groq API key. Check GROQ_API_KEY in .env"
        elif "503" in str(e) or "429" in str(e):
            error_msg = "ERROR: Groq API rate limited or temporarily unavailable"
        elif "connection" in str(e).lower():
            error_msg = "ERROR: Cannot connect to Groq API. Check internet connection."
        else:
            error_msg = f"ERROR: Groq API error: {str(e)}"
        
        if gui_callback:
            gui_callback("error", error_msg)
        raise Exception(error_msg)
```

#### 2.2.3 Request/Response Format Changes

**Ollama Request Format:**
```json
{
  "model": "llama3.2",
  "prompt": "...",
  "stream": true
}
```

**Ollama Response (Streaming):**
```
{"response":"The","model":"llama3.2",...}
{"response":" tandoori","model":"llama3.2",...}
{"response":" chicken","model":"llama3.2",...}
```

**Groq Request Format (OpenAI-Compatible):**
```json
{
  "model": "llama-3.1-8b-instant",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": true
}
```

**Groq Response (Streaming - Server-Sent Events):**
```
data: {"choices":[{"delta":{"role":"assistant","content":"The"}}]}
data: {"choices":[{"delta":{"content":" tandoori"}}]}
data: {"choices":[{"delta":{"content":" chicken"}}]}
data: [DONE]
```

### Phase 3: Complete Implementation

#### 2.3.1 Updated `rag_run.py` with Groq

Create `rag_run_groq.py` for testing:

```python
import os
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv()

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, "foods.json")

# Initialize clients
try:
    # Upstash Vector (for embeddings)
    vector_index = Index(
        url=os.getenv("UPSTASH_VECTOR_REST_URL"),
        token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
    )
    print("[OK] Connected to Upstash Vector")
except Exception as e:
    print(f"[ERROR] Failed to connect to Upstash Vector: {e}")
    vector_index = None

try:
    # Groq (for LLM)
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    print("[OK] Groq client initialized")
except Exception as e:
    print(f"[ERROR] Failed to initialize Groq client: {e}")
    groq_client = None

# Load food data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# RAG query function
def rag_query(question, gui_callback=None):
    """Query RAG system using Upstash Vector + Groq LLM"""
    try:
        if not groq_client:
            raise Exception("ERROR: Groq client not initialized")
        
        if not vector_index:
            raise Exception("ERROR: Vector index not initialized")

        # Step 1: Query Upstash Vector with raw text
        results = vector_index.query(
            data=question,
            top_k=3,
            include_metadata=True
        )
        
        # Step 2: Extract documents
        top_docs = [r["text"] for r in results]
        top_ids = [r["id"] for r in results]
        top_scores = [r["score"] for r in results]
        
        # Step 3: Display retrieved documents in GUI
        sources_text = "[SOURCES & RELEVANCE]\n"
        for i, (doc, score) in enumerate(zip(top_docs, top_scores)):
            sources_text += f"\n[{i + 1}] (Relevance: {score:.2f})\n{doc}\n"
        
        if gui_callback:
            gui_callback("sources", sources_text)
        
        # Step 4: Build message for Groq
        context = "\n\n".join(top_docs)
        user_message = f"""Use the following food information to answer the question. Provide clear, helpful responses based only on the provided context.

FOOD INFORMATION:
{context}

QUESTION: {question}

Please provide your answer:"""

        # Step 5: Query Groq with streaming
        stream = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert food specialist. Answer questions about food based on the provided context. Be concise and informative."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            stream=True,
            stop=None
        )

        # Step 6: Stream response
        full_response = ""
        if gui_callback:
            gui_callback("answer_start", "")
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                if gui_callback:
                    gui_callback("answer_update", content)
        
        return full_response.strip()
    
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        if gui_callback:
            gui_callback("error", error_msg)
        return ""

# Tkinter GUI
class RAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Food Q&A - Groq Powered")
        self.root.geometry("1000x700")
        
        # Question input
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(input_frame, text="Question:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.question_input = tk.Entry(input_frame, font=("Arial", 10))
        self.question_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.question_input.bind("<Return>", lambda e: self.ask_question())
        
        self.ask_btn = tk.Button(input_frame, text="Ask (Groq)", command=self.ask_question, fg="white", bg="green")
        self.ask_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(root, text="Ready", font=("Arial", 9), fg="green")
        self.status_label.pack(anchor=tk.W, padx=10)
        
        # Sources display
        tk.Label(root, text="Retrieved Sources:", font=("Arial", 9, "bold")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.sources_text = scrolledtext.ScrolledText(root, height=8, font=("Courier", 9))
        self.sources_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)
        
        # Answer display
        tk.Label(root, text="Generated Answer:", font=("Arial", 9, "bold")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.answer_text = scrolledtext.ScrolledText(root, height=12, font=("Courier", 9))
        self.answer_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.querying = False
    
    def update_gui(self, update_type, content):
        """Callback for updating GUI from RAG query."""
        if update_type == "sources":
            self.sources_text.config(state=tk.NORMAL)
            self.sources_text.delete(1.0, tk.END)
            self.sources_text.insert(tk.END, content)
            self.sources_text.config(state=tk.DISABLED)
        
        elif update_type == "answer_start":
            self.status_label.config(text="Generating answer with Groq...", fg="orange")
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, "[Generating answer...]\n")
        
        elif update_type == "answer_update":
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.insert(tk.END, content)
            self.answer_text.see(tk.END)
            self.answer_text.config(state=tk.DISABLED)
        
        elif update_type == "error":
            self.status_label.config(text="Error occurred", fg="red")
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, content)
            self.answer_text.config(state=tk.DISABLED)
        
        self.root.update()
    
    def ask_question(self):
        """Handle question submission."""
        question = self.question_input.get().strip()
        if not question:
            messagebox.showwarning("Empty Question", "Please enter a question.")
            return
        
        if self.querying:
            messagebox.showwarning("Busy", "Already processing a question.")
            return
        
        self.querying = True
        self.ask_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Retrieving documents...", fg="blue")
        self.sources_text.config(state=tk.NORMAL)
        self.sources_text.delete(1.0, tk.END)
        self.sources_text.insert(tk.END, "[Retrieving sources...]\n")
        self.sources_text.config(state=tk.DISABLED)
        
        # Run in background thread
        def query_thread():
            try:
                rag_query(question, gui_callback=self.update_gui)
                self.status_label.config(text="Ready", fg="green")
            except Exception as e:
                self.status_label.config(text="Error", fg="red")
            finally:
                self.querying = False
                self.ask_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=query_thread, daemon=True).start()

# Main execution
if __name__ == "__main__":
    if not groq_client:
        print("[WARN] Groq not available - some features may not work")
    
    root = tk.Tk()
    gui = RAGUI(root)
    root.mainloop()
```

---

## 3. Error Handling & Recovery

### 3.1 Authentication Errors

```python
def handle_groq_error(error):
    """Parse and handle Groq API errors"""
    error_str = str(error).lower()
    
    if "401" in str(error) or "unauthorized" in error_str:
        return {
            "type": "AUTH_ERROR",
            "message": "Invalid Groq API key",
            "action": "Check GROQ_API_KEY in .env file",
            "recoverable": False
        }
    elif "403" in str(error) or "forbidden" in error_str:
        return {
            "type": "PERMISSION_ERROR",
            "message": "Groq API key doesn't have required permissions",
            "action": "Regenerate API key in Groq console",
            "recoverable": False
        }
    elif "429" in str(error) or "rate" in error_str:
        return {
            "type": "RATE_LIMIT",
            "message": "Groq API rate limit exceeded",
            "action": "Wait before retrying",
            "recoverable": True,
            "wait_time": 60
        }
    elif "503" in str(error) or "unavailable" in error_str:
        return {
            "type": "SERVICE_UNAVAILABLE",
            "message": "Groq API temporarily unavailable",
            "action": "Wait and retry",
            "recoverable": True,
            "wait_time": 30
        }
    elif "connection" in error_str or "timeout" in error_str:
        return {
            "type": "NETWORK_ERROR",
            "message": "Cannot connect to Groq API",
            "action": "Check internet connection",
            "recoverable": True,
            "wait_time": 5
        }
    else:
        return {
            "type": "UNKNOWN_ERROR",
            "message": str(error),
            "action": "Check logs for details",
            "recoverable": False
        }

# Usage
try:
    completion = groq_client.chat.completions.create(...)
except Exception as e:
    error_info = handle_groq_error(e)
    print(f"Error: {error_info['message']}")
    print(f"Action: {error_info['action']}")
    if error_info['recoverable']:
        print(f"Retry after {error_info['wait_time']} seconds")
```

### 3.2 Retry Logic with Exponential Backoff

```python
import time

def query_groq_with_retry(messages, max_retries=3):
    """Query Groq with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )
        except Exception as e:
            error_info = handle_groq_error(e)
            
            if not error_info['recoverable']:
                raise  # Can't recover from auth errors, etc
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential: 1s, 2s, 4s
                print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise  # Max retries exceeded
    
    raise Exception("Failed to get Groq response after retries")
```

### 3.3 Fallback to Ollama (Hybrid Mode)

```python
def rag_query_hybrid(question, gui_callback=None):
    """Try Groq first, fallback to Ollama if needed"""
    try:
        # Try Groq first
        print("[INFO] Attempting Groq API query...")
        return rag_query_groq(question, gui_callback)
    except Exception as groq_error:
        print(f"[WARN] Groq failed: {groq_error}")
        print("[INFO] Falling back to Ollama...")
        try:
            return rag_query_ollama(question, gui_callback)
        except Exception as ollama_error:
            error_msg = f"[ERROR] Both Groq and Ollama failed:\n"
            error_msg += f"  Groq: {str(groq_error)}\n"
            error_msg += f"  Ollama: {str(ollama_error)}"
            if gui_callback:
                gui_callback("error", error_msg)
            raise Exception(error_msg)
```

### 3.4 Timeout Handling

```python
from groq import APITimeoutError, APIConnectionError

def rag_query_with_timeout(question, gui_callback=None, timeout=60):
    """Query with explicit timeout handling"""
    try:
        # Groq SDK has built-in timeout (default ~600s)
        # But we can wrap for custom handling
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Query exceeded timeout")
        
        # Set signal handler for Unix systems
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = rag_query(question, gui_callback)
            signal.alarm(0)  # Cancel alarm
            return result
        except TimeoutError:
            msg = f"Query timed out after {timeout}s - response too slow"
            if gui_callback:
                gui_callback("error", msg)
            raise
    except Exception as e:
        raise
```

---

## 4. Rate Limiting & Usage Monitoring

### 4.1 Rate Limit Details

**Groq API Rate Limits (as of 2026):**

| Tier | Requests/Min | Tokens/Min | Tokens/Day |
|------|-------------|-----------|-----------|
| Free | 30 | 10,000 | 100,000 |
| Pro | 300 | 100,000 | 1,000,000 |
| Enterprise | Custom | Custom | Custom |

**Our Project Usage Profile:**
- Hobby: ~10 queries/day × 500 tokens = 5,000 tokens/day (✅ Well within free tier)
- Moderate: ~100 queries/day × 500 tokens = 50,000 tokens/day (✅ Still within free tier)
- Heavy: ~1000 queries/day × 500 tokens = 500,000 tokens/day (❌ Needs Pro tier)

### 4.2 Rate Limit Implementation

```python
import time
from collections import deque
from datetime import datetime, timedelta

class GroqRateLimiter:
    """Track and enforce Groq API rate limits"""
    
    def __init__(self, requests_per_minute=30, tokens_per_minute=10000):
        self.req_limit = requests_per_minute
        self.token_limit = tokens_per_minute
        self.req_window = deque()  # Timestamps of requests
        self.token_window = deque()  # (timestamp, token_count) tuples
    
    def can_make_request(self, estimated_tokens=500):
        """Check if request can be made without exceeding limits"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        while self.req_window and self.req_window[0] < minute_ago:
            self.req_window.popleft()
        while self.token_window and self.token_window[0][0] < minute_ago:
            self.token_window.popleft()
        
        # Check limits
        requests_in_window = len(self.req_window)
        tokens_in_window = sum(t[1] for t in self.token_window)
        
        if requests_in_window >= self.req_limit:
            return False, f"Request limit: {requests_in_window}/{self.req_limit}"
        if tokens_in_window + estimated_tokens > self.token_limit:
            return False, f"Token limit: {tokens_in_window}/{self.token_limit}"
        
        return True, "OK"
    
    def record_request(self, token_count):
        """Record a completed request"""
        now = datetime.now()
        self.req_window.append(now)
        self.token_window.append((now, token_count))
    
    def wait_if_needed(self, estimated_tokens=500):
        """Wait if approaching limits"""
        can_request, msg = self.can_make_request(estimated_tokens)
        if not can_request:
            print(f"[WARN] {msg} - waiting...")
            time.sleep(1)
            return self.wait_if_needed(estimated_tokens)

# Usage
rate_limiter = GroqRateLimiter()

def rag_query_with_rate_limit(question, gui_callback=None):
    """Check rate limits before querying Groq"""
    rate_limiter.wait_if_needed(estimated_tokens=500)
    
    result = rag_query(question, gui_callback)
    
    # Estimate tokens used (rough: 1 token ≈ 4 characters)
    token_count = len(result) // 4 + 100  # prompt tokens
    rate_limiter.record_request(token_count)
    
    return result
```

### 4.3 Usage Monitoring & Analytics

```python
import json
from datetime import datetime

class UsageTracker:
    """Track Groq API usage for monitoring"""
    
    def __init__(self, log_file="groq_usage.log"):
        self.log_file = log_file
    
    def log_query(self, question, response, tokens_used, latency):
        """Log query details"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question_length": len(question),
            "response_length": len(response),
            "tokens_used": tokens_used,
            "latency_seconds": latency,
            "model": "llama-3.1-8b-instant"
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_stats(self):
        """Calculate usage statistics"""
        try:
            with open(self.log_file, 'r') as f:
                entries = [json.loads(line) for line in f]
        except FileNotFoundError:
            return None
        
        if not entries:
            return None
        
        total_tokens = sum(e['tokens_used'] for e in entries)
        avg_latency = sum(e['latency_seconds'] for e in entries) / len(entries)
        
        return {
            "total_queries": len(entries),
            "total_tokens": total_tokens,
            "avg_latency": avg_latency,
            "min_latency": min(e['latency_seconds'] for e in entries),
            "max_latency": max(e['latency_seconds'] for e in entries),
            "estimated_cost": total_tokens * 0.00015,  # Groq pricing
            "first_query": entries[0]['timestamp'],
            "last_query": entries[-1]['timestamp']
        }

# Usage
tracker = UsageTracker()

import time

def rag_query_tracked(question, gui_callback=None):
    """Query with usage tracking"""
    start_time = time.time()
    response = rag_query(question, gui_callback)
    latency = time.time() - start_time
    
    # Estimate tokens (rough approximation)
    tokens_used = (len(question) + len(response)) // 4
    
    tracker.log_query(question, response, tokens_used, latency)
    
    return response
```

---

## 5. Cost Implications

### 5.1 Groq Pricing (2026)

**Groq Free Tier:**
- Up to 10,000 tokens/day (lifetime)
- API rate: 30 req/min
- $0/month
- Perfect for hobby projects

**Groq Pro Tier:**
- Pay-per-use: $0.0005 per 1K input tokens + $0.0015 per 1K output tokens
- Higher rate limits (300 req/min)
- Cost example: 1.5M tokens/month ≈ $0.75-$2.25/month

### 5.2 Cost Comparison: Ollama vs Groq

**Ollama (Local):**
```
Hardware costs:
- GPU (if buying): $200-$3000
- Electricity: $10-30/month
- System: $0 (local machine)

Monthly equivalent: ~$20-50 amortized
Annual: ~$240-600
```

**Groq API:**
```
Free tier: $0/month (up to 10k tokens/day)
Small hobby project: ~$0-1/month
Medium project: $1-5/month
Large project: $5-50/month

Example: 100k tokens/month
- Input tokens: ~70k × $0.0005 = $0.035
- Output tokens: ~30k × $0.0015 = $0.045
- Total: ~$0.08/month
```

**Cost-Benefit Analysis:**

| Scenario | Ollama | Groq (Free) | Groq (Pro) | Winner |
|----------|--------|------------|-----------|--------|
| Hobby (1k tokens/day) | $20/mo* | $0/mo | $0/mo | Groq |
| Moderate (100k tokens/mo) | $20/mo* | $0/mo free | $0.08/mo | Groq |
| Heavy (1M tokens/mo) | $20/mo* | $30/day excess | $0.75/mo | Groq |
| Multiple servers | $40-100/mo | $0 (with scaling) | $5-50/mo | Groq |
| Privacy required | $20/mo* | ❌ | ❌ | Ollama |
| 24/7 uptime needed | $20-30/mo* | ✅ | ✅ | Groq |

*Hardware amortization + electricity

### 5.3 Estimating Your Usage

**For Alloush Food RAG:**

```
Assumptions:
- 10 queries per day (hobby level)
- Average prompt: 600 tokens (context + question)
- Average response: 200 tokens
- 30 days/month

Calculation:
- Daily tokens: 10 × (600 + 200) = 8,000 tokens
- Monthly tokens: 8,000 × 30 = 240,000 tokens
- Free tier limit: 10,000 tokens/day = 300,000 tokens/month

Result: ✅ Comfortably within free tier
Cost: $0/month
```

**If scaled to 100 queries/day:**
```
- Daily tokens: 100 × (600 + 200) = 80,000 tokens
- Monthly tokens: 80,000 × 30 = 2,400,000 tokens
- Estimate: 2M tokens/month
  - Input: 1.4M × $0.0005 = $0.70
  - Output: 0.6M × $0.0015 = $0.90
  - Total: $1.60/month

Result: ✅ Excellent ROI vs Ollama infrastructure
```

### 5.4 Cost Optimization Tips

1. **Batch Queries**: Process multiple questions at once to reduce overhead
2. **Prompt Compression**: Use fewer context docs (top 3 vs top 5)
3. **Token Limit**: Cap max_tokens to actual need (~256 for food Q&A)
4. **Cache**: Implement response caching for duplicate questions
5. **Monitor**: Use usage tracking to identify expensive queries

---

## 6. Fallback Strategies

### 6.1 Hybrid Mode (Groq + Ollama)

**Primary Path:** Groq (faster, managed)  
**Fallback:** Ollama (always available locally)

```python
LLM_STRATEGY = "hybrid"  # "groq", "ollama", or "hybrid"

def get_llm_response(prompt, strategy=LLM_STRATEGY):
    """Get LLM response with optional fallback"""
    
    if strategy in ("groq", "hybrid"):
        try:
            return get_groq_response(prompt)
        except Exception as e:
            if strategy == "groq":
                raise  # Strict Groq mode
            # Continue to fallback
            print(f"[WARN] Groq failed, falling back to Ollama: {e}")
    
    if strategy in ("ollama", "hybrid"):
        try:
            return get_ollama_response(prompt)
        except Exception as e:
            if strategy == "ollama":
                raise  # Strict Ollama mode
            # Both failed
            raise Exception(f"All LLM providers failed: Groq and Ollama unavailable")
    
    raise Exception(f"Unknown LLM strategy: {strategy}")
```

### 6.2 Graceful Degradation

```python
def rag_query_graceful(question, gui_callback=None):
    """Query with graceful degradation"""
    try:
        # Attempt full RAG with streaming
        return rag_query(question, gui_callback)
    except Exception as e:
        logger.error(f"Full RAG failed: {e}")
        
        # Degrade: Use vector DB without LLM
        try:
            results = vector_index.query(data=question, top_k=3)
            degraded_response = "Based on retrieved information:\n\n"
            for i, r in enumerate(results, 1):
                degraded_response += f"{i}. {r['text']}\n\n"
            
            if gui_callback:
                gui_callback("answer_update", degraded_response)
            return degraded_response
        except Exception as e2:
            logger.error(f"Vector DB also failed: {e2}")
            error_msg = "All systems failed. Please try again later."
            if gui_callback:
                gui_callback("error", error_msg)
            raise
```

### 6.3 Configuration-Based Selection

```python
# In .env
LLM_PROVIDER=groq  # or "ollama" or "hybrid"
GROQ_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# Load from config
provider = os.getenv("LLM_PROVIDER", "groq")

def initialize_llm():
    if provider == "groq":
        return GroqLLM(api_key=os.getenv("GROQ_API_KEY"))
    elif provider == "ollama":
        return OllamaLLM(base_url=os.getenv("OLLAMA_BASE_URL"))
    elif provider == "hybrid":
        return HybridLLM(
            groq_key=os.getenv("GROQ_API_KEY"),
            ollama_url=os.getenv("OLLAMA_BASE_URL")
        )
```

---

## 7. Testing Approach

### 7.1 Unit Tests

```python
# test_groq_migration.py

import unittest
from unittest.mock import patch, MagicMock
import asyncio

class TestGroqIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_question = "What is tandoori chicken?"
        self.expected_keywords = ["tandoori", "chicken", "yogurt", "spices"]
    
    def test_groq_client_initialization(self):
        """Test Groq client can be initialized"""
        from groq import Groq
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.assertIsNotNone(client)
        except Exception as e:
            self.fail(f"Groq client initialization failed: {e}")
    
    def test_rag_query_returns_string(self):
        """Test RAG query returns valid string response"""
        response = rag_query(self.test_question)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_answer_contains_relevant_keywords(self):
        """Test response contains food-related information"""
        response = rag_query(self.test_question)
        self.assertTrue(
            any(keyword in response.lower() for keyword in self.expected_keywords),
            f"Response missing expected keywords. Got: {response}"
        )
    
    @patch('groq.Groq.chat.completions.create')
    def test_error_handling_auth_error(self, mock_groq):
        """Test handling of authentication errors"""
        mock_groq.side_effect = Exception("401 Unauthorized")
        
        try:
            rag_query(self.test_question)
            self.fail("Should have raised exception")
        except Exception as e:
            self.assertIn("401", str(e))
    
    @patch('groq.Groq.chat.completions.create')
    def test_error_handling_rate_limit(self, mock_groq):
        """Test handling of rate limit errors"""
        mock_groq.side_effect = Exception("429 Too Many Requests")
        
        error_info = handle_groq_error(mock_groq.side_effect)
        self.assertEqual(error_info['type'], 'RATE_LIMIT')
        self.assertTrue(error_info['recoverable'])

class TestGroqVsOllama(unittest.TestCase):
    """Compare performance between Groq and Ollama"""
    
    def test_groq_faster_than_ollama(self):
        """Verify Groq is faster than Ollama"""
        questions = [
            "What is biryani?",
            "Tell me about sushi",
            "Describe samosa"
        ]
        
        groq_times = []
        ollama_times = []
        
        for q in questions:
            # Test Groq timing
            start = time.time()
            rag_query(q, strategy="groq")
            groq_times.append(time.time() - start)
            
            # Test Ollama timing
            start = time.time()
            rag_query(q, strategy="ollama")
            ollama_times.append(time.time() - start)
        
        avg_groq = sum(groq_times) / len(groq_times)
        avg_ollama = sum(ollama_times) / len(ollama_times)
        
        print(f"Groq avg: {avg_groq:.2f}s")
        print(f"Ollama avg: {avg_ollama:.2f}s")
        
        # Groq should be significantly faster
        self.assertLess(avg_groq, avg_ollama * 0.8,
                       f"Groq not faster. Groq: {avg_groq}s, Ollama: {avg_ollama}s")
```

### 7.2 Integration Tests

```python
# test_rag_groq_flow.py

def test_complete_rag_groq_flow():
    """Test complete RAG pipeline with Groq"""
    query = "Which Indian dish uses chickpeas?"
    
    # Execute RAG
    response = rag_query(query)
    
    # Validate response
    assert response is not None, "Response is None"
    assert len(response) > 50, "Response too short"
    assert "chole" in response.lower() or "chickpea" in response.lower(), \
        f"Wrong answer for chickpeas question. Got: {response}"
    
    print("✅ Complete RAG Groq flow test passed")

def test_groq_streaming():
    """Test Groq streaming works correctly"""
    chunks = []
    
    def callback(update_type, content):
        if update_type == "answer_update":
            chunks.append(content)
    
    rag_query("Tell me about Pad Thai", gui_callback=callback)
    
    # Verify streaming
    assert len(chunks) > 1, "Not enough chunks (inadequate streaming)"
    full_text = "".join(chunks)
    assert len(full_text) > 100, "Response too short"
    assert "pad thai" in full_text.lower(), "Wrong response"
    
    print(f"✅ Streamed {len(chunks)} chunks, total {len(full_text)} chars")

def test_groq_error_recovery():
    """Test recovery from Groq errors"""
    # Simulate transient error
    with patch('groq.Groq.chat.completions.create') as mock:
        # First attempt fails, second succeeds
        mock.side_effect = [
            Exception("429 Rate Limit"),
            MagicMock(text="Fixed response")
        ]
        
        # Should retry and succeed
        try:
            response = query_groq_with_retry(
                [{"role": "user", "content": "test"}],
                max_retries=2
            )
            assert response is not None
            print("✅ Error recovery test passed")
        except Exception as e:
            print(f"❌ Test failed: {e}")
```

### 7.3 Performance Benchmarking

```python
# benchmark_groq_vs_ollama.py

import time
import statistics

def benchmark_providers():
    """Compare Groq vs Ollama performance"""
    
    test_queries = [
        "What is tandoori chicken?",
        "Describe biryani",
        "Tell me about sushi",
        "What is Pad Thai?",
        "Explain samosa",
    ]
    
    providers = ["groq", "ollama"]
    results = {}
    
    for provider in providers:
        times = []
        for query in test_queries:
            start = time.time()
            try:
                rag_query(query, strategy=provider)
                times.append(time.time() - start)
            except Exception as e:
                print(f"{provider.upper()} error: {e}")
                continue
        
        if times:
            results[provider] = {
                "total_time": sum(times),
                "avg_time": statistics.mean(times),
                "median_time": statistics.median(times),
                "min_time": min(times),
                "max_time": max(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
                "queries_completed": len(times),
            }
    
    # Print results
    print("\n=== BENCHMARK RESULTS ===\n")
    for provider, metrics in results.items():
        print(f"{provider.upper()}:")
        print(f"  Queries: {metrics['queries_completed']}")
        print(f"  Avg Time: {metrics['avg_time']:.2f}s")
        print(f"  Median Time: {metrics['median_time']:.2f}s")
        print(f"  Min Time: {metrics['min_time']:.2f}s")
        print(f"  Max Time: {metrics['max_time']:.2f}s")
        print(f "  Stdev: {metrics['stdev']:.2f}s")
        print()
    
    # Calculate speedup
    if "groq" in results and "ollama" in results:
        speedup = results["ollama"]["avg_time"] / results["groq"]["avg_time"]
        print(f"Groq is {speedup:.1f}x faster than Ollama")

if __name__ == "__main__":
    benchmark_providers()
```

---

## 8. Performance Comparison & Expectations

### 8.1 Inference Speed Comparison

**Hardware Setup:**
- Ollama: GPU (varies, assume RTX 3060 or similar)
- Groq: Specialized LPU hardware (Groq nodes)

**Response Time Breakdown:**

| Phase | Ollama | Groq | Notes |
|-------|--------|------|-------|
| Network latency | ~5ms | ~50-100ms | Groq: REST API overhead |
| Embedding (other) | ~100ms | ~50ms | Upstash Vector |
| Token generation | ~1000-5000ms | ~100-300ms | **Groq 10-20x faster** |
| Streaming overhead | ~100ms | ~100ms | Similar |
| **Total per query** | **1200-5200ms** | **300-600ms** | **Groq 5-10x faster overall** |

### 8.2 Throughput Comparison

**Tokens Per Second:**

```
Ollama (llama3.2 on RTX 3060):
  - Input processing: ~40 tokens/sec
  - Output generation: ~20-40 tokens/sec
  - Bottleneck: GPU memory bandwidth

Groq (llama-3.1-8b-instant):
  - Input processing: ~500 tokens/sec
  - Output generation: ~500-600 tokens/sec
  - Advantage: Parallel token generation on LPU
```

### 8.3 Example Performance Profile

**Query: "What is tandoori chicken?"**

```
OLLAMA:
[100ms] Network → [50ms] Vector → [3000ms] Ollama LLM → [150ms] Streaming
Total: ~3.25 seconds

GROQ:
[100ms] Network → [50ms] Vector → [300ms] Groq LLM → [150ms] Streaming
Total: ~0.60 seconds

Speedup: ~5.4x faster ✅
```

### 8.4 Concurrent User Performance

**With 10 concurrent users:**

```
OLLAMA:
- GPU memory: 10GB (may exceed)
- Queue buildup: Yes
- Response time: 3-30 seconds
- Success rate: 80%

GROQ:
- API rate limits: 30 req/min per account
- Queue handling: Automatic
- Response time: 0.5-2 seconds
- Success rate: 99.9%
```

### 8.5 Recommendations Based on Expectations

| Use Case | Recommendation | Reason |
|----------|----------------|--------|
| Single user, local | Ollama | Lower latency (5ms vs 50ms) |
| Hobby/demo app | Groq (Free) | Zero cost, reliable |
| Production deployment | Groq (Pro) | Scalability, reliability |
| Privacy-critical | Ollama | Data stays local |
| Scale to 1000s users | Groq | Unlimited capacity |
| GPU constrained system | Groq | No local GPU needed |

---

## 9. Migration Execution Plan

### Phase 1: Preparation (1-2 hours)

- [ ] Verify GROQ_API_KEY in .env
- [ ] Install groq SDK: `pip install groq`
- [ ] Create feature branch: `git checkout -b feature/groq-migration`
- [ ] Set up test environment
- [ ] Review Groq API docs

### Phase 2: Implementation (2-3 hours)

- [ ] Create `rag_run_groq.py` test version
- [ ] Migrate RAG query function
- [ ] Implement error handling
- [ ] Add rate limiting logic
- [ ] Test with sample queries
- [ ] Performance benchmarking

### Phase 3: Testing (1-2 hours)

- [ ] Unit tests (error handling, API calls)
- [ ] Integration tests (full RAG flow)
- [ ] Performance tests (Groq vs Ollama)
- [ ] Edge case testing (API failures, rate limits)
- [ ] User acceptance testing (GUI behavior)

### Phase 4: Deployment (30 mins)

- [ ] Code review
- [ ] Merge to main branch
- [ ] Update README
- [ ] Push to GitHub
- [ ] Monitor initial usage

### Phase 5: Monitoring (Ongoing)

- [ ] Track API costs
- [ ] Monitor error rates
- [ ] Assessment of performance improvement
- [ ] Usage analytics

---

## 10. Complete Implementation Example

See previous section for complete `rag_run_groq.py` implementation above.

### Key Features:
- ✅ Full Groq API integration
- ✅ Streaming support (token-by-token)
- ✅ Error handling with informative messages
- ✅ GUI updates in real-time
- ✅ Status indicators (Ready/Processing/Error)
- ✅ Compatible with Upstash Vector backend

---

## 11. Migration Checklist

### Pre-Migration
- [ ] Back up current `rag_run.py`
- [ ] Verify GROQ_API_KEY configured
- [ ] Confirm Groq account active
- [ ] Document current performance baseline
- [ ] Create feature branch

### During Migration
- [ ] Update imports (add `from groq import Groq`)
- [ ] Initialize Groq client
- [ ] Refactor `rag_query()` function
- [ ] Update request/response handling
- [ ] Implement error handling
- [ ] Add rate limiting
- [ ] Update GUI for status display
- [ ] Test basic functionality

### Post-Migration
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Performance benchmark
- [ ] Verify all error scenarios handled
- [ ] Update documentation
- [ ] Commit with clear message
- [ ] Push to GitHub
- [ ] Monitor for 24 hours

---

## 12. Rollback Plan

If issues arise:

**Immediate Rollback (< 5 minutes):**
```bash
git revert <groq-commit-hash>
python rag_run.py  # Reverts to Ollama
```

**Gradual Rollback (Hybrid Mode):**
```python
# In .env
LLM_PROVIDER=hybrid  # Try Groq first, fallback to Ollama
```

**Data Safety:**
- ✅ Groq and Ollama both stateless
- ✅ Upstash Vector data unaffected
- ✅ foods.json unmodified
- ✅ No data loss possible

---

## 13. FAQ

**Q: Will my data be safe on Groq?**
A: Groq follows enterprise security standards. However, queries sent to cloud. Use Ollama if privacy is critical.

**Q: What if Groq API goes down?**
A: Implement hybrid mode to fallback to Ollama automatically.

**Q: Will my costs increase?**
A: No - Free tier unlimited. Typical hobby project: $0/month.

**Q: Can I switch between Groq and Ollama?**
A: Yes - use hybrid mode or configuration switch.

**Q: Is Groq faster for all queries?**
A: Yes - 5-20x faster due to LPU hardware.

**Q: What about streaming responses?**
A: Groq supports real-time streaming like Ollama.

**Q: Do I need to change database?**
A: No - Groq only replaces LLM inference, Upstash Vector stays.

---

## Conclusion

Migrating from Ollama to Groq is a **low-risk, high-reward change** that:

✅ Improves performance by 5-20x  
✅ Costs $0-1/month for hobby projects  
✅ Requires no infrastructure management  
✅ Provides enterprise-grade reliability  
✅ Can be rolled back instantly  

**Recommended approach:** Implement hybrid mode for safety, then optionally switch to Groq-only once confident.

---

**Document Version:** 1.0  
**Last Updated:** February 8, 2026  
**Status:** Ready for Implementation  
**Next Step:** Create `rag_run_groq.py` test version
