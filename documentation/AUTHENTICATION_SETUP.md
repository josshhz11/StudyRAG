# 🔐 Authentication Setup Guide

## Why Supabase?

For your use case, **Supabase is the best choice** because:

1. **Fast Setup**: 10 minutes vs 2-3 hours for raw Postgres
2. **Built-in Auth**: Login, signup, password reset all handled
3. **Free Tier**: 500MB database, 50K monthly active users
4. **Row Level Security**: Automatically isolates user data
5. **No Server Management**: Hosted solution
6. **Python SDK**: Easy integration with FastAPI

---

## Step 1: Create Supabase Project (5 minutes)

### 1.1 Sign Up
1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (easiest)

### 1.2 Create New Project
1. Click "New Project"
2. Fill in:
   - **Name**: `studyrag-prod`
   - **Database Password**: (generate strong password - save it!)
   - **Region**: Singapore / Asia-Pacific (closest to you)
   - **Pricing Plan**: Free
3. Click "Create new project"
4. Wait 2-3 minutes for provisioning

### 1.3 Get API Keys
1. Go to **Settings** (gear icon) → **API**
2. Copy these values:
   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (long string)
   - **service_role secret key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (different long string)

### 1.4 Enable Email Auth
1. Go to **Authentication** → **Providers**
2. **Email** should be enabled by default
3. Optional: Disable "Confirm email" for testing (re-enable later)

---

## Step 2: Set Up Database Tables (5 minutes)

### 2.1 Create Users Metadata Table
Supabase already has `auth.users` table. We'll create a profile table:

1. Go to **SQL Editor**
2. Click **New Query**
3. Paste this SQL:

```sql
-- User profiles (extends auth.users)
CREATE TABLE public.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read/update their own profile
CREATE POLICY "Users can view own profile" 
    ON public.user_profiles FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" 
    ON public.user_profiles FOR UPDATE 
    USING (auth.uid() = user_id);

-- User preferences
CREATE TABLE public.user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    default_semester VARCHAR(50),
    theme VARCHAR(20) DEFAULT 'light',
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own preferences" 
    ON public.user_preferences FOR ALL 
    USING (auth.uid() = user_id);

-- Usage logs (optional - for analytics)
CREATE TABLE public.usage_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    action_type VARCHAR(50),  -- 'upload', 'query', 'delete', 'ingest'
    resource_path TEXT,  -- S3 key or query text
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own logs" 
    ON public.usage_logs FOR SELECT 
    USING (auth.uid() = user_id);

-- Trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id, username)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1))
    );
    
    INSERT INTO public.user_preferences (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users table
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

4. Click **Run** (or press F5)
5. Verify tables created: Go to **Table Editor** → Should see `user_profiles`, `user_preferences`, `usage_logs`

---

## Step 3: Update Your .env File

Add Supabase credentials:

```bash
# Existing
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-2
S3_BUCKET_NAME=studyrag-prototyping-s3-bucket-1
STORAGE_MODE=s3

# NEW: Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 4: Install Dependencies

```bash
pip install supabase python-dotenv pydantic fastapi uvicorn python-multipart
```

Or add to `requirements.txt`:
```
supabase>=2.0.0
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0  # For JWT token handling
```

---

## Step 5: Test Supabase Connection

Create `test_supabase.py`:

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(url, key)

print("✅ Supabase connection successful!")
print(f"URL: {url}")

# Test signup
try:
    response = supabase.auth.sign_up({
        "email": "test@example.com",
        "password": "TestPassword123!",
        "options": {
            "data": {
                "username": "testuser"
            }
        }
    })
    print("✅ Test signup successful!")
    print(f"User ID: {response.user.id}")
except Exception as e:
    if "already registered" in str(e):
        print("✅ User already exists (that's fine!)")
    else:
        print(f"❌ Signup failed: {e}")

# Test login
try:
    response = supabase.auth.sign_in_with_password({
        "email": "test@example.com",
        "password": "TestPassword123!"
    })
    print("✅ Test login successful!")
    print(f"Session token: {response.session.access_token[:20]}...")
except Exception as e:
    print(f"❌ Login failed: {e}")
```

Run:
```bash
python test_supabase.py
```

Expected output:
```
✅ Supabase connection successful!
URL: https://xxxxxxxxxxxxx.supabase.co
✅ Test signup successful!
User ID: 12345678-1234-1234-1234-123456789abc
✅ Test login successful!
Session token: eyJhbGciOiJIUzI1NiI...
```

---

## Architecture Changes

### Before (No Auth):
```
Streamlit UI → StudyRAGSystem.py → S3/ChromaDB
```

### After (With Auth):
```
┌─────────────────────────────────────┐
│  Streamlit UI                       │
│  • Login Page (new!)                │
│  • Protected Chat Page              │
│  • Protected Upload Page            │
└──────────────┬──────────────────────┘
               │ HTTP + Auth Token
               ▼
