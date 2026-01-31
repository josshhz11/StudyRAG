# 🧪 Backend Testing Guide

## Choose Your Testing Tool

- **Option 1: Postman** (Recommended - Visual, Easy, Save Collections)
- **Option 2: curl** (Command-line, Quick Tests)

---

## 🚀 Start the Backend Server

```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
🚀 StudyRAG API starting...
📝 API Docs: http://localhost:8000/docs
🔐 Auth endpoints: /auth/signup, /auth/login
🌐 CORS enabled for: ['http://localhost:8501']
```

---

# 📬 OPTION 1: Testing with Postman (Recommended)

## Setup Postman

1. **Download Postman**: https://www.postman.com/downloads/
2. **Install and launch** Postman
3. **Create new Collection**: "StudyRAG API"

---

## 1. Health Check

**Method:** `GET`  
**URL:** `http://localhost:8000/health`  
**Headers:** None needed

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "studyrag-backend"
}
```

---

## 2. Sign Up New User

**Method:** `POST`  
**URL:** `http://localhost:8000/auth/signup`  
**Headers:**
- `Content-Type`: `application/json`

**Body (raw JSON):**
```json
{
  "email": "joshua@example.com",
  "password": "MySecurePass123",
  "username": "joshua"
}
```

**Expected Response:**
```json
{
  "user": {
    "user_id": "12345678-1234-1234-1234-123456789abc",
    "email": "joshua@example.com",
    "username": "joshua"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "...",
  "expires_at": 1234567890
}
```

**⚠️ IMPORTANT:** Copy the `access_token` value!

---

## 3. Set Up Authorization for All Future Requests

### Method 1: Using Collection Variables (Best Practice)

1. Click on your "StudyRAG API" collection
2. Go to **Variables** tab
3. Add variable:
   - Name: `access_token`
   - Initial Value: (paste your token)
   - Current Value: (paste your token)
4. Save

Now in any request:
- Go to **Authorization** tab
- Type: `Bearer Token`
- Token: `{{access_token}}`

### Method 2: Manual for Each Request

In each protected request:
- Go to **Authorization** tab
- Type: `Bearer Token`
- Token: (paste your actual token)

---

## 4. Login (Get New Token)

**Method:** `POST`  
**URL:** `http://localhost:8000/auth/login`  
**Headers:**
- `Content-Type`: `application/json`

**Body (raw JSON):**
```json
{
  "email": "joshua@example.com",
  "password": "MySecurePass123"
}
```

**Expected Response:** Same as signup (new tokens)

---

## 5. Get Current User Profile

**Method:** `GET`  
**URL:** `http://localhost:8000/auth/me`  
**Authorization:** Bearer Token (use `{{access_token}}`)

**Expected Response:**
```json
{
  "user_id": "12345678-1234-1234-1234-123456789abc",
  "email": "joshua@example.com",
  "username": "joshua"
}
```

---

## 6. List User's Files

**Method:** `GET`  
**URL:** `http://localhost:8000/api/files`  
**Authorization:** Bearer Token (use `{{access_token}}`)

**Expected Response (no files yet):**
```json
{
  "files": [],
  "total": 0
}
```

**Note:** Your `users/{user_id}/` folder is created on-demand when you upload your first file!

---

## 7. Upload a PDF File

**Method:** `POST`  
**URL:** `http://localhost:8000/api/files/upload?semester=Y3S2&subject=NLP&book=TextbookCh1`  
**Authorization:** Bearer Token (use `{{access_token}}`)

**Body:**
1. Select **form-data** (not raw JSON!)
2. Add key: `file`
   - Change type dropdown from "Text" to **"File"**
   - Click "Select Files" and choose a PDF

**Query Parameters (in URL or Params tab):**
- `semester`: Y3S2
- `subject`: NLP
- `book`: TextbookCh1

**Expected Response:**
```json
{
  "message": "File 'yourfile.pdf' uploaded successfully",
  "details": {
    "s3_key": "users/12345678.../raw_data/Y3S2/NLP/TextbookCh1/yourfile.pdf",
    "size_bytes": 123456,
    "semester": "Y3S2",
    "subject": "NLP",
    "book": "TextbookCh1"
  }
}
```

