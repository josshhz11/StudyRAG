"""
FastAPI backend configuration and settings
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Info
    app_name: str = "StudyRAG API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # AWS S3
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-2")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "")
    storage_mode: str = os.getenv("STORAGE_MODE", "s3")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # CORS
    cors_origins: list = [
        "http://localhost:8501",  # Streamlit default
        "http://localhost:3000",  # React default
        "https://*.streamlit.app",  # Streamlit Cloud
    ]
    
    # Vector DB
    vectorstore_dir: str = "./vectorstore"
    collection_name: str = "study_materials"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
