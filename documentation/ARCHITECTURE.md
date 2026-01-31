# StudyRAG System Architecture

## 🎯 Final Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Streamlit → React)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Chat Page    │  │ Upload Page  │  │ Library Browser     │   │
│  │ (Q&A)        │  │ (Drag-Drop)  │  │ (Folder Tree View)  │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│         │                  │                     │               │
│         └──────────────────┼─────────────────────┘               │
│                            │ HTTP REST API                       │
└────────────────────────────┼─────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI - Async)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Endpoints:                                           │   │
│  │  • POST /api/upload      - Upload PDF to S3              │   │
│  │  • GET  /api/files       - List user's files/folders     │   │
│  │  • POST /api/move        - Move/reorganize files         │   │
│  │  • DELETE /api/files/{id} - Delete file                  │   │
│  │  • POST /api/ingest      - Trigger ingestion job         │   │
│  │  • POST /api/chat        - Query RAG agent               │   │
│  │  • GET  /api/health      - Health check                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                                                         │
│         ├────────────► Background Task Queue (Celery/RQ)         │
│         │               - Async PDF ingestion                    │
│         │               - Embedding generation                   │
│         │                                                         │
└─────────┼─────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                             │
│  ┌──────────────────┐              ┌─────────────────────────┐  │
│  │   AWS S3         │              │   ChromaDB              │  │
│  │                  │              │   (Vector Store)        │  │
│  │  users/          │              │                         │  │
│  │   └─{user_id}/   │              │  Collections:           │  │
│  │      └─raw_data/ │              │   • user_{id}_docs      │  │
│  │         └─Y3S2/  │──ingestion──►│                         │  │
│  │            └─NLP/│              │  Metadata filters:      │  │
│  │               └─*│              │   • user_id             │  │
│  │                  │              │   • semester            │  │
│  │  PDFs stored     │              │   • subject             │  │
│  │  with metadata   │              │   • book_id             │  │
│  └──────────────────┘              └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Current State → Target State Migration

### **Phase 1: File System Setup (CURRENT FOCUS)**

#### What You Have Now:
- ✅ `storage_adapter.py` - Abstraction for local/S3 storage
- ✅ S3 credentials configured in `.env`
- ✅ S3 connection tested and working
- ✅ `StudyRAGSystem.py` - Monolithic system with ingestion + agent
- ✅ Basic Streamlit UI (chat + upload pages)

#### What We Need to Build:
1. **Enhanced S3 Upload Page**
   - Drag-and-drop file upload
   - Folder selector (semester/subject/book)
   - Visual file browser with folder tree
   - File management (move, delete, rename)

2. **Storage Layer Completion**
   - Test file upload to S3
   - Verify folder structure
   - Implement file operations (move, delete)

---

### **Phase 2: Backend Separation (NEXT)**

#### Current Problem:
- `StudyRAGSystem.py` mixes:
  - Business logic (ingestion, RAG agent)
  - CLI interface
  - Direct file system access
  - No API layer

#### Target Solution:
```
backend/
├── main.py                 # FastAPI app entry point
├── routers/
│   ├── upload.py          # File upload endpoints
│   ├── files.py           # File management endpoints
│   ├── chat.py            # RAG chat endpoints
│   └── ingestion.py       # Ingestion trigger endpoints
├── services/
│   ├── storage_service.py # Storage adapter wrapper
│   ├── rag_service.py     # LangGraph agent wrapper
│   └── ingestion_service.py # PDF processing
├── models/
│   ├── request_models.py  # Pydantic request models
│   └── response_models.py # Pydantic response models
└── core/
    ├── config.py          # Settings (S3, vector DB, etc.)
    └── dependencies.py    # FastAPI dependencies
```

---

### **Phase 3: Async Ingestion (FUTURE)**

#### Components:
1. **S3 Event Triggers**
   - S3 → EventBridge → Lambda → SQS → Backend
   - Or: S3 upload → API endpoint → Celery task

2. **Background Task Queue**
   - Celery + Redis (or RQ for simplicity)
   - Job states: `pending`, `processing`, `completed`, `failed`
   - Progress tracking via WebSocket or polling

3. **Job Status API**
   ```
   POST /api/ingest/{file_id}  → Returns job_id
   GET  /api/jobs/{job_id}     → Returns status, progress
   ```

---

## 📊 Data Flow Diagrams

### **Current: Monolithic System**
```
User → Streamlit UI
         ↓ (direct call)
      StudyRAGSystem.py
         ↓
   IngestionPipeline.scan_library()
         ↓
   storage_adapter.list_pdfs()
         ↓
   Local FS / S3
```

