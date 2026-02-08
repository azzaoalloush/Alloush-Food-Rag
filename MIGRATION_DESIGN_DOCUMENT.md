# ChromaDB to Upstash Vector Database Migration Design Document

**Project:** Alloush Food RAG  
**Date:** February 8, 2026  
**Status:** Design Phase  
**Author:** azzaoalloush (azzaoalloush@gmail.com)

---

## Executive Summary

This document outlines the complete migration strategy from ChromaDB (local vector storage) to Upstash Vector (cloud-hosted serverless vector database). The migration simplifies the architecture by eliminating manual embedding generation while maintaining RAG functionality and improving scalability.

### Key Benefits
- **Serverless Architecture**: Eliminates local database management
- **Automatic Embedding**: No need for Ollama embedding API
- **Reduced Dependencies**: Removes embedding model dependency
- **Cloud Scalability**: Enterprise-grade vector database infrastructure
- **Cost Efficiency**: Pay-per-use model with no infrastructure overhead
- **Simplified Deployment**: No local database persistence needed

---

## 1. Architecture Comparison

### Current Architecture (ChromaDB)

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Application (rag_run.py)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────────────────────┐   │
│  │ User Query   │──────│ Question Embedding (Ollama)  │   │
│  └──────────────┘      └──────────────────────────────┘   │
│         │                           │                      │
│         │                           ▼                      │
│         │      ┌────────────────────────────────────┐     │
│         │      │      ChromaDB (Local Vector DB)    │     │
│         └─────►│   - Persistent storage on disk     │     │
│                │   - Cosine similarity search       │     │
│                │   - Returns top K results          │     │
│                └────────────────────────────────────┘     │
│         │                           │                      │
│         │                           ▼                      │
│         │      ┌────────────────────────────────────┐     │
│         └─────►│       Ollama LLM (llama3.2)        │     │
│                │   - Generates answer               │     │
│                │   - Streams response               │     │
│                └────────────────────────────────────┘     │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │   Tkinter GUI   │                       │
│                  │  - Shows sources│                       │
│                  │  - Streams answer                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

Data Loading Flow (Initialization):
┌─────────────┐
│  foods.json │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ Parse JSON data      │
│ Enrich with region   │
│ & type metadata      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Generate Embeddings (Ollama) │
│ - mxbai-embed-large          │
│ - API calls for each item    │
│ - ~90+ items = 90+ requests  │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Store in ChromaDB            │
│ - Local persistence          │
│ - Disk-based storage         │
│ - Ready for queries          │
└──────────────────────────────┘
```

### Proposed Architecture (Upstash Vector)

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Application (rag_run.py)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────────────────────┐   │
│  │ User Query   │──────│ Upstash Vector API (auto)    │   │
│  └──────────────┘      │ Query with raw text          │   │
│         │              │ (embedding done server-side) │   │
│         │              └──────────────────────────────┘   │
│         │                           │                      │
│         │                           ▼                      │
│         │      ┌────────────────────────────────────┐     │
│         └─────►│  Upstash Vector (Cloud, REST API) │     │
│         [REST] │   - Serverless vector DB          │     │
│                │   - Built-in embedding model      │     │
│                │   - Cosine similarity search      │     │
│                │   - Returns top K results         │     │
│                └────────────────────────────────────┘     │
│         │                           │                      │
│         │                           ▼                      │
│         │      ┌────────────────────────────────────┐     │
│         └─────►│       Ollama LLM (llama3.2)        │     │
│                │   - Generates answer               │     │
│                │   - Streams response               │     │
│                └────────────────────────────────────┘     │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │   Tkinter GUI   │                       │
│                  │  - Shows sources│                       │
│                  │  - Streams answer                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘

Data Loading Flow (Initialization):
┌─────────────┐
│  foods.json │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ Parse JSON data      │
│ Enrich with region   │
│ & type metadata      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Upsert to Upstash Vector (REST API)  │
│ - Send raw text data                 │
│ - Embeddings generated server-side   │
│ - mxbai-embed-large v1 (built-in)    │
│ - No local processing needed         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Upstash Vector Storage               │
│ - Cloud-hosted persistence           │
│ - 1024-dimensional vectors           │
│ - Ready for queries                  │
└──────────────────────────────────────┘
```

### Key Differences Summary

| Aspect | ChromaDB (Current) | Upstash Vector (Proposed) |
|--------|-------------------|--------------------------|
| **Hosting** | Local disk | Cloud (Upstash servers) |
| **Embedding** | Manual via Ollama | Automatic (server-side) |
| **Infrastructure** | Persistent local DB | Serverless REST API |
| **Dependencies** | Ollama, ChromaDB | Upstash Python SDK |
| **Dimensions** | 1024 (mxbai-embed-large) | 1024 (BAAI/bge-large-en-v1.5) |
| **Sequence Length** | - | 512 tokens (truncates if needed) |
| **Query Latency** | Sub-millisecond (local) | ~100-300ms (network + cloud) |
| **Scalability** | Limited by local disk | Unlimited (cloud) |
| **Cost** | $0 (local) | Pay-per-use (vectors stored + API calls) |
| **Authentication** | File-based | Token-based (REST) |
| **Deployment** | Self-hosted | Managed service |

