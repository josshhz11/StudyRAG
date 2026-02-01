# 🚀 StudyRAG Chat & RAG System Implementation Plan

## Current Issues & Immediate Fixes

### Issue 1: Frontend-Backend Mismatch
**Problem**: Frontend sends `question`, backend expects `query`  
**Fix**: Update ChatRequest model to accept `question`

### Issue 2: Chat Backend Not Implemented
**Problem**: chat.py references StudyRAGSystem but it's not properly integrated  
**Fix**: Implement proper RAG pipeline integration

### Issue 3: No Automatic Ingestion
**Problem**: Uploaded PDFs don't automatically get ingested into vector DB  
**Fix**: Implement S3 event trigger → Lambda → ingestion pipeline

---

## 🏗️ Architecture Overview

### Current Architecture
```
User → Next.js Frontend → FastAPI Backend → Supabase Auth
                                          → AWS S3 (file storage)
                                          → [NOT YET: Vector DB]
```

### Target Architecture
```
User → Next.js Frontend → FastAPI Backend → Supabase (auth + chat history)
                                          → AWS S3 (raw PDFs)
                                          ↓
                                     S3 Event Trigger
                                          ↓
                                    AWS Lambda / Background Worker
                                          ↓
                                    PDF Processing Pipeline:
                                    1. Extract text (PyPDF)
                                    2. Chunk documents
                                    3. Generate embeddings (OpenAI)
                                    4. Store in Vector DB (ChromaDB/Pinecone)
                                          ↓
                                    Vector DB ← Query for RAG
```

---

## 📊 Database Design

### Supabase Tables

#### 1. **user_profiles** (existing)
```sql
- user_id (uuid, PK)
- username (text)
- created_at (timestamp)
```

#### 2. **chat_sessions** (new)
```sql
CREATE TABLE chat_sessions (
    session_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    title text,  -- Auto-generated from first message
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
```

#### 3. **chat_messages** (new)
```sql
CREATE TABLE chat_messages (
    message_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id uuid REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    role text CHECK (role IN ('user', 'assistant', 'system')),
    content text NOT NULL,
    metadata jsonb,  -- Store sources, model used, tokens, etc.
    created_at timestamp DEFAULT now()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_user ON chat_messages(user_id);
```

#### 4. **document_ingestion_logs** (new)
```sql
CREATE TABLE document_ingestion_logs (
    log_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    s3_key text NOT NULL,
    semester text,
    subject text,
    book_id text,
    status text CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    chunks_count integer,
    error_message text,
    created_at timestamp DEFAULT now(),
    processed_at timestamp
);

CREATE INDEX idx_ingestion_user ON document_ingestion_logs(user_id);
CREATE INDEX idx_ingestion_status ON document_ingestion_logs(status);
```

#### 5. **vector_store_metadata** (new)
```sql
-- Track which documents are in the vector DB
CREATE TABLE vector_store_metadata (
    doc_id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    s3_key text NOT NULL,
    semester text,
    subject text,
    book_id text,
    chunk_count integer,
    collection_name text,  -- ChromaDB collection name
    indexed_at timestamp DEFAULT now()
);

CREATE INDEX idx_vector_user ON vector_store_metadata(user_id);
CREATE UNIQUE INDEX idx_vector_s3_key ON vector_store_metadata(user_id, s3_key);
```

---

## 🗄️ Vector Database Options

### Option 1: ChromaDB (Self-Hosted) ⭐ RECOMMENDED for MVP
**Pros:**
- ✅ Open source, free
- ✅ Easy to set up locally and in Docker
- ✅ Built-in filtering by metadata
- ✅ Good for development and moderate scale

**Cons:**
- ⚠️ Need to manage hosting
- ⚠️ Scaling requires manual work
- ⚠️ No built-in high availability

**Hosting Options:**
1. **AWS EC2** (t3.medium, $30/month)
   - Run ChromaDB in Docker container
   - Persistent EBS volume for data
   - Use EC2 security groups for access control

2. **AWS ECS/Fargate** (serverless)
   - Container-based deployment
   - Auto-scaling
   - ~$50-100/month depending on usage

3. **Railway/Render** (PaaS, easiest)
   - One-click Docker deployment
   - $10-20/month for small scale
   - Easy to set up

**Recommended for you**: Start with **Railway** for simplicity, migrate to AWS ECS later if needed.

---

### Option 2: Pinecone (Managed) 💰
**Pros:**
- ✅ Fully managed, no ops
- ✅ Scales automatically
- ✅ High availability built-in
- ✅ Good documentation

**Cons:**
- 💰 Expensive: Free tier (1M vectors), then $70/month minimum
- 🔒 Vendor lock-in

**When to use**: Production app with >10K users, need enterprise support

---

### Option 3: Weaviate Cloud (Managed)
**Pros:**
- ✅ Open source with managed option
- ✅ Good for complex queries
- ✅ Free tier available