**🎉 Your user folder is now created in S3!**

---

## 8. List Files Again (Should Show Uploaded File)

**Method:** `GET`  
**URL:** `http://localhost:8000/api/files`  
**Authorization:** Bearer Token

**Expected Response:**
```json
{
  "files": [
    {
      "key": "users/12345678.../raw_data/Y3S2/NLP/TextbookCh1/yourfile.pdf",
      "semester": "Y3S2",
      "subject": "NLP",
      "book_id": "TextbookCh1",
      "book_title": "yourfile",
      "size": 123456,
      "s3_url": "s3://studyrag-prototyping-s3-bucket-1/users/12345678.../raw_data/Y3S2/NLP/TextbookCh1/yourfile.pdf"
    }
  ],
  "total": 1
}
```

---

## 9. Chat Query (RAG)

**Method:** `POST`  
**URL:** `http://localhost:8000/api/chat/query`  
**Authorization:** Bearer Token  
**Headers:**
- `Content-Type`: `application/json`

**Body (raw JSON):**
```json
{
  "question": "What is natural language processing?",
  "semester": "Y3S2",
  "subject": "NLP",
  "books": ["TextbookCh1"]
}
```

**Expected Response:**
```json
{
  "answer": "Natural language processing (NLP) is...",
  "sources": [
    {
      "content": "NLP is a field of AI...",
      "metadata": {
        "semester": "Y3S2",
        "subject": "NLP",
        "book": "TextbookCh1"
      }
    }
  ],
  "metadata": {
    "user_id": "12345678-...",
    "scope": {"semester": "Y3S2", "subject": "NLP"},
    "model": "gpt-4o"
  }
}
```

---

## 10. Delete a File

**Method:** `DELETE`  
**URL:** `http://localhost:8000/api/files/users/12345678.../raw_data/Y3S2/NLP/TextbookCh1/yourfile.pdf`  
**Authorization:** Bearer Token

**Note:** Replace the path with actual `file_key` from list_files response

**Expected Response:**
```json
{
  "message": "File deleted successfully",
  "success": true,
  "details": {
    "deleted_key": "users/12345678.../..."
  }
}
```

---

## 📁 Save Your Postman Collection

1. Click on "StudyRAG API" collection
2. Click **...** (three dots)
3. **Export** → Collection v2.1
4. Save as `studyrag-api-collection.json`
5. Share with team or backup

---

# 🖥️ OPTION 2: Testing with curl

## Test Endpoints

### 1. Health Check
```powershell
curl http://localhost:8000/health
```

**Expected:**
```json
{"status": "healthy", "service": "studyrag-backend"}
```

---

