# storage_adapter.py - NEW FILE
"""
Storage adapter for StudyRAG - supports both local filesystem and AWS S3
"""
import os
import boto3
import io
from pathlib import Path
from typing import List, Dict, Optional, BinaryIO
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()


class StorageAdapter(ABC):
    """Abstract base class for storage operations"""
    
    @abstractmethod
    def list_pdfs(self, prefix: str = "") -> List[Dict]:
        """List all PDF files with their metadata"""
        pass
    
    @abstractmethod
    def upload_file(self, file_data: BinaryIO, s3_key: str) -> bool:
        """Upload a file to storage"""
        pass
    
    @abstractmethod
    def download_file(self, s3_key: str) -> bytes:
        """Download a file from storage"""
        pass
    
    @abstractmethod
    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from storage"""
        pass
    
    @abstractmethod
    def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists"""
        pass


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage adapter"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def list_pdfs(self, prefix: str = "") -> List[Dict]:
        """
        List all PDFs in the local directory structure.
        Returns list of dicts with structure: semester/subject/book/filename.pdf
        """
        pdfs = []
        search_dir = self.base_dir / prefix if prefix else self.base_dir
        
        if not search_dir.exists():
            return pdfs
        
        # Scan: semester/subject/book/*.pdf
        for semester_dir in search_dir.iterdir():
            if not semester_dir.is_dir():
                continue
            
            for subject_dir in semester_dir.iterdir():
                if not subject_dir.is_dir():
                    continue
                
                for book_dir in subject_dir.iterdir():
                    if not book_dir.is_dir():
                        continue
                    
                    for pdf_file in book_dir.glob("*.pdf"):
                        relative_path = pdf_file.relative_to(self.base_dir)
                        pdfs.append({
                            'key': str(relative_path).replace('\\', '/'),
                            'semester': semester_dir.name,
                            'subject': subject_dir.name,
                            'book_id': book_dir.name,
                            'book_title': pdf_file.stem,
                            'size': pdf_file.stat().st_size,
                            'local_path': str(pdf_file)
                        })
        
        return pdfs
    
    def upload_file(self, file_data: BinaryIO, key: str) -> bool:
        """Upload (write) a file to local storage"""
        try:
            file_path = self.base_dir / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(file_data.read())
            return True
        except Exception as e:
            print(f"Error uploading to local storage: {e}")
            return False
    
    def download_file(self, key: str) -> bytes:
        """Download (read) a file from local storage"""
        file_path = self.base_dir / key
        with open(file_path, 'rb') as f:
            return f.read()
    
    def delete_file(self, key: str) -> bool:
        """Delete a file from local storage"""
        try:
            file_path = self.base_dir / key
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting from local storage: {e}")
            return False
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists locally"""
        return (self.base_dir / key).exists()


class S3StorageAdapter(StorageAdapter):
    """AWS S3 storage adapter"""
    
    def __init__(self, bucket_name: Optional[str] = None, user_id: Optional[str] = None):
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        self.user_id = user_id or "default_user"  # For multi-user support later
        self.region = os.getenv('AWS_REGION', 'us-east-2')
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region
        )
        
        print(f"✅ Connected to S3 bucket: {self.bucket_name}")
    
    def _get_user_prefix(self) -> str:
        """Get the S3 prefix for this user"""
        return f"users/{self.user_id}/raw_data/"
    
    def list_pdfs(self, prefix: str = "") -> List[Dict]:
        """
        List all PDFs in S3 bucket under user's prefix.
        Expected structure: users/{user_id}/raw_data/semester/subject/book/filename.pdf
        Returns empty list if user folder doesn't exist (not created yet).
        """
        pdfs = []
        full_prefix = self._get_user_prefix() + prefix
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=full_prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    # No objects found - user folder doesn't exist yet (first time user)
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    if not key.endswith('.pdf'):
                        continue
                    
                    # Parse structure: users/{user_id}/raw_data/semester/subject/book/filename.pdf
                    parts = key.replace(full_prefix, '').split('/')
                    if len(parts) >= 4:
                        semester, subject, book_id, filename = parts[0], parts[1], parts[2], parts[3]
                        pdfs.append({
                            'key': key,
                            'semester': semester,
                            'subject': subject,
                            'book_id': book_id,
                            'book_title': Path(filename).stem,
                            'size': obj['Size'],
                            's3_url': f"s3://{self.bucket_name}/{key}"
                        })
        
        except Exception as e:
            print(f"Error listing S3 objects: {e}")
        
        return pdfs
    
    def upload_file(self, file_data: BinaryIO, key: str) -> bool:
        """
        Upload a file to S3.
        
        Note: key should be the full S3 path including users/{user_id}/raw_data/...
        This creates the folder structure on-demand (S3 creates paths automatically).
        """
        try:
            # Key already includes full path from backend, don't prepend user prefix
            self.s3_client.upload_fileobj(file_data, self.bucket_name, key)
            print(f"✅ Uploaded to S3: {key}")
            return True
        except Exception as e:
            print(f"❌ Error uploading to S3: {e}")
            return False
    
    def download_file(self, key: str) -> bytes:
        """Download a file from S3 into memory"""
        buffer = io.BytesIO()
        self.s3_client.download_fileobj(self.bucket_name, key, buffer)
        buffer.seek(0)
        return buffer.read()
    
    def download_to_temp(self, key: str, temp_path: str) -> bool:
        """Download a file from S3 to a temporary local path"""
        try:
            self.s3_client.download_file(self.bucket_name, key, temp_path)
            return True
        except Exception as e:
            print(f"Error downloading from S3: {e}")
            return False
    
    def delete_file(self, key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            print(f"Error deleting from S3: {e}")
            return False
    
    def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except:
            return False


def get_storage_adapter(storage_mode: Optional[str] = None, user_id: Optional[str] = None) -> StorageAdapter:
    """
    Factory function to get the appropriate storage adapter.
    
    Args:
        storage_mode: "local" or "s3". If None, reads from STORAGE_MODE env var.
        user_id: User identifier for S3 multi-user support
    
    Returns:
        StorageAdapter instance
    """
    mode = storage_mode or os.getenv('STORAGE_MODE', 'local')
    
    if mode == 's3':
        return S3StorageAdapter(user_id=user_id)
    else:
        # Default to local storage
        base_dir = Path(__file__).parent / "raw_data"
        return LocalStorageAdapter(base_dir)