**Cons:**
- ⚠️ More complex than ChromaDB
- ⚠️ Learning curve

---

## 🔧 Implementation Steps

### Phase 1: Fix Current Chat Functionality (1-2 hours)

#### Step 1.1: Update Request/Response Models
```python
# backend/models/requests.py
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)  # Changed from 'query'
    semester: Optional[str] = None
    subject: Optional[str] = None
    books: Optional[List[str]] = []
```

#### Step 1.2: Simplify StudyRAGSystem
- Remove CLI interface (keep only API methods)
- Remove redundant catalog/navigation logic
- Focus on: ingest_pdf(), query() methods

#### Step 1.3: Implement Basic Chat Endpoint
```python
# backend/routers/chat.py
@router.post("/query")
async def chat_query(request: ChatRequest, user_id: str = Depends(get_current_user)):
    # 1. Query vector DB with user_id filter
    # 2. Get relevant chunks
    # 3. Build context for LLM
    # 4. Generate answer
    # 5. Return response
    pass
```

---

### Phase 2: Set Up Vector Database (2-3 hours)

#### Option A: ChromaDB on Railway (Recommended for MVP)

**Step 2.1: Create Dockerfile for ChromaDB**
```dockerfile
FROM chromadb/chroma:latest
EXPOSE 8000
CMD ["uvicorn", "chromadb.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2.2: Deploy to Railway**
1. Create Railway account
2. New Project → Deploy from GitHub
3. Add Dockerfile
4. Get public URL: `https://your-chroma.railway.app`

**Step 2.3: Update Backend to Use Hosted ChromaDB**
```python
# backend/.env
CHROMA_HOST=https://your-chroma.railway.app
CHROMA_API_KEY=your-api-key  # If using auth
```

---

### Phase 3: Implement Automatic PDF Ingestion (3-4 hours)

#### Architecture Choice:

**Option A: Polling Worker (Simpler, Good for MVP)**
```python
# Run as background service alongside FastAPI
# Check document_ingestion_logs every 30 seconds
# Process files with status='pending'
```

**Option B: S3 Event + AWS Lambda (Production-grade)**
```
S3 Upload → Event Notification → Lambda Function → Process PDF
```

Let's implement **Option A** first (simpler):

**Step 3.1: Create Background Worker**
```python
# backend/workers/pdf_ingestion_worker.py
import asyncio
from services.StudyRAGSystem import ingest_pdf_to_vectordb

async def ingestion_worker():
    while True:
        # 1. Query document_ingestion_logs for status='pending'
        # 2. Download PDF from S3
        # 3. Chunk and embed
        # 4. Store in ChromaDB
        # 5. Update status='completed'
        await asyncio.sleep(30)  # Check every 30 seconds
```

**Step 3.2: Trigger on File Upload**
```python
# backend/routers/files.py
@router.post("/upload")
async def upload_file(...):
    # ... existing upload code ...
    
    # Create ingestion log entry
    supabase.table("document_ingestion_logs").insert({
        "user_id": user_id,
        "s3_key": s3_key,
        "semester": semester,
        "subject": subject,
        "book_id": book,
        "status": "pending"
    }).execute()
    
    return response
```

**Step 3.3: Run Worker Alongside FastAPI**
```python
# backend/main.py
from workers.pdf_ingestion_worker import ingestion_worker
import asyncio

@app.on_event("startup")
async def startup_event():
    # Start background ingestion worker
    asyncio.create_task(ingestion_worker())
```

---

### Phase 4: Implement Chat History (2-3 hours)

#### Step 4.1: Create Supabase Tables
Run SQL migrations (provided above)

#### Step 4.2: Update Chat Endpoint to Save Messages
```python
@router.post("/query")
async def chat_query(
    request: ChatRequest, 
    session_id: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    # Get or create session
    if not session_id:
        session = supabase.table("chat_sessions").insert({
            "user_id": user_id,
            "title": request.question[:50] + "..."  # First message as title
        }).execute()
        session_id = session.data[0]["session_id"]
    
    # Save user message
    supabase.table("chat_messages").insert({
        "session_id": session_id,
        "user_id": user_id,
        "role": "user",
        "content": request.question
    }).execute()
    
    # ... generate answer ...
    
    # Save assistant message
    supabase.table("chat_messages").insert({
        "session_id": session_id,
        "user_id": user_id,
        "role": "assistant",
        "content": answer,
        "metadata": {
            "sources": sources,
            "model": "gpt-4o",
            "tokens": token_count
        }
    }).execute()
    
    return response
```

#### Step 4.3: Add Chat History Endpoints
```python
@router.get("/sessions")
async def list_sessions(user_id: str = Depends(get_current_user)):
    # Get all user's chat sessions
    pass

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, user_id: str = Depends(get_current_user)):
    # Get all messages in a session
    pass

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user)):
    # Delete session and all messages
    pass
```

---

## 💾 Storing Chats in Relational DB

### Why Store in Postgres (Supabase)?

