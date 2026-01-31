# 🚀 Quick Start: Backend with Authentication

## What I've Created So Far

### ✅ Completed Files:

```
backend/
├── core/
│   ├── config.py          ✅ Settings from .env
│   └── dependencies.py    ✅ Auth middleware
├── models/
│   ├── requests.py        ✅ API request models
│   └── responses.py       ✅ API response models
└── routers/
    └── auth.py            ✅ Signup/login/logout endpoints
```

### 🔲 Still Need to Create:

```
backend/
├── main.py                🔲 FastAPI app entry point
├── routers/
│   ├── files.py          🔲 Upload/list/delete files
│   └── chat.py           🔲 RAG query endpoint
└── services/
    ├── storage_service.py 🔲 S3 operations
    └── rag_service.py     🔲 LangGraph wrapper
```

---

## Step-by-Step: Complete the Backend

### Step 1: Test Supabase Connection (Do This First!)

```bash
# Follow AUTHENTICATION_SETUP.md to:
# 1. Create Supabase project
# 2. Add credentials to .env
# 3. Run SQL to create tables

# Then test:
python test_supabase.py
```

**Expected output:**
```
✅ Supabase connection successful!
✅ Test signup successful!
✅ Test login successful!
```

---

### Step 2: Install Backend Dependencies

```bash
pip install fastapi uvicorn supabase python-multipart python-jose pydantic-settings
```

Or add to `requirements.txt`:
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
supabase>=2.0.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
pydantic-settings>=2.1.0
```

---

### Step 3: Create Remaining Backend Files

I'll create these files next. For now, here's what each does:

#### `backend/main.py` - FastAPI App
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, files, chat

app = FastAPI(title="StudyRAG API", version="1.0.0")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "StudyRAG API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

#### `backend/routers/files.py` - File Operations
- `GET /api/files` - List user's files (filtered by user_id)
- `POST /api/upload` - Upload PDF to S3 (user's folder)
- `DELETE /api/files/{file_key}` - Delete file from S3

#### `backend/routers/chat.py` - RAG Queries
- `POST /api/chat` - Query with scope filters

---

### Step 4: Update S3 Adapter for User Isolation

**Current:**
```python
# storage_adapter.py
class S3StorageAdapter:
    def __init__(self, user_id="default_user"):
        self.user_id = user_id
```

**Problem:** Everyone uses "default_user"

**Fix:** Pass actual user_id from authentication
```python
# In backend/routers/files.py
@router.get("/files")
async def list_files(user_id: str = Depends(get_current_user)):
    storage = S3StorageAdapter(user_id=user_id)  # ← User's own folder!
    files = storage.list_pdfs()
    return files
```

**S3 Structure:**
```
s3://bucket/
└── users/
    ├── 12345678-1234-1234-1234-123456789abc/  ← User 1
    │   └── raw_data/Y3S2/NLP/...
    └── 87654321-4321-4321-4321-cba987654321/  ← User 2
        └── raw_data/Y3S2/Stats/...
```

---

### Step 5: Run Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Test endpoints:**
```bash
# Signup
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","username":"testuser"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Get profile (with token from login)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Step 6: Update Streamlit Frontend

Create `frontend/pages/0_🔐_Login.py`:

```python
import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Login - StudyRAG", page_icon="🔐")

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Check if already logged in
if st.session_state.get('authenticated'):
    st.success(f"✅ Logged in as {st.session_state.get('email')}")
    
    if st.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
    
    st.info("👉 Go to **Chat** page to start asking questions!")
    st.stop()

# Login/Signup tabs
tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

with tab1:
    st.title("🔐 Login")
    
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login", type="primary"):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Save to session state
                st.session_state.authenticated = True
                st.session_state.user_id = response.user.id
                st.session_state.email = response.user.email
                st.session_state.access_token = response.session.access_token
                
                st.success("✅ Login successful!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Login failed: {str(e)}")

with tab2:
    st.title("📝 Sign Up")
    
    email = st.text_input("Email", key="signup_email")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    password_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
    
    if st.button("Sign Up", type="primary"):
        if password != password_confirm:
            st.error("❌ Passwords don't match!")
        elif len(password) < 8:
            st.error("❌ Password must be at least 8 characters!")
        else:
            try:
                response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "username": username
                        }
                    }
                })
                
                if response.user:
                    st.success("✅ Signup successful! Please check your email to verify.")
                    st.info("You can now login with your credentials.")
            except Exception as e:
                st.error(f"❌ Signup failed: {str(e)}")
```

**Update `streamlit_app.py`** to check authentication:

```python
# At the top, after imports
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Please login first!")
    st.info("👉 Go to the **Login** page")
    st.stop()

# Rest of your chat code...
```

---

### Step 7: Test End-to-End Flow

1. **Start backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start frontend:**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Test workflow:**
   - Go to Login page
   - Sign up new user
   - Login
   - Chat page now accessible
   - Upload page shows only your files

---

## Architecture After Authentication

```
┌─────────────────────────────────────┐
│  Streamlit Frontend                 │
│  ├─ 0_🔐_Login.py (NEW!)           │
│  ├─ 1_💬_Chat.py (protected)       │
│  ├─ 2_📚_Upload.py (user-scoped)   │
│  └─ Check auth on each page        │
└──────────────┬──────────────────────┘
               │ HTTP + JWT Token
               ▼
┌─────────────────────────────────────┐
│  FastAPI Backend                    │
│  ├─ Auth middleware (verify token) │
│  ├─ Inject user_id into routes     │
│  └─ All operations scoped by user  │
└──────┬────────────────┬─────────────┘
       │                │
       ▼                ▼
┌─────────────┐   ┌──────────────────┐
│  Supabase   │   │  S3 (per-user)   │
│  Auth +     │   │  users/{user_id}/│
│  Profiles   │   │    └─ raw_data/  │
└─────────────┘   └──────────────────┘
```

---

## Security Features

1. **JWT Tokens**: Secure session management
2. **Row Level Security**: Database-level user isolation
3. **S3 Path Isolation**: `users/{user_id}/` prevents cross-user access
4. **Vector DB Filtering**: Metadata filter by `user_id`
5. **Password Hashing**: Automatic via Supabase

---

## Next Actions for You

1. **Follow AUTHENTICATION_SETUP.md** to create Supabase project
2. **Run `python test_supabase.py`** to verify connection
3. **Let me know when ready**, and I'll create the remaining backend files:
   - `backend/main.py`
   - `backend/routers/files.py`
   - `backend/routers/chat.py`
   - `backend/services/storage_service.py`
   - `backend/services/rag_service.py`
4. **Update Streamlit** with login page

---

## Estimated Timeline

- **Supabase Setup**: 10 minutes
- **Backend Completion**: 30 minutes (I'll code it)
- **Frontend Login Page**: 15 minutes
- **Testing**: 15 minutes
- **Total**: ~1-1.5 hours

Much faster than raw Postgres (4-6 hours)!

---

**Ready to proceed?** 

1. Create your Supabase project now
2. Run `python test_supabase.py`
3. Share the output, and I'll complete the backend!