---

## 2. Detailed Implementation Plan

### Phase 1: Environment & Authentication Setup

#### 2.1.1 Environment Variables
Update `.env` file with Upstash Vector credentials:

```env
# Existing credentials
USERNAME=azzaoalloush
EMAIL=azzaoalloush@gmail.com

# Upstash Vector (NEW)
UPSTASH_VECTOR_REST_URL="https://your-index.upstash.io"
UPSTASH_VECTOR_REST_TOKEN="your-token-here"

# Optional: Keep Ollama for LLM generation (still needed)
OLLAMA_BASE_URL="http://localhost:11434"
```

#### 2.1.2 Install Dependencies
Remove ChromaDB, add Upstash Vector SDK:

```bash
# Remove old
pip uninstall chromadb

# Add new
pip install upstash-vector requests python-dotenv
```

### Phase 2: Code Structure Changes

#### 2.2.1 Module Organization

**Old Structure:**
```
rag_run.py
├── ChromaDB client initialization
├── get_embedding() - for question
├── (internal: items are embedded during load)
├── rag_query() - uses ChromaDB
└── GUI (Tkinter)
```

**New Structure:**
```
rag_run.py
├── Upstash Vector client initialization
├── rag_query() - uses Upstash Vector (no embedding needed)
├── GUI (Tkinter) - unchanged
└── Data loading - simplified (no embedding step)
```

#### 2.2.2 Core Components to Replace

**Component 1: Vector Database Client**

**BEFORE (ChromaDB):**
```python
import chromadb

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
```

**AFTER (Upstash):**
```python
from upstash_vector import Index

vector_index = Index(
    url=os.getenv("UPSTASH_VECTOR_REST_URL"),
    token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
)
```

**Component 2: Data Upsert Process**

**BEFORE (ChromaDB with Ollama embedding):**
```python
documents = []
ids = []
embeddings = []

for item in food_data:
    enriched_text = item["text"]
    if "region" in item:
        enriched_text += f" This food is popular in {item['region']}."
    if "type" in item:
        enriched_text += f" It is a type of {item['type']}."
    
    # Manual embedding generation
    emb = get_embedding(enriched_text)
    documents.append(item["text"])
    embeddings.append(emb)
    ids.append(item["id"])

# Batch upsert with pre-computed embeddings
collection.add(
    documents=documents,
    embeddings=embeddings,
    ids=ids
)
```

**AFTER (Upstash with automatic embedding):**
```python
vectors_to_upsert = []

for item in food_data:
    enriched_text = item["text"]
    if "region" in item:
        enriched_text += f" This food is popular in {item['region']}."
    if "type" in item:
        enriched_text += f" It is a type of {item['type']}."
    
    # Store metadata as dict
    metadata = {
        "original_id": item["id"],
        "region": item.get("region", "Unknown"),
        "type": item.get("type", "Unknown"),
    }
    
    # Upstash handles embedding automatically
    vectors_to_upsert.append({
        "id": item["id"],
        "text": enriched_text,
        "metadata": metadata
    })

# Batch upsert with raw text (embedding done server-side)
vector_index.upsert(vectors_to_upsert)
```

**Component 3: Query Process**

**BEFORE (ChromaDB):**
```python
def rag_query(question, gui_callback=None):
    # Step 1: Embed the question
    q_emb = get_embedding(question)
    
    # Step 2: Query ChromaDB with embedded vector
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=3
    )
    
    # Step 3: Extract and process results
    top_docs = results['documents'][0]
    top_ids = results['ids'][0]
    # ... rest of processing
```

**AFTER (Upstash):**
```python
def rag_query(question, gui_callback=None):
    try:
        # Step 1: Query Upstash with raw text (no embedding needed)
        results = vector_index.query(
            data=question,
            top_k=3,
            include_metadata=True
        )
        
        # Step 2: Extract documents from results
        top_docs = [r["text"] for r in results]
        top_ids = [r["id"] for r in results]
        top_metadata = [r["metadata"] for r in results]
        
        # Step 3: Rest of processing remains the same
        # ... continue with answer generation
```

### Phase 3: API Integration Details

#### 2.3.1 Upstash Vector SDK Methods

