# 🚀 Quick Testing Checklist

## Before You Start

- [ ] Supabase project created and credentials in .env
- [ ] AWS S3 bucket configured and credentials in .env
- [ ] Backend dependencies installed: `pip install -r backend/requirements.txt`

---

## Test with Postman (Recommended)

### 1. Start Backend
```powershell
cd backend
uvicorn main:app --reload
```
**Wait for:** `🚀 StudyRAG API starting...`

---

### 2. Open Postman & Test

| # | Method | URL | Body/Params | Expected |
|---|--------|-----|-------------|----------|
| 1 | GET | `http://localhost:8000/health` | None | `"status": "healthy"` |
| 2 | POST | `/auth/signup` | JSON: email, password, username | Get `access_token` |
| 3 | GET | `/api/files` | Auth: Bearer {token} | `"files": []` (empty) |
| 4 | POST | `/api/files/upload?semester=Y3S2&subject=NLP&book=Ch1` | form-data: file={PDF} | Success message |
| 5 | GET | `/api/files` | Auth: Bearer {token} | 1 file listed |

---

### 3. Verify in AWS S3

Check AWS Console → S3 → Your Bucket:
```
✅ Should see: users/{user_id}/raw_data/Y3S2/NLP/Ch1/yourfile.pdf
```

---

### 4. Test Multi-User Isolation

| Step | Action | Expected |
|------|--------|----------|
| 1 | Sign up User 2 (different email) | New access_token |
| 2 | GET /api/files (User 2 token) | `"files": []` (User 1's file NOT visible) |
| 3 | Upload file as User 2 | Success |
| 4 | Check S3 | Two separate folders: `users/{user1_id}/` and `users/{user2_id}/` |

---

## Test with Streamlit

### 1. Start Streamlit
```powershell
streamlit run streamlit_app.py
```

### 2. Test Flow

| # | Page | Action | Expected |
|---|------|--------|----------|
| 1 | Login | Sign up new account | Auto-login |
| 2 | Chat | Try to access | Should work (authenticated) |
| 3 | S3 Upload | View files | "👋 Welcome! First time uploading" |
| 4 | S3 Upload | Upload PDF | "🎉 Your user folder has been created!" 🎈 |
| 5 | S3 Upload | View files again | Should see uploaded file |

---

## Common Checks

### ✅ Backend Running?
- Open: http://localhost:8000/docs
- Should see: Swagger UI with endpoints

### ✅ Authentication Working?
```powershell
# In Postman
POST /auth/login → Should return access_token
GET /auth/me (with token) → Should return user profile
```

### ✅ User Folder Created?
- New user: GET /api/files → Returns `[]`
- After upload: GET /api/files → Returns file list
- AWS S3: Folder `users/{user_id}/` now exists

### ✅ User Isolation Working?
- User 1 uploads file1.pdf
- User 2 lists files → Should NOT see file1.pdf
- User 2 uploads file2.pdf
- User 1 lists files → Should NOT see file2.pdf

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Token expired - login again |
| "User ID not found" | Session expired - refresh Streamlit page |
| Empty files after upload | Check backend terminal logs for errors |
| Can't connect to S3 | Verify AWS credentials in .env |
| Supabase error | Check SUPABASE_URL and SUPABASE_ANON_KEY |

---

## Success Criteria

- [x] Backend starts without errors
- [x] Can sign up new user
- [x] Can login and get token
- [x] New user sees empty file list
- [x] Can upload PDF file
- [x] File appears in S3 under `users/{user_id}/`
- [x] Can list uploaded files
- [x] Second user doesn't see first user's files
- [x] Streamlit login page works
- [x] Streamlit pages protected (redirect to login if not authenticated)

---

## Next Steps After Testing

1. ✅ Backend API tested and working
2. 🔄 **Next:** Test Streamlit integration
3. 🔄 **Next:** Ingest uploaded PDFs into ChromaDB
4. 🔄 **Next:** Test chat with RAG queries
5. 🔄 **Next:** Deploy to production

---

## Quick Commands Reference

```powershell
# Start backend
cd backend
uvicorn main:app --reload

# Start Streamlit
streamlit run streamlit_app.py

# Test S3 connection
python test_connection.py

# Test Supabase connection
python test_supabase.py
```

---

## Documentation Files

- [START_HERE.md](START_HERE.md) - Complete quickstart guide
- [BACKEND_TESTING.md](BACKEND_TESTING.md) - Detailed Postman + curl testing
- [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - How authentication works
- [ON_DEMAND_FOLDERS_IMPLEMENTATION.md](ON_DEMAND_FOLDERS_IMPLEMENTATION.md) - On-demand folder creation explained

---

**Ready? Let's test!** 🚀

Open Postman, follow [BACKEND_TESTING.md](BACKEND_TESTING.md), and verify everything works!
