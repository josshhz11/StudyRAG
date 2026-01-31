"""
Files router - S3 upload, list, delete operations
User-scoped file management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import List
from core.dependencies import get_current_user
from models.responses import FileInfo, FilesResponse, MessageResponse
from services.storage_adapter import get_storage_adapter

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.get("", response_model=FilesResponse)
async def list_user_files(
    user_id: str = Depends(get_current_user)
):
    """
    List all PDFs in user's S3 directory.
    
    Returns files grouped by semester/subject/book structure.
    Only shows files owned by authenticated user.
    Returns empty list if user hasn't uploaded any files yet (folder not created).
    """
    try:
        # Get user-scoped storage adapter
        storage = get_storage_adapter(user_id=user_id)
        
        # List all PDFs in user's directory (returns [] if folder doesn't exist)
        pdf_files = storage.list_pdfs()
        
        # Convert to FileInfo objects
        files = []
        for pdf_path in pdf_files:
            # Extract metadata from path
            # Format: users/{user_id}/raw_data/semester/subject/book/file.pdf
            parts = pdf_path.split('/')
            
            if len(parts) >= 6:
                semester = parts[3]
                subject = parts[4]
                book = parts[5]
                filename = parts[-1]
                
                # Get file size if available
                try:
                    file_size = storage.get_file_size(pdf_path)
                except:
                    file_size = 0
                
                files.append(FileInfo(
                    file_key=pdf_path,
                    filename=filename,
                    semester=semester,
                    subject=subject,
                    book=book,
                    size_bytes=file_size,
                    uploaded_at=None  # Can add metadata later
                ))
        
        return FilesResponse(
            files=files,
            total_count=len(files)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.post("/upload", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    semester: str = "General",
    subject: str = "General",
    book: str = "General",
    user_id: str = Depends(get_current_user)
):
    """
    Upload a PDF file to user's S3 directory.
    
    File will be stored at: users/{user_id}/raw_data/{semester}/{subject}/{book}/{filename}
    Only the authenticated user can upload to their directory.
    Creates user folder structure on-demand (first upload creates folders).
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Get user-scoped storage adapter
        storage = get_storage_adapter(user_id=user_id)
        
        # Construct full S3 key (includes user folder)
        # This creates the folder structure automatically on first upload
        s3_key = f"users/{user_id}/raw_data/{semester}/{subject}/{book}/{file.filename}"
        
        # Read file content
        content = await file.read()
        
        # Upload to S3 (creates folders on-demand)
        import io
        storage.upload_file(io.BytesIO(content), s3_key)
        
        return MessageResponse(
            message=f"File '{file.filename}' uploaded successfully",
            details={
                "s3_key": s3_key,
                "size_bytes": len(content),
                "semester": semester,
                "subject": subject,
                "book": book
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.delete("/{file_key:path}", response_model=MessageResponse)
async def delete_file(
    file_key: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a file from user's S3 directory.
    
    Security: Validates that file_key starts with user's prefix to prevent
    unauthorized deletion of other users' files.
    """
    # Security check: Ensure file belongs to user
    user_prefix = f"users/{user_id}/"
    if not file_key.startswith(user_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this file"
        )
    
    try:
        storage = get_storage_adapter(user_id=user_id)
        
        # Delete from S3
        storage.delete_file(file_key)
        
        return MessageResponse(
            message="File deleted successfully",
            details={"deleted_key": file_key}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.post("/batch-upload", response_model=MessageResponse)
async def batch_upload_files(
    files: List[UploadFile] = File(...),
    semester: str = "General",
    subject: str = "General",
    book: str = "General",
    user_id: str = Depends(get_current_user)
):
    """
    Upload multiple PDF files at once.
    
    All files will be stored in the same semester/subject/book location.
    """
    uploaded = []
    failed = []
    
    for file in files:
        if not file.filename.endswith('.pdf'):
            failed.append({"filename": file.filename, "reason": "Not a PDF"})
            continue
        
        try:
            storage = get_storage_adapter(user_id=user_id)
            s3_key = f"users/{user_id}/raw_data/{semester}/{subject}/{book}/{file.filename}"
            content = await file.read()
            storage.upload_file(content, s3_key)
            uploaded.append(file.filename)
        except Exception as e:
            failed.append({"filename": file.filename, "reason": str(e)})
    
    return MessageResponse(
        message=f"Uploaded {len(uploaded)}/{len(files)} files",
        details={
            "uploaded": uploaded,
            "failed": failed,
            "semester": semester,
            "subject": subject,
            "book": book
        }
    )