**Upsert (Store Data):**
```python
# Single vector
vector_index.upsert(
    id="food-1",
    text="Biryani is a flavorful Indian rice dish...",
    metadata={"region": "Hyderabad", "type": "Main Course"}
)

# Batch upsert
vectors = [
    {"id": "1", "text": "...", "metadata": {...}},
    {"id": "2", "text": "...", "metadata": {...}},
]
vector_index.upsert(vectors)
```

**Query (Search):**
```python
results = vector_index.query(
    data="What is tandoori chicken?",  # Raw text - embedded by Upstash
    top_k=3,                            # Return top 3 results
    include_metadata=True,              # Include stored metadata
    include_vectors=False,              # Don't return vector data
    include_data=True,                  # Return original text
    filters=None,                       # Optional metadata filtering
)

# Result structure:
# [
#     {
#         "id": "12",
#         "score": 0.92,  # Cosine similarity
#         "text": "Tandoori chicken is chicken marinated in yogurt...",
#         "metadata": {"region": "Punjab", "type": "Main Course"}
#     },
#     ...
# ]
```

**Delete (if needed):**
```python
vector_index.delete(["id-1", "id-2"])
```

**Update (if needed):**
```python
vector_index.upsert(
    id="id-1",
    text="Updated text...",
    metadata={...}
)
```

#### 2.3.2 Error Handling

**BEFORE (ChromaDB):**
```python
except requests.exceptions.ConnectionError:
    raise Exception("Cannot connect to Ollama at localhost:11434")
except requests.exceptions.Timeout:
    raise Exception("Ollama request timed out")
```

**AFTER (Upstash):**
```python
except Exception as e:
    if "401" in str(e):
        raise Exception("Invalid Upstash Vector credentials")
    elif "connection" in str(e).lower():
        raise Exception("Cannot connect to Upstash Vector API")
    elif "timeout" in str(e).lower():
        raise Exception("Upstash Vector request timed out")
    elif "429" in str(e):
        raise Exception("Rate limit exceeded on Upstash Vector")
    else:
        raise Exception(f"Upstash Vector error: {str(e)}")
```

---

## 3. Code Structure Changes Required

### 3.1 Complete rag_run.py Refactor

**Sections to Modify:**

1. **Imports Section**
   - Remove: `import chromadb`
   - Add: `from upstash_vector import Index`

2. **Constants Section**
   - Remove: `CHROMA_DIR`, `COLLECTION_NAME`
   - Add: Upstash endpoint constants

3. **Vector Database Initialization**
   - Replace entire ChromaDB setup block

4. **get_embedding() Function**
   - ⚠️ **IMPORTANT**: Keep this function for now (still need for Ollama)
   - Remove embedding generation from data loading pipeline

5. **Data Loading Block**
   - Remove embedding generation loop
   - Simplify to just parse JSON and upsert raw text

6. **rag_query() Function**
   - Replace collection.query() with vector_index.query()
   - Update results parsing to match Upstash response format

7. **GUI Section**
   - Minimal changes (handles sources and answers the same way)

### 3.2 Migration Checklist

- [ ] Update .env with Upstash credentials
- [ ] Install upstash-vector package
- [ ] Replace ChromaDB client initialization
- [ ] Update data loading (remove embedding generation)
- [ ] Modify upsert logic to use Upstash API
- [ ] Update query function to use Upstash API
- [ ] Update error handling for API errors
- [ ] Test with sample queries
- [ ] Verify metadata is stored correctly
- [ ] Performance testing
- [ ] Remove chroma_db/ directory (no longer needed)

---

## 4. API Differences and Implications

### 4.1 Request/Response Structure

**ChromaDB Query:**
```python
response = {
    'documents': [['doc1', 'doc2', 'doc3']],
    'ids': [['id1', 'id2', 'id3']],
    'distances': [[0.1, 0.2, 0.3]],
    'embeddings': None,
    'metadatas': [[{...}, {...}, {...}]]
}
```

**Upstash Vector Query:**
```python
response = [
    {
        'id': 'id1',
        'score': 0.9,  # Higher = more similar (unlike distance)
        'text': 'doc1',
        'metadata': {...}
    },
    {
        'id': 'id2',
        'score': 0.85,
        'text': 'doc2',
        'metadata': {...}
    },
    {
        'id': 'id3',
        'score': 0.8,
        'text': 'doc3',
        'metadata': {...}
    }
]
```

### 4.2 Implications

| Aspect | Impact |
|--------|--------|
| **Response Format** | Single list vs nested dict - requires parsing change |
| **Similarity Score** | Cosine similarity (0-1) vs distance - score is higher for better matches |
| **Metadata** | Comes within each result vs separate array |
| **Async Operations** | All calls are async over REST - consider 100-300ms latency |
| **Batch Size** | Upstash has batch limits - may need chunking for large datasets |
| **Rate Limiting** | API enforces rate limits - need error handling for 429 responses |

---