### 2. Sign Up New User
```powershell
curl -X POST http://localhost:8000/auth/signup `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"joshua@example.com\",\"password\":\"MySecurePass123\",\"username\":\"joshua\"}'
```

**Expected:**
```json
{
  "user": {
    "user_id": "12345678-1234-1234-1234-123456789abc",
    "email": "joshua@example.com",
    "username": "joshua"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "...",
  "expires_at": 1234567890
}
```

**Copy the `access_token` for next tests!**

---

### 3. Login
```powershell
curl -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"joshua@example.com\",\"password\":\"MySecurePass123\"}'
```

---

### 4. Get Current User Profile
```powershell
# Replace YOUR_TOKEN with the access_token from signup/login
curl http://localhost:8000/auth/me `
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:**
```json
{
  "user_id": "12345678-1234-1234-1234-123456789abc",
  "email": "joshua@example.com",
  "username": "joshua"
}
```

---

### 5. List User's Files
```powershell
curl http://localhost:8000/api/files `
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected (if no files yet):**
```json
{
  "files": [],
  "total_count": 0
}
```

---

### 6. Upload a PDF File
```powershell
# Upload test file
curl -X POST "http://localhost:8000/api/files/upload?semester=Y3S2&subject=NLP&book=TextbookCh1" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -F "file=@path/to/your/file.pdf"
```

**Expected:**
```json
{
  "message": "File 'file.pdf' uploaded successfully",
  "details": {
    "s3_key": "users/12345678.../raw_data/Y3S2/NLP/TextbookCh1/file.pdf",
    "size_bytes": 123456,
    "semester": "Y3S2",
    "subject": "NLP",
    "book": "TextbookCh1"
  }
}
```

---

### 7. Chat Query (RAG)
```powershell
curl -X POST http://localhost:8000/api/chat/query `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{\"question\":\"What is natural language processing?\",\"semester\":\"Y3S2\",\"subject\":\"NLP\"}'
```

**Expected:**
```json
{
  "answer": "Natural language processing (NLP) is...",
  "sources": [
    {
      "content": "NLP is a field of AI that focuses on...",
      "metadata": {
        "semester": "Y3S2",
        "subject": "NLP",
        "book": "TextbookCh1"
      }
    }
  ],
  "metadata": {
    "user_id": "...",
    "scope": {"semester": "Y3S2", "subject": "NLP"},
    "model": "gpt-4o"
  }
}
```

---

### 8. Delete a File
```powershell
# Replace FILE_KEY with actual S3 key from list_files
curl -X DELETE "http://localhost:8000/api/files/users%2F12345678...%2Fraw_data%2FY3S2%2FNLP%2FTextbookCh1%2Ffile.pdf" `
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Test with Interactive API Docs

1. Open http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Enter: `Bearer YOUR_TOKEN`
4. Now you can test all endpoints interactively!

---

# 🌐 Interactive API Docs (Swagger UI)

1. Open http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Enter: `Bearer YOUR_TOKEN`
4. Now you can test all endpoints interactively!

---

# ✅ Verify in Dashboards

## Supabase Dashboard

1. Go to https://supabase.com/dashboard
2. **Authentication** → **Users**: Should see your test user
3. **Table Editor** → **user_profiles**: Should see username

## AWS S3 Console

1. Go to AWS S3 console
2. Open bucket: `studyrag-prototyping-s3-bucket-1`
3. Should see folder structure:
   ```
   users/
   └── 12345678-1234-1234-1234-123456789abc/
       └── raw_data/
           └── Y3S2/
               └── NLP/
                   └── TextbookCh1/
                       └── yourfile.pdf
   ```

**Note:** User folder is created on-demand when first file is uploaded!

---

# 🐛 Common Issues

### 401 Unauthorized
- Check if token is valid (not expired)
- Ensure `Authorization: Bearer <token>` header is included
- Token expires after 1 hour by default
- Get new token by logging in again

### 500 Internal Server Error
- Check backend logs in terminal
- Verify .env file has all required variables
- Check if S3 credentials are correct
- Verify Supabase credentials

### CORS Error (from Streamlit)
- Verify `CORS_ORIGINS=http://localhost:8501` in .env
- Restart backend after changing .env

### Empty Files List After Upload
- Check AWS S3 console directly
- Verify user_id in access token matches S3 path
- Check backend logs for upload confirmation

### "User folder doesn't exist"
- This is normal for new users!
- User folder is created automatically on first file upload
- Upload a file, then list_files will show results

---

# 🎯 Multi-User Testing Workflow

Test user isolation:

1. **Sign up User 1**: `user1@test.com`
2. **Upload file for User 1**: `Y3S2/NLP/Book1/file1.pdf`
3. **List files for User 1**: Should see 1 file
4. **Sign up User 2**: `user2@test.com`
5. **List files for User 2**: Should see 0 files (empty folder)
6. **Upload file for User 2**: `Y3S2/NLP/Book1/file2.pdf`
7. **List files for User 2**: Should see 1 file (only file2.pdf)
8. **List files for User 1**: Should still see 1 file (only file1.pdf)

**Verify in S3:**
```
users/
├── {user1_id}/
│   └── raw_data/Y3S2/NLP/Book1/file1.pdf
└── {user2_id}/
    └── raw_data/Y3S2/NLP/Book1/file2.pdf
```

---

# 📚 Postman Tips

- **Save your collection** for reuse
- **Use environment variables** for `access_token` and `base_url`
- **Create tests** to auto-extract tokens from responses
- **Share collections** with your team

---

# 🚀 Ready to Test!

Choose Postman (recommended) or curl, and start testing your authenticated multi-user API!