┌─────────────────────────────────────┐
│  FastAPI Backend                    │
│  • POST /auth/signup                │
│  • POST /auth/login                 │
│  • GET  /auth/me (verify token)     │
│  • Middleware: verify JWT           │
│  • All routes require auth          │
└──────┬───────────────┬──────────────┘
       │               │
       ▼               ▼
┌─────────────┐   ┌──────────────────┐
│  Supabase   │   │  S3 + ChromaDB   │
│  • Auth     │   │  Scoped by       │
│  • Database │   │  user_id         │
└─────────────┘   └──────────────────┘
```

---

## S3 Path Structure (User-Isolated)

### Before:
```
s3://bucket/
└── users/
    └── default_user/
        └── raw_data/
            └── Y3S2/...
```

### After:
```
s3://bucket/
└── users/
    ├── 12345678-1234-1234-1234-123456789abc/  ← User 1's UUID
    │   └── raw_data/
    │       └── Y3S2/...
    └── 87654321-4321-4321-4321-cba987654321/  ← User 2's UUID
        └── raw_data/
            └── Y3S2/...
```

**Key Change**: `user_id` from Supabase becomes S3 prefix!

---

## Streamlit Authentication Flow

```python
# Login page
if not st.session_state.get('authenticated'):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        response = supabase.auth.sign_in_with_password({...})
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user_id = response.user.id
            st.session_state.access_token = response.session.access_token
            st.rerun()

# Protected pages
else:
    # Show actual app
    st.title("Chat with Your Textbooks")
    # ... rest of app
```

---

## FastAPI Authentication Flow

```python
from fastapi import Depends, HTTPException, Header
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

async def get_current_user(authorization: str = Header(None)):
    """Verify JWT token and return user_id"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        return user.id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Protected route
@app.get("/api/files")
async def list_files(user_id: str = Depends(get_current_user)):
    # user_id automatically injected!
    storage = S3StorageAdapter(user_id=user_id)
    files = storage.list_pdfs()
    return files
```

---

## Security Features You Get Free

1. **Password Hashing**: Supabase handles bcrypt automatically
2. **JWT Tokens**: Secure session management
3. **Email Verification**: Optional, easy to enable
4. **Password Reset**: Built-in "forgot password" flow
5. **Rate Limiting**: Built-in protection against brute force
6. **Row Level Security**: Database-level user isolation

---

## Next Steps

1. ✅ Create Supabase project (done above)
2. ✅ Add credentials to `.env` (done above)
3. ✅ Test connection (done above)
4. 🔲 Create FastAPI backend structure (I'll implement next)
5. 🔲 Add auth endpoints (signup, login, logout)
6. 🔲 Update Streamlit with login page
7. 🔲 Update S3 adapter to be user-scoped
8. 🔲 Test end-to-end auth flow

---

## Comparison: Supabase vs Raw Postgres

| Feature | Supabase | Raw Postgres + Custom |
|---------|----------|---------------------|
| **Setup Time** | 10 mins | 2-3 hours |
| **Auth Logic** | Built-in | Write yourself |
| **Password Hashing** | Automatic | bcrypt manual |
| **JWT Tokens** | Automatic | python-jose manual |
| **Email Verification** | 1 click | SendGrid + code |
| **Password Reset** | Built-in UI | Build form + email |
| **Database Hosting** | Free 500MB | Need PostgreSQL server |
| **Scaling** | Automatic | Manual |
| **Cost (100 users)** | $0/month | $12-25/month (server) |
| **Row Level Security** | Built-in | Manual policies |
| **Admin UI** | Yes | Need pgAdmin |

**Verdict**: Supabase wins by a landslide for your use case!

---

## Alternative: If You Must Use Raw Postgres

If you insist on not using Supabase (not recommended):

1. Install PostgreSQL locally
2. Use **passlib** for password hashing
3. Use **python-jose** for JWT tokens
4. Use **SQLAlchemy** for database ORM
5. Implement signup/login/logout routes manually
6. Set up email service (SendGrid) for verification

**Estimated time**: 4-6 hours vs 10 minutes for Supabase

---

## Ready to Implement?

Run:
```bash
python test_supabase.py
```

If you see ✅ messages, you're ready! I'll now create:
1. FastAPI backend with auth
2. Streamlit login page
3. User-scoped S3 operations

Let me know if you want me to proceed!