## 5. Error Handling Strategies

### 5.1 Authentication Errors

```python
try:
    vector_index.query(data="test")
except Exception as e:
    if "401" in str(e) or "Unauthorized" in str(e):
        print("[ERROR] Invalid Upstash Vector credentials")
        print("Please check UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN in .env")
        return None
```

### 5.2 Network Errors

```python
import requests
from urllib.error import URLError

try:
    results = vector_index.query(data=question, top_k=3)
except (URLError, requests.ConnectionError) as e:
    print("[ERROR] Cannot connect to Upstash Vector")
    print("Please check your internet connection and UPSTASH_VECTOR_REST_URL")
    return None
except requests.Timeout as e:
    print("[ERROR] Upstash Vector request timed out")
    print("The query took too long. Try again shortly.")
    return None
```

### 5.3 Rate Limiting

```python
import time

def rag_query_with_retry(question, max_retries=3):
    for attempt in range(max_retries):
        try:
            results = vector_index.query(data=question, top_k=3)
            return results
        except Exception as e:
            if "429" in str(e):  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"[WARN] Rate limited. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Failed after retries - rate limit exceeded")
```

### 5.4 Data Loss Prevention

```python
# Always validate before upsert
def safe_upsert_foods(food_data):
    if not food_data:
        print("[ERROR] No food data to upsert")
        return False
    
    if not isinstance(food_data, list):
        print("[ERROR] Food data must be a list")
        return False
    
    try:
        # Validate each item
        validated = []
        for item in food_data:
            if "id" not in item or "text" not in item:
                print(f"[WARN] Skipping invalid item: {item}")
                continue
            validated.append(item)
        
        if not validated:
            print("[ERROR] No valid items to upsert")
            return False
        
        vector_index.upsert(validated)
        print(f"[OK] Successfully upserted {len(validated)} items")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to upsert: {str(e)}")
        return False
```

---

## 6. Performance Considerations

### 6.1 Latency Analysis

**ChromaDB (Local):**
- Vector search: ~1-10ms
- Embedding generation: ~100-500ms per query
- Total query latency: 100-510ms

**Upstash Vector:**
- Network round-trip: ~50-150ms (varies by region)
- Server-side embedding: ~50-200ms
- Similarity search: ~10-50ms
- Total query latency: 110-400ms

**RAG Total Time (unchanged):**
- Vector search: 100-500ms (varies)
- LLM generation: 5-30 seconds (depends on answer length)
- Total: 5-30+ seconds

### 6.2 Throughput Comparison

| Operation | ChromaDB | Upstash Vector |
|-----------|----------|-----------------|
| Query/sec (single) | ~100 | ~5-10 (API limits) |
| Concurrent queries | Limited by CPU | Distributed |
| Data load size | Local disk space | 100GB+ (paid) |
| Batch upsert | ~1000 items/call | ~100 items/call (batching) |

### 6.3 Optimization Strategies

1. **Connection Pooling**
   - Upstash SDK handles this automatically
   - Reuse single Index client instance

2. **Query Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def cached_query(question):
       return vector_index.query(data=question, top_k=3)
   ```

3. **Batch Operations**
   - Upsert data in batches of 50-100 items
   - Reduces API call overhead

4. **Lazy Initialization**
   - Only connect to Upstash when needed
   - Check availability on first query

---

## 7. Cost Implications

### 7.1 Upstash Vector Pricing (as of 2026)

**Free Tier:**
- 10,000 vectors
- 10 ReQ/second
- $0/month

**Pro Tier:**
- Unlimited vectors
- Higher throughput
- Per-vector pricing + per-operation pricing
- Estimated: $0.04 per 1M vectors + $0.02 per 1K operations

### 7.2 Cost Estimation for Alloush Food RAG

**Scenario: 90 food items, 10 queries/day**

**Monthly Cost:**
- Storage: 90 vectors ≈ $0.0036 (negligible)
- Query operations: 10 queries × 30 days = 300 operations ≈ $0.006
- **Estimated monthly cost: <$0.01**

**ChromaDB (Current) Cost:**
- Server/hosting: $0 (local)
- Ollama: $0 (local)
- Electricity: ~$5-10/month (small overhead)
- **Current monthly cost: ~$5-10**

### 7.3 Break-Even Analysis

For this project, cost difference is negligible. Upstash is more economical for:
- Deployed applications (not running locally)
- Multiple users accessing simultaneously
- Scaling to thousands of items
- Multi-region deployments

For local development: ChromaDB is cheaper but less scalable.

### 7.4 Cost Optimization Tips

1. Use Free Tier during development
2. Batch queries to reduce API calls
3. Cache frequent queries
4. Clean up unused vectors periodically
5. Monitor usage via Upstash dashboard

**Recommendation:** Switch to Upstash for production, keep ChromaDB for local dev.

---

## 8. Security Considerations

### 8.1 API Key Management

**Current (ChromaDB):**
```python
# File-based storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")
```
- ✅ No credentials needed
- ❌ Database visible on filesystem

**Upstash Vector:**
```python
# Token-based authentication
UPSTASH_VECTOR_REST_URL = "https://your-index.upstash.io"
UPSTASH_VECTOR_REST_TOKEN = "secret-token"
```
- ✅ Token-based access control
- ❌ Credentials must be protected

### 8.2 Security Best Practices

1. **Environment Variables**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   url = os.getenv("UPSTASH_VECTOR_REST_URL")
   token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
   
   # Never hardcode credentials
   ```

