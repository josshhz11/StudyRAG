# 🚀 Start Your Multi-User StudyRAG System

## What's Been Built

✅ **Backend API (FastAPI)**
- Authentication endpoints (signup, login, logout, profile)
- File management (upload, list, delete) with user isolation
- Chat endpoint for RAG queries
- JWT token validation
- CORS enabled for Streamlit

✅ **Database (Supabase)**
- User authentication system
- User profiles and preferences tables
- Automatic triggers for new users
- Row Level Security for data isolation

✅ **Frontend (Streamlit)**
- Login/signup page with validation
- Protected chat interface
- Protected textbook upload page
- Protected S3 file manager
- Session state management

---

## 🎯 Quick Start (15 minutes)

### Step 1: Start Backend (Terminal 1)

```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
🚀 StudyRAG API starting...
📝 API Docs: http://localhost:8000/docs
🔐 Auth endpoints: /auth/signup, /auth/login
🌐 CORS enabled for: ['http://localhost:8501']
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

---

### Step 2: Start Streamlit (Terminal 2)

```powershell
streamlit run streamlit_app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Keep this terminal open too!**

---

### Step 3: Open Browser

Open: http://localhost:8501

You should see:
- Sidebar with **🔐 Login** page (first in list)
- Login/signup form
- No access to chat/upload pages until logged in

---

### Step 4: Create Your Account

1. Click on **🔐 Login** page (sidebar)
2. Click **Sign Up** tab
3. Fill in:
   - Email: `your.email@example.com`
   - Username: `yourname`
   - Password: `MySecure123` (min 8 chars, 1 uppercase, 1 number)
   - Confirm password
   - Check "I agree" checkbox
4. Click **Create Account**

**What happens:**
- Supabase creates account in `auth.users` (password hashed)
- Database trigger creates row in `user_profiles`
- You get JWT access token
- Logged in automatically!

---

### Step 5: Test the System

#### ✅ Chat Page
1. Click **💬 StudyRAG** in sidebar
2. Should see chat interface (not login warning)
3. Try asking: "What is machine learning?"

#### ✅ Upload Textbooks
1. Click **📚 Add Textbooks**
2. Should see ingestion interface (not blocked)

#### ✅ S3 File Manager
1. Click **☁️ S3 Upload**
2. Should see your file directory (empty at first)
3. Upload a PDF → Goes to `users/{your_user_id}/raw_data/`

---

## 🔐 Understanding the Flow

### User Creation
```
Streamlit Form
    ↓
supabase.auth.sign_up({email, password, username})
    ↓
Supabase Auth Service
    - Hashes password with bcrypt
    - Stores in auth.users.encrypted_password
    - Stores username in auth.users.raw_user_meta_data
    ↓
PostgreSQL Trigger Fires
    - on_auth_user_created trigger
    - handle_new_user() function runs
    ↓
Creates Rows:
    - public.user_profiles (user_id, username)
    - public.user_preferences (user_id, default_settings)
    ↓
Returns to Streamlit:
    - user.id (UUID)
    - session.access_token (JWT)
    - session.refresh_token
    ↓
Streamlit Session State:
    st.session_state.authenticated = True
    st.session_state.user_id = "12345678-..."
    st.session_state.access_token = "eyJhbG..."
```

### Login Flow
```
User enters email + password
    ↓
supabase.auth.sign_in_with_password({email, password})
    ↓
Supabase:
    - Hashes entered password
    - Compares with auth.users.encrypted_password
    - If match: generates new JWT token
    - If no match: raises "Invalid credentials"
    ↓
Returns session with access_token
    ↓
Streamlit stores token in session_state
    ↓
User can access protected pages
```

### File Upload Flow (User-Isolated)
```
User uploads PDF
    ↓
Streamlit checks: st.session_state.get('user_id')
    ↓
storage = get_storage_adapter(user_id=user_id)
    ↓
S3 key: users/{user_id}/raw_data/Y3S2/NLP/textbook.pdf
    ↓
Only this user can access files in their directory
```

---

## 🔍 Verify Everything Works

### 1. Check Supabase Dashboard

Go to: https://supabase.com/dashboard

**Authentication → Users:**
- Should see your account
- Email, created_at timestamp
- Confirmed status

**Table Editor → user_profiles:**
- Should see row with your user_id
- Username should match what you entered

**Table Editor → user_preferences:**
- Should see row with your user_id
- Default settings

### 2. Check S3 Bucket

AWS Console → S3 → `studyrag-prototyping-s3-bucket-1`

Should see folder structure:
```
users/
└── 12345678-1234-1234-1234-123456789abc/  ← Your user_id
    └── raw_data/
        └── (your uploaded files)
```

### 3. Test Backend API

Open: http://localhost:8000/docs

**Try these:**
1. POST `/auth/login` → Returns access_token
2. Click "Authorize" → Enter: `Bearer {your_token}`
3. GET `/auth/me` → Returns your profile
4. GET `/api/files` → Returns your files only