### **Target: API-Based System**
```
User → Streamlit UI
         ↓ (HTTP POST)
      FastAPI Backend
         ↓ (async)
   StorageService.upload_file()
         ↓
      AWS S3
         
User → Streamlit Chat
         ↓ (HTTP POST /api/chat)
      FastAPI Backend
         ↓
   RAGService.query()
         ↓ (retrieval)
      ChromaDB
         ↓ (LLM)
      OpenAI API
```

---

## 🛠️ Implementation Phases

### **Phase 1: File System (Week 1)**
- [x] S3 connection setup
- [x] storage_adapter.py implementation
- [ ] Enhanced S3 Upload UI
  - [ ] Drag-and-drop zone
  - [ ] Folder tree browser
  - [ ] File operations (move, delete)
- [ ] Test file upload/download from S3
- [ ] Verify folder structure in S3

### **Phase 2: Backend API (Week 2)**
- [ ] Create FastAPI project structure
- [ ] Implement upload endpoint
- [ ] Implement file listing endpoint
- [ ] Implement chat endpoint (wraps RAG agent)
- [ ] Connect Streamlit UI to API
- [ ] Remove direct StudyRAGSystem calls from UI

### **Phase 3: Async Ingestion (Week 3)**
- [ ] Add Celery for background tasks
- [ ] Implement ingestion job queue
- [ ] Add job status tracking
- [ ] Update UI with progress indicators
- [ ] Optional: S3 event triggers

### **Phase 4: Multi-User (Week 4)**
- [ ] Add authentication (Streamlit auth or Auth0)
- [ ] User ID in all API calls
- [ ] S3 path prefixing by user_id
- [ ] ChromaDB filtering by user_id
- [ ] User isolation testing

---

## 🔑 Key Architectural Decisions

### **1. Storage: AWS S3**
- **Why**: Scalable, durable (11 nines), cost-effective
- **Structure**: `users/{user_id}/raw_data/semester/subject/book/file.pdf`
- **Access**: Pre-signed URLs for direct uploads (future optimization)

### **2. Vector DB: ChromaDB**
- **Why**: Simple, self-hosted, good for prototyping
- **Approach**: Shared DB with metadata filtering by `user_id`
- **Alternative**: Qdrant Cloud (production-ready, $70/mo starter)

### **3. Backend: FastAPI (Async)**
- **Why**: Fast, async, auto-docs, type-safe
- **Async benefits**: Handle multiple uploads/queries concurrently
- **CORS**: Enable for Streamlit (or future React app)

### **4. Frontend: Streamlit → React**
- **Now**: Streamlit (rapid prototyping, 1 week to MVP)
- **Later**: Next.js + React (production UI, better UX)
- **Transition**: API-first design makes migration easy

---

## 📂 File Organization

### **Current (Monolithic)**
```
StudyRAG/
├── StudyRAGSystem.py      # Everything in one file
├── streamlit_app.py       # Main chat UI
├── pages/
│   ├── 1_Add_Textbooks.py
│   └── 2_S3_Upload.py
├── storage_adapter.py     # NEW: Storage abstraction
├── raw_data/              # Local files (deprecated for S3)
├── vectorstore/           # ChromaDB storage
└── cache/
```

### **Target (API-Based)**
```
StudyRAG/
├── frontend/
│   ├── streamlit_app.py
│   └── pages/
│       ├── 1_Chat.py
│       ├── 2_Upload.py
│       └── 3_Library.py
│
├── backend/
│   ├── main.py            # FastAPI app
│   ├── routers/
│   ├── services/
│   ├── models/
│   └── core/
│
├── shared/
│   └── storage_adapter.py # Used by both frontend & backend
│
├── vectorstore/           # ChromaDB storage
└── cache/
```

---

## 🚀 Next Steps (Immediate)

1. **Test S3 Upload** ✅ (Just completed!)
2. **Upload a test PDF to S3**
3. **Build enhanced S3 Upload UI** (drag-drop, folder tree)
4. **Test file operations** (list, move, delete)
5. **Verify ingestion works with S3 files**

Once Phase 1 is solid, we'll architect the FastAPI backend.

---

## 💡 Design Principles

1. **API-First**: All business logic behind REST endpoints
2. **Separation of Concerns**: Frontend only does UI, backend handles logic
3. **Storage Abstraction**: Easy to switch between local/S3/other
4. **User Isolation**: All data scoped by user_id
5. **Async by Default**: Handle concurrent operations efficiently
6. **Type Safety**: Pydantic models for all API I/O

---

## 📝 Notes

- **ChromaDB Limitation**: Max ~10K collections, so use shared DB with filters
- **S3 Costs**: ~$0.023/GB/month, negligible for small-scale (<$1/mo for 100 users)
- **Embedding Costs**: OpenAI ~$0.0001/1K tokens (~$5-10 per 100 textbooks)
- **Compute**: FastAPI can run on $5/mo DigitalOcean droplet for MVP