2. **Git Ignore**
   ```gitignore
   .env              # Ignore all .env files
   .env.local
   .env.*.local
   chroma_db/        # No longer needed
   ```

3. **Token Rotation**
   - Upstash allows rotating tokens without downtime
   - Plan for quarterly rotation
   - Keep old token during transition

4. **Network Security**
   - Upstash uses HTTPS (TLS 1.2+)
   - All traffic encrypted in transit
   - No plaintext credentials in logs

5. **Access Control**
   - One read-write token per environment (dev, prod)
   - Consider creating read-only tokens for querying
   - Monitor token usage in Upstash dashboard

6. **Deployment Security**

   **For Containerized Apps (Docker):**
   ```dockerfile
   FROM python:3.9
   # ...
   # Pass secrets via environment variables or secrets manager
   # Never build secrets into image
   ```

   **For Serverless (AWS Lambda, etc.):**
   ```python
   # Use AWS Secrets Manager or similar
   import aws_lambda_powertools
   
   @aws_lambda_powertools.parameters.secrets_manager_cache
   def get_upstash_token():
       return secrets_manager.get_secret_value(...)
   ```

7. **Monitoring & Logging**
   ```python
   import logging
   
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   try:
       results = vector_index.query(...)
   except Exception as e:
       logger.error(f"Query failed: {str(e)}", exc_info=True)
       # Don't log the actual error details (might contain token)
   ```

### 8.3 Credential Exposure Prevention

**DO:**
- ✅ Store credentials in .env (git-ignored)
- ✅ Use os.getenv() to load credentials
- ✅ Rotate tokens regularly
- ✅ Use HTTPS only
- ✅ Monitor access logs
- ✅ Use read-only tokens where possible

**DON'T:**
- ❌ Commit .env to git
- ❌ Hardcode credentials in code
- ❌ Log credentials
- ❌ Share tokens via email/chat
- ❌ Use same token across environments
- ❌ Expose credentials in error messages

### 8.4 Disaster Recovery

1. **Backup Strategy**
   - Export food data periodically: `python export_foods.py`
   - Store JSON backup locally
   - Can quickly rebuild Upstash index from backup

2. **Token Compromise Response**
   - Immediately rotate token in Upstash dashboard
   - Update .env with new token
   - Redeploy application
   - Review access logs for suspicious activity

3. **Data Loss Prevention**
   - Maintain foods.json as source of truth
   - Can always upsert fresh data
   - Upstash provides backup options (paid)

---

## 9. Embedding Model Details

### 9.1 Selected Model: BAAI/bge-large-en-v1.5

**Specifications:**
```
Model Name:      BAAI/bge-large-en-v1.5
Dimensions:      1024
Max Tokens:      512
MTEB Score:      64.23
Training Data:   Large corpus of English text
Optimization:    Retrieval & semantic similarity
```

**Why This Model:**
- ✅ 1024 dimensions matches current mxbai-embed-large
- ✅ High MTEB score (64.23) - excellent for retrieval
- ✅ 512 token limit covers our food descriptions (most <200 tokens)
- ✅ Recommended for general-purpose search
- ✅ No retraining needed - ready to use

### 9.2 Model Comparison

| Model | Dim | Tokens | MTEB | Best For |
|-------|-----|--------|------|----------|
| BAAI/bge-small | 384 | 512 | 62.17 | Speed-focused, low latency |
| BAAI/bge-base | 768 | 512 | 63.55 | Balanced accuracy/speed |
| BAAI/bge-large | 1024 | 512 | 64.23 | **Accuracy-focused (Our Choice)** |
| BAAI/bge-m3 | 1024 | 8192 | 64.94 | Long documents, multilingual |

### 9.3 Embedding Process

**No Code Changes Needed:**
```python
# Before (Manual)
text = "Tandoori chicken is chicken marinated in yogurt..."
embedding = get_embedding(text)  # Calls Ollama API
vector_index.add(documents=[text], embeddings=[embedding])

# After (Automatic)
text = "Tandoori chicken is chicken marinated in yogurt..."
vector_index.upsert(id="12", text=text)  # Upstash handles embedding
```

