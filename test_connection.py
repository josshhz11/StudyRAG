# test_s3_connection.py
from storage_adapter import S3StorageAdapter
import os
from dotenv import load_dotenv

load_dotenv()

try:
    s3 = S3StorageAdapter()
    print("✅ S3 connection successful!")
    
    # List existing files
    pdfs = s3.list_pdfs()
    print(f"Found {len(pdfs)} PDFs in bucket")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")