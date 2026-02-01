"""
Chat router - RAG query endpoint
Simple implementation for MVP - returns helpful message until vector DB is set up
"""
from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user
from models.requests import ChatRequest
from models.responses import ChatResponse

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Send a question to the RAG system.
    
    **Current Status**: Vector database not yet set up.
    This endpoint returns a helpful placeholder message.
    
    **Next Steps**:
    1. Deploy ChromaDB to Railway/Render
    2. Implement PDF ingestion pipeline
    3. Connect to vector store for actual RAG queries
    
    See RAG_IMPLEMENTATION_PLAN.md for full implementation details.
    """
    try:
        # TODO: Replace with actual RAG query when vector DB is ready
        # For now, return a helpful placeholder response
        
        # Build scope description
        scope_parts = []
        if request.semester:
            scope_parts.append(f"Semester: {request.semester}")
        if request.subject:
            scope_parts.append(f"Subject: {request.subject}")
        if request.books and len(request.books) > 0:
            scope_parts.append(f"Books: {', '.join(request.books)}")
        
        scope_desc = " | ".join(scope_parts) if scope_parts else "All materials"
        
        # Placeholder response
        answer = f"""👋 Hi! I'm your StudyRAG assistant.

**Your Question**: {request.question}
**Search Scope**: {scope_desc}

🚧 **System Status**: The RAG system is currently being set up. Here's what's happening:

1. ✅ Your PDF files are successfully stored in AWS S3
2. ✅ Authentication and file management working perfectly
3. 🔄 Vector database setup in progress
4. 🔄 PDF ingestion pipeline being implemented
5. ⏳ ChromaDB deployment pending

**What this means**: 
Once the vector database is deployed and your PDFs are ingested, I'll be able to:
- Search through your uploaded textbooks
- Find relevant passages based on your questions
- Provide accurate answers with source citations
- Filter by semester, subject, or specific books

**Next Steps**:
1. Deploy ChromaDB to Railway (10 minutes)
2. Run ingestion pipeline on your uploaded PDFs (5-10 minutes per PDF)
3. Start asking real questions!

Check `RAG_IMPLEMENTATION_PLAN.md` for technical details."""

        return ChatResponse(
            answer=answer,
            sources=[],
            metadata={
                "user_id": user_id,
                "scope": {
                    "semester": request.semester,
                    "subject": request.subject,
                    "books": request.books
                },
                "model": "placeholder",
                "status": "vector_db_not_ready"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat query failed: {str(e)}"
        )

@router.get("/status")
async def get_system_status(
    user_id: str = Depends(get_current_user)
):
    """
    Get RAG system status for current user.
    
    Returns information about:
    - Number of uploaded PDFs
    - Ingestion status
    - Vector DB connection
    - Available for queries
    """
    # TODO: Implement actual status checks
    return {
        "user_id": user_id,
        "vector_db_ready": False,
        "documents_ingested": 0,
        "documents_pending": 0,
        "ready_for_queries": False,
        "message": "Vector database not yet configured. See RAG_IMPLEMENTATION_PLAN.md"
    }

@router.get("/history")
async def get_chat_history(
    user_id: str = Depends(get_current_user)
):
    """
    Get user's chat history (not yet implemented).
    
    TODO: Query chat_messages table in Supabase
    """
    return {
        "message": "Chat history not yet implemented",
        "user_id": user_id,
        "sessions": []
    }