Upstash automatically:
1. Tokenizes the input text (512 tokens max)
2. Embeds using selected model (BAAI/bge-large)
3. Stores 1024-dimensional vector
4. Indexes for similarity search

### 9.4 Embedding Compatibility

**Original System:**
- mxbai-embed-large (Ollama)
- 1024 dimensions
- Cosine similarity

**New System:**
- BAAI/bge-large-en-v1.5 (Upstash)
- 1024 dimensions
- Cosine similarity

**Compatibility:** ✅ Excellent
- Same dimensions (1024) - models can interchange
- Both use cosine similarity
- Both trained on general English text
- Similar quality (MTEB: 64.68 vs 64.23)

---

## 10. Implementation Timeline & Rollback Plan

### 10.1 Implementation Phases

**Phase 1: Preparation (1 hour)**
- [ ] Obtain Upstash credentials
- [ ] Update .env file
- [ ] Install dependencies
- [ ] Backup foods.json

**Phase 2: Development (2-3 hours)**
- [ ] Create new code branch
- [ ] Implement Upstash Vector client
- [ ] Update data loading logic
- [ ] Update query function
- [ ] Update error handling

**Phase 3: Testing (1-2 hours)**
- [ ] Unit test data upsert
- [ ] Unit test query function
- [ ] Integration test full RAG flow
- [ ] Test error scenarios
- [ ] Performance benchmarking

**Phase 4: Deployment (30 mins)**
- [ ] Code review
- [ ] Merge to main branch
- [ ] Update README
- [ ] Deploy to production
- [ ] Monitor for issues

### 10.2 Rollback Plan

If issues arise:

1. **Immediate Rollback (< 5 minutes)**
   ```bash
   git revert <commit-hash>
   python rag_run.py  # Falls back to ChromaDB
   ```

2. **Data Recovery**
   - Upstash data is in cloud (safe)
   - ChromaDB data still on disk (safe)
   - foods.json is source of truth
   - Can recreate either database

3. **Hybrid Approach (if needed)**
   ```python
   # Keep both databases temporarily
   try:
       results = vector_index.query(data=question, top_k=3)
   except:
       logger.warning("Upstash failed, falling back to ChromaDB")
       results = collection.query(query_embeddings=[emb], n_results=3)
   ```

### 10.3 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| API credentials invalid | Low | High | Validate before deployment |
| Rate limiting | Low | Medium | Implement retry logic |
| Network outage | Low | High | Fallback to ChromaDB temp |
| Data loss | Very Low | High | Backup foods.json |
| Embedding quality drop | Very Low | Low | Same model quality |

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# test_upstash_integration.py

import unittest
from unittest.mock import patch, MagicMock
from rag_run import rag_query, safe_upsert_foods

class TestUpstashIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_query = "What is tandoori chicken?"
        self.test_foods = [{
            "id": "1",
            "text": "Tandoori chicken...",
            "region": "Punjab",
            "type": "Main Course"
        }]
    
    def test_upsert_valid_data(self):
        """Test upserting valid food data"""
        result = safe_upsert_foods(self.test_foods)
        self.assertTrue(result)
    
    def test_upsert_empty_data(self):
        """Test upserting empty data"""
        result = safe_upsert_foods([])
        self.assertFalse(result)
    
    def test_query_returns_results(self):
        """Test that queries return valid results"""
        results = rag_query(self.test_query)
        self.assertIsNotNone(results)
        self.assertIn("sources", results)
        self.assertIn("answer", results)
    
    def test_query_error_handling(self):
        """Test error handling for failed queries"""
        with patch('upstash_vector.Index.query', side_effect=Exception("API Error")):
            results = rag_query(self.test_query)
            self.assertIsNone(results)

if __name__ == '__main__':
    unittest.main()
```

### 11.2 Integration Tests

```python
# test_rag_flow.py

def test_complete_rag_flow():
    """Test complete RAG pipeline with Upstash"""
    # 1. Load and upsert data
    with open("foods.json") as f:
        foods = json.load(f)
    assert safe_upsert_foods(foods), "Failed to upsert data"
    
    # 2. Query and get results
    query = "Which Indian dish uses chickpeas?"
    results = rag_query(query)
    assert results is not None, "Query returned None"
    assert len(results["sources"]) > 0, "No sources retrieved"
    assert len(results["answer"]) > 0, "No answer generated"
    
    # 3. Verify results quality
    assert "chole" in results["answer"].lower(), "Incorrect answer"
    
    print("✅ Complete RAG flow test passed")

def test_query_performance():
    """Measure query performance"""
    import time
    query = "Tell me about Pad Thai"
    
    start = time.time()
    results = rag_query(query)
    elapsed = time.time() - start
    
    print(f"Query time: {elapsed:.2f}s")
    assert elapsed < 120, "Query took too long"  # 2 min timeout