**Advantages:**
- ✅ ACID transactions
- ✅ Easy to query by user, session, date
- ✅ Join with user profiles
- ✅ Native JSON support for metadata
- ✅ Full-text search on messages
- ✅ Easy backups and exports

**Chat Structure:**
```
chat_sessions (one) → chat_messages (many)
```

**Querying Examples:**
```sql
-- Get user's recent sessions
SELECT * FROM chat_sessions 
WHERE user_id = $1 
ORDER BY updated_at DESC 
LIMIT 10;

-- Get all messages in a session
SELECT * FROM chat_messages 
WHERE session_id = $1 
ORDER BY created_at ASC;

-- Search messages
SELECT * FROM chat_messages 
WHERE user_id = $1 
AND content ILIKE '%natural language%'
ORDER BY created_at DESC;

-- Get usage stats
SELECT 
    DATE(created_at) as date,
    COUNT(*) as message_count,
    COUNT(DISTINCT session_id) as session_count
FROM chat_messages
WHERE user_id = $1
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## 📈 Scaling Considerations

### ChromaDB Scaling Strategy

**Stage 1: Single Instance (0-1K users)**
- Railway/Render hosted ChromaDB
- 1-2 GB RAM
- Cost: $10-20/month

**Stage 2: Optimized Single Instance (1K-10K users)**
- AWS EC2 t3.large (2 vCPU, 8GB RAM)
- Persistent EBS volume (100GB)
- CloudFront CDN for read queries
- Cost: $70-100/month

**Stage 3: Replicated Setup (10K-100K users)**
- Primary ChromaDB for writes
- Read replicas for queries
- AWS ECS/Fargate for auto-scaling
- S3 for backups
- Cost: $200-500/month

**Stage 4: Managed Solution (100K+ users)**
- Migrate to Pinecone or Weaviate Cloud
- Let them handle scaling
- Focus on application logic
- Cost: $500-2000/month

### Cost Breakdown (Estimated)

**MVP (0-100 users):**
- Supabase: Free
- AWS S3: $1-5/month
- ChromaDB (Railway): $10/month
- OpenAI API: $10-50/month (embeddings + completions)
- **Total: $21-65/month**

**Growth (100-1K users):**
- Supabase: $25/month
- AWS S3: $10-20/month
- ChromaDB (EC2): $70/month
- OpenAI API: $100-300/month
- **Total: $205-415/month**

**Scale (1K-10K users):**
- Supabase Pro: $125/month
- AWS (S3 + EC2 + ECS): $300/month
- OpenAI API: $500-2000/month
- **Total: $925-2425/month**

---

## 🎯 Implementation Priority

### Week 1: Get Chat Working
1. ✅ Fix frontend error handling (done above)
2. ⚠️ Simplify StudyRAGSystem.py
3. ⚠️ Implement basic chat endpoint with hardcoded test data
4. ⚠️ Test end-to-end chat flow

### Week 2: Vector DB Integration
1. Deploy ChromaDB to Railway
2. Implement PDF ingestion pipeline
3. Test query with real embeddings
4. Verify user isolation

### Week 3: Automatic Ingestion
1. Create Supabase tables
2. Implement background worker
3. Test automatic PDF→vectorDB flow
4. Monitor logs

### Week 4: Chat History
1. Implement session management
2. Save messages to Supabase
3. Add chat history UI in frontend
4. Add export/delete functionality

---

## 🚨 Important Considerations

### Security
- ✅ User isolation: Filter vector DB queries by `user_id` metadata
- ✅ Rate limiting: Prevent abuse of expensive OpenAI calls
- ✅ Input validation: Sanitize user queries
- ✅ Access control: Verify user owns the session before returning messages

### Performance
- ⚡ Cache embeddings: Don't re-embed same chunks
- ⚡ Batch processing: Ingest multiple PDFs in parallel
- ⚡ Lazy loading: Load chat messages on demand
- ⚡ Pagination: Limit message history queries

### Monitoring
- 📊 Track ingestion success rate
- 📊 Monitor OpenAI API costs
- 📊 Log query latency
- 📊 Alert on failures

---

## 🎉 Summary

**Immediate Action Items:**
1. Fix ChatRequest model (`question` not `query`)
2. Fix frontend error handling ✅ (already done)
3. Simplify StudyRAGSystem.py (I'll do this next)
4. Deploy ChromaDB to Railway
5. Implement basic chat with test data

**Long-term Roadmap:**
- Automatic PDF ingestion with background worker
- Chat history with Supabase
- Production ChromaDB deployment
- Monitoring and analytics

**Recommended Stack:**
- Vector DB: ChromaDB on Railway (start), migrate to Pinecone (scale)
- Chat Storage: Supabase Postgres with JSONB metadata
- Ingestion: Background worker (simple), AWS Lambda (production)

Let me know which part you want me to implement first! I recommend starting with fixing the chat endpoint to work with test data, then moving to vector DB integration.
