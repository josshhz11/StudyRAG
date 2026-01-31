"""
FastAPI Backend for StudyRAG
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, files, chat
from core.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="StudyRAG API",
    description="Multi-user RAG system for textbook question-answering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["http://localhost:8501"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(auth.router)

# Root endpoint
@app.get("/")
async def root():
    """API root - health check"""
    return {
        "message": "StudyRAG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "studyrag-backend"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 StudyRAG API starting...")
    print("📝 API Docs: http://localhost:8000/docs")
    print("🔐 Auth endpoints: /auth/signup, /auth/login")
    print(f"🌐 CORS enabled for: {settings.cors_origins}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 StudyRAG API shutting down...")