```

### 11.3 Performance Benchmarks

```python
# benchmark.py

import time
from statistics import mean, stdev

def benchmark_queries(queries, num_runs=3):
    times = []
    for _ in range(num_runs):
        for query in queries:
            start = time.time()
            rag_query(query)
            times.append(time.time() - start)
    
    return {
        "mean": mean(times),
        "stdev": stdev(times),
        "min": min(times),
        "max": max(times),
    }

if __name__ == "__main__":
    test_queries = [
        "What is tandoori chicken?",
        "Which foods are vegetarian?",
        "Tell me about Japanese cuisine",
    ]
    
    stats = benchmark_queries(test_queries)
    print(f"Query Performance:")
    print(f"  Mean: {stats['mean']:.2f}s")
    print(f"  Stdev: {stats['stdev']:.2f}s")
    print(f"  Range: {stats['min']:.2f}s - {stats['max']:.2f}s")
```

---

## 12. Migration Execution Guide

### 12.1 Step-by-Step Implementation

**Step 1: Create Development Branch**
```bash
git checkout -b feature/upstash-migration
```

**Step 2: Update Environmental Setup**
```bash
# Update .env
# Add UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN

# Install new dependencies
pip install upstash-vector
pip uninstall chromadb  # Or keep for fallback
```

**Step 3: Create New Version of rag_run.py**

Create `rag_run_upstash.py` alongside existing for comparison:

```python
# rag_run_upstash.py

import os
import json
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from dotenv import load_dotenv
from upstash_vector import Index

# Load environment variables
load_dotenv()

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, "foods.json")
LLM_MODEL = "llama3.2"

# Upstash Vector client
try:
    vector_index = Index(
        url=os.getenv("UPSTASH_VECTOR_REST_URL"),
        token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
    )
    print("[OK] Connected to Upstash Vector")
except Exception as e:
    print(f"[ERROR] Failed to connect to Upstash Vector: {e}")
    vector_index = None

# Load food data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# Initialize vector database
def initialize_vector_db():
    """Upsert all food items to Upstash Vector"""
    if not vector_index:
        print("[ERROR] Vector database not available")
        return False
    
    print(f"[INFO] Preparing {len(food_data)} food items...")
    
    vectors_to_upsert = []
    for item in food_data:
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."
        
        vectors_to_upsert.append({
            "id": item["id"],
            "text": enriched_text,
            "metadata": {
                "original_id": item["id"],
                "region": item.get("region", "Unknown"),
                "type": item.get("type", "Unknown"),
            }
        })
    
    try:
        vector_index.upsert(vectors_to_upsert)
        print(f"[OK] Upserted {len(vectors_to_upsert)} items to Upstash Vector")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to upsert to Upstash Vector: {e}")
        return False

# RAG query function
def rag_query(question, gui_callback=None):
    """Query RAG system using Upstash Vector"""
    try:
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
        sources_text = "[SOURCES]\n"
        for i, (doc, score) in enumerate(zip(top_docs, top_scores)):
            sources_text += f"\n[{i + 1}] (Relevance: {score:.2f})\n    {doc}\n"
        
        if gui_callback:
            gui_callback("sources", sources_text)
        
        # Step 4: Build prompt from context
        context = "\n".join(top_docs)
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        # Step 5: Generate answer with Ollama (streaming)
        try:
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": True
            }, stream=True, timeout=60)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise Exception("ERROR: Cannot connect to Ollama. Please start Ollama first.")
        except requests.exceptions.Timeout:
            raise Exception("ERROR: Ollama request timed out.")
        except Exception as e:
            raise Exception(f"ERROR: Failed to generate answer: {str(e)}")

        # Step 6: Stream response
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
    
    except Exception as e:
        error_msg = f"[ERROR] {str(e)}"
        if gui_callback:
            gui_callback("error", error_msg)
        return ""

# Tkinter GUI (same as before, no changes needed)
class RAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Food Q&A")
        self.root.geometry("1000x700")
        
        # Question input
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(input_frame, text="Question:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.question_input = tk.Entry(input_frame, font=("Arial", 10))
        self.question_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.question_input.bind("<Return>", lambda e: self.ask_question())
        
        self.ask_btn = tk.Button(input_frame, text="Ask", command=self.ask_question, fg="white", bg="green")
        self.ask_btn.pack(side=tk.LEFT, padx=5)
        
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
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, "[Generating answer...]\n")
        
        elif update_type == "answer_update":
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.insert(tk.END, content)
            self.answer_text.see(tk.END)
            self.answer_text.config(state=tk.DISABLED)
        
        elif update_type == "error":
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
        self.sources_text.config(state=tk.NORMAL)
        self.sources_text.delete(1.0, tk.END)
        self.sources_text.insert(tk.END, "[Retrieving sources...]\n")
        self.sources_text.config(state=tk.DISABLED)
        
        # Run in background thread
        def query_thread():
            try:
                rag_query(question, gui_callback=self.update_gui)
            finally:
                self.querying = False
                self.ask_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=query_thread, daemon=True).start()