---

## 🐛 Troubleshooting

### "Please login to access this page"
- Session expired (token valid for 1 hour)
- Solution: Go to Login page, login again

### "401 Unauthorized" in backend
- Token expired or invalid
- Solution: Login again to get new token

### "CORS Error" in browser console
- Backend not running
- Solution: Start backend with `uvicorn main:app --reload`

### Can't see uploaded files in S3
- Check if user_id in session_state
- Check S3 bucket in AWS console
- Verify `STORAGE_MODE=s3` in .env

### Backend errors on startup
- Missing dependencies: `pip install -r backend/requirements.txt`
- Missing .env variables: Check `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- Port 8000 already in use: Kill process or use `--port 8001`

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  STREAMLIT FRONTEND (localhost:8501)                        │
│  ├─ pages/0_🔐_Login.py        → Authentication UI         │
│  ├─ streamlit_app.py            → Chat Interface (protected)│
│  ├─ pages/1_📚_Add_Textbooks.py → Ingestion (protected)    │
│  └─ pages/2_☁️_S3_Upload.py     → File Manager (protected) │
└────────────────────┬────────────────────────────────────────┘
                     │ Session State:
                     │ - authenticated: True/False
                     │ - user_id: UUID
                     │ - access_token: JWT
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND (localhost:8000)                           │
│  ├─ /auth/signup, /auth/login   → User management          │
│  ├─ /api/files                  → S3 operations (protected) │
│  ├─ /api/chat                   → RAG queries (protected)   │
│  └─ Middleware: JWT validation + user_id injection          │
└──────────┬─────────────────┬────────────────────────────────┘
           │                 │
           ▼                 ▼
┌─────────────────┐   ┌────────────────────────────────┐
│  SUPABASE       │   │  AWS S3                        │
│  ├─ auth.users  │   │  users/{user_id}/raw_data/     │
│  ├─ profiles    │   │    ├─ Y3S2/NLP/textbook.pdf    │
│  └─ preferences │   │    └─ Y4S1/Stats/book.pdf      │
└─────────────────┘   └────────────────────────────────┘
                              │
                              ▼
                      ┌───────────────────┐
                      │  CHROMADB         │
                      │  Vector Store     │
                      │  (per-user docs)  │
                      └───────────────────┘
```

---

## 🎉 What You've Achieved

✅ **Multi-User Authentication**
- Secure signup/login with Supabase
- Password hashing (bcrypt)
- JWT session management
- Email verification support

✅ **User Isolation**
- Each user has their own S3 directory
- Files stored at `users/{user_id}/raw_data/`
- No cross-user data access

✅ **Protected Routes**
- All Streamlit pages check authentication
- Backend endpoints require valid JWT token
- Automatic redirect to login if not authenticated

✅ **Scalable Architecture**
- FastAPI backend (async)
- Supabase database (managed Postgres)
- AWS S3 storage (cloud-based)
- Easy to deploy to production

---

## 🚀 Next Steps (Optional)

### 1. Add User Isolation to ChromaDB
Update ingestion to tag documents with `user_id`:
```python
# In StudyRAGSystem.py
metadata = {
    "semester": semester,
    "subject": subject,
    "book": book,
    "user_id": user_id  # Add this!
}
```

Then filter by user_id in retrieval:
```python
# In build_study_agent()
scope["user_id"] = user_id
```

### 2. Deploy to Production
- Backend: Railway, Fly.io, or AWS EC2
- Frontend: Streamlit Cloud
- Database: Already on Supabase (production-ready)
- Storage: Already on AWS S3 (production-ready)

### 3. Add Features
- Chat history storage
- File search functionality
- Usage analytics dashboard
- Team collaboration (share textbooks)
- Export chat conversations

---

## 📝 Important Files

### Backend
- `backend/main.py` - FastAPI app entry point
- `backend/routers/auth.py` - Authentication endpoints
- `backend/routers/files.py` - File management
- `backend/routers/chat.py` - RAG queries
- `backend/core/dependencies.py` - JWT validation
- `backend/core/config.py` - Environment settings

### Frontend
- `pages/0_🔐_Login.py` - Login/signup interface
- `streamlit_app.py` - Chat page (protected)
- `pages/1_📚_Add_Textbooks.py` - Ingestion (protected)
- `pages/2_☁️_S3_Upload.py` - File manager (protected)

### Database
- Check `AUTHENTICATION_SETUP.md` for SQL schema
- Supabase manages auth.users automatically
- Your tables: user_profiles, user_preferences, usage_logs

---

## ✅ Ready to Go!

1. **Start both servers** (backend + frontend)
2. **Open browser** → http://localhost:8501
3. **Sign up** for account
4. **Start chatting** with your AI study assistant!

🎓 **Happy studying with StudyRAG!**
