"""
Chat router - RAG query endpoint
Interfaces with StudyRAGSystem for question answering
"""
from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user
from models.requests import ChatRequest
from models.responses import ChatResponse
from services.StudyRAGSystem import StudyRAGSystem
from langchain_core.messages import HumanMessage
import os

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Initialize RAG system (cached per worker process)
_rag_system = None

def get_rag_system() -> StudyRAGSystem:
    """Get or initialize RAG system (singleton per worker)"""
    global _rag_system
    if _rag_system is None:
        _rag_system = StudyRAGSystem(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            chroma_persist_dir="./vectorstore",
            collection_name="study_materials"
        )
    return _rag_system

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Send a question to the RAG system.
    
    The system will:
    1. Search user's ingested textbooks (filtered by user_id)
    2. Apply optional scope filters (semester/subject/books)
    3. Generate answer using GPT-4o with retrieved context
    
    Returns:
    - answer: Generated response
    - sources: List of textbook chunks used
    - metadata: Semester/subject/book info for each source
    """
    try:
        rag_system = get_rag_system()
        
        # Build scope for retrieval
        scope = {}
        if request.semester:
            scope["semester"] = request.semester
        if request.subject:
            scope["subject"] = request.subject
        if request.books:
            scope["books"] = request.books
        
        # Add user_id to scope for multi-user isolation
        # TODO: Update ChromaDB to filter by user_id metadata
        scope["user_id"] = user_id
        
        # Create LangChain message
        message = HumanMessage(content=request.question)
        
        # Get RAG agent
        agent = rag_system.build_study_agent(scope=scope)
        
        # Invoke agent
        response = agent.invoke({
            "messages": [message]
        })
        
        # Extract answer from response
        answer = response["messages"][-1].content
        
        # Extract sources (if available)
        sources = []
        if "retrieved_docs" in response:
            for doc in response["retrieved_docs"]:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            metadata={
                "user_id": user_id,
                "scope": scope,
                "model": "gpt-4o"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat query failed: {str(e)}"
        )

@router.get("/history")
async def get_chat_history(
    user_id: str = Depends(get_current_user)
):
    """
    Get user's chat history (if implemented).
    
    TODO: Store chat messages in Supabase usage_logs table
    """
    return {
        "message": "Chat history not yet implemented",
        "user_id": user_id
    }

@router.post("/clear-context")
async def clear_context(
    user_id: str = Depends(get_current_user)
):
    """
    Clear chat context/memory for user.
    
    Useful if user wants to start fresh conversation.
    """
    # TODO: Implement conversation memory per user
    return {
        "message": "Context cleared",
        "user_id": user_id
    }