# Main execution
if __name__ == "__main__":
    # Initialize vector database
    if not initialize_vector_db():
        print("[WARN] Vector database initialization failed")
    
    root = tk.Tk()
    gui = RAGUI(root)
    root.mainloop()
```

**Step 4: Test the new implementation**
```bash
python rag_run_upstash.py
```

**Step 5: Replace original file**
```bash
mv rag_run.py rag_run_chromadb_backup.py
mv rag_run_upstash.py rag_run.py
```

**Step 6: Test, commit, and push**
```bash
# Test
python rag_run.py

# Commit
git add rag_run.py
git commit -m "Migrate to Upstash Vector Database"

# Push
git push origin feature/upstash-migration

# Create PR for review, merge, and deploy
```

### 12.2 Validation Checklist

- [ ] All 90+ food items successfully upserted
- [ ] Sample queries return relevant results
- [ ] Answer generation working correctly
- [ ] GUI displays sources and answers properly
- [ ] Error handling for API failures
- [ ] Performance metrics acceptable (<120s total per query)
- [ ] No data loss or corruption
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Rollback plan documented

---

## 13. Post-Migration Tasks

### 13.1 Monitoring

```python
# Create monitoring log
import logging
from datetime import datetime

logging.basicConfig(
    filename='rag_usage.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_query(question, success, latency):
    logging.info(f"Query: '{question[:50]}...' | Success: {success} | Latency: {latency:.2f}s")
```

### 13.2 Documentation Updates

Update README.md:
- [ ] Change "Using ChromaDB" to "Using Upstash Vector"
- [ ] Update installation instructions
- [ ] Remove chroma_db setup steps
- [ ] Add Upstash setup requirements
- [ ] Update architecture diagram
- [ ] Add Upstash credentials section

### 13.3 Cleanup

```bash
# After successful migration
rm -rf chroma_db/          # No longer needed
rm rag_run_chromadb_backup.py  # Keep for 1 month, then delete
```

---

## 14. Decision Matrix

| Feature | ChromaDB | Upstash | Winner |
|---------|----------|---------|--------|
| Local control | ✅ | ❌ | ChromaDB |
| Scalability | ❌ | ✅ | Upstash |
| Zero setup | ❌ | ✅ | Upstash |
| Automatic embedding | ❌ | ✅ | Upstash |
| Privacy (no cloud) | ✅ | ❌ | ChromaDB |
| Cost (local dev) | ✅ | ❌ | ChromaDB |
| Cost (production) | ❌ | ✅ | Upstash |
| Query speed | ✅ | ❌ | ChromaDB |
| Managed service | ❌ | ✅ | Upstash |
| Data ownership | ✅ | ❌ | ChromaDB |
| **Overall for this project** | **Dev** | **Prod** | **Hybrid** |

### Recommendation

- **For Development**: Keep ChromaDB (free, no cloud costs)
- **For Production**: Switch to Upstash (scalable, managed, minimal cost)
- **For Hobby Projects**: ChromaDB (sufficient, no monthly fees)
- **For Deployed Apps**: Upstash (always available, no local infra)

---

## 15. Conclusion

The migration from ChromaDB to Upstash Vector is a **strategic shift from local-first to cloud-first architecture**. While adding minimal cost, it significantly simplifies the system by:

1. **Eliminating manual embedding generation** - Upstash handles vectorization
2. **Removing local infrastructure** - No persistent disk database needed
3. **Improving scalability** - Cloud-hosted with unlimited growth potential
4. **Reducing operational complexity** - Managed service with reliability guarantees

**This design document provides a complete blueprint for implementation, testing, and deployment.**

The migration is **backward compatible** - if needed, fallback to ChromaDB is always possible.

---

## Appendix: Quick Reference

### Environment Setup
```env
UPSTASH_VECTOR_REST_URL="https://your-index.upstash.io"
UPSTASH_VECTOR_REST_TOKEN="your-secret-token"
```

### Key Code Changes

**Upsert:**
```python
vector_index.upsert([{
    "id": "1",
    "text": "Biryani is...",
    "metadata": {"region": "Hyderabad"}
}])
```

**Query:**
```python
results = vector_index.query(data=question, top_k=3)
```

### Installation
```bash
pip install upstash-vector
```

### Testing
```bash
pytest test_upstash_integration.py -v
```

---

**Document Version:** 1.0  
**Last Updated:** February 8, 2026  
**Status:** Ready for Implementation

