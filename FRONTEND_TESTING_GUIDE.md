# 🧪 Complete Next.js Frontend Testing Guide

## Prerequisites

✅ **Backend running**: `cd backend && uvicorn main:app --reload --port 8000`  
✅ **Frontend running**: `cd frontend && npm run dev`  
✅ **Browser open**: http://localhost:3000

---

## 🎯 Test Checklist

### Phase 1: Basic Navigation & UI

#### Test 1.1: Initial Load & Redirect
- [ ] Open http://localhost:3000
- [ ] Should see loading spinner briefly
- [ ] Automatically redirects to http://localhost:3000/login
- [ ] Login page displays with:
  - [ ] "📚 StudyRAG" header
  - [ ] Email input field
  - [ ] Password input field
  - [ ] "Sign in" button
  - [ ] "Don't have an account? Sign up" link

**Expected Result**: Clean redirect to login page, no errors in browser console

---

#### Test 1.2: Navigate to Signup Page
- [ ] Click "Sign up" link at bottom of login page
- [ ] URL changes to http://localhost:3000/signup
- [ ] Signup page displays with:
  - [ ] Username input field
  - [ ] Email input field
  - [ ] Password input field (min 8 characters)
  - [ ] "Sign up" button
  - [ ] "Already have an account? Sign in" link

**Expected Result**: Smooth navigation, form fields appear correctly

---

#### Test 1.3: Navigate Back to Login
- [ ] From signup page, click "Sign in" link
- [ ] URL changes back to http://localhost:3000/login
- [ ] Login form displays correctly

**Expected Result**: Can navigate between login/signup freely

---

### Phase 2: Authentication Flow

#### Test 2.1: Sign Up New User
**Actions:**
1. [ ] Go to http://localhost:3000/signup
2. [ ] Fill in form:
   - Username: `testuser1`
   - Email: `testuser1@example.com`
   - Password: `Password123!`
3. [ ] Click "Sign up" button
4. [ ] Wait for response

**Expected Results:**
- [ ] Button shows "Creating account..." while loading
- [ ] No error messages appear
- [ ] Automatically redirects to http://localhost:3000/dashboard
- [ ] Navbar appears at top with:
  - [ ] "📚 StudyRAG" logo on left
  - [ ] "Dashboard" and "Chat" links
  - [ ] Username/email displayed
  - [ ] "Logout" button on right
- [ ] Dashboard shows "Your Files (0)" - empty list
- [ ] "No files uploaded yet" message

**Verify in Supabase:**
1. [ ] Go to https://supabase.com/dashboard
2. [ ] Open your project
3. [ ] Go to **Authentication** → **Users**
4. [ ] New user `testuser1@example.com` appears in list
5. [ ] Copy the `user_id` (UUID format: `12345678-1234-...`)
6. [ ] Go to **Table Editor** → **user_profiles**
7. [ ] User profile exists with:
   - [ ] `user_id` matches from auth.users
   - [ ] `username` = `testuser1`
   - [ ] `created_at` timestamp

**Verify in Browser DevTools:**
1. [ ] Press F12 to open DevTools
2. [ ] Go to **Application** tab → **Local Storage** → `http://localhost:3000`
3. [ ] Check keys exist:
   - [ ] `studyrag_token` (JWT token string)
   - [ ] `studyrag_user` (JSON object with user info)

**If Test Fails:**
- Check backend terminal for errors
- Check browser console for error messages
- Verify backend is running on port 8000
- Check CORS is enabled in backend

---

#### Test 2.2: Logout and Login
**Actions:**
1. [ ] Click "Logout" button in navbar (top right)
2. [ ] Redirects to http://localhost:3000/login
3. [ ] Fill in login form:
   - Email: `testuser1@example.com`
   - Password: `Password123!`
4. [ ] Click "Sign in" button

**Expected Results:**
- [ ] Button shows "Signing in..." while loading
- [ ] Redirects to http://localhost:3000/dashboard
- [ ] User still logged in (navbar shows username)
- [ ] LocalStorage has new token

**Verify Token Cleared:**
1. [ ] Before logging in, check DevTools → Application → Local Storage
2. [ ] After logout: `studyrag_token` and `studyrag_user` should be deleted
3. [ ] After login: New token and user data saved

---

#### Test 2.3: Protected Route Access Without Auth
**Actions:**
1. [ ] Logout (if logged in)
2. [ ] Manually try to access http://localhost:3000/dashboard in address bar
3. [ ] Try http://localhost:3000/chat

**Expected Results:**
- [ ] Shows loading spinner briefly
- [ ] Automatically redirects to http://localhost:3000/login
- [ ] Cannot access protected pages without authentication

---

#### Test 2.4: Authentication Persistence
**Actions:**
1. [ ] Login successfully
2. [ ] Refresh the page (F5 or Ctrl+R)
3. [ ] Open new browser tab, go to http://localhost:3000

**Expected Results:**
- [ ] Still logged in after refresh
- [ ] New tab also shows authenticated state
- [ ] Token persists in localStorage

---

### Phase 3: File Upload & Management

#### Test 3.1: Upload First PDF File
**Setup:**
- [ ] Make sure you're logged in as `testuser1@example.com`
- [ ] Have a PDF file ready (any PDF, e.g., a textbook chapter)

**Actions:**
1. [ ] Go to Dashboard page
2. [ ] Fill in upload form:
   - Semester: `Y3S2`
   - Subject: `NLP`
   - Book/Chapter: `TextbookCh1`
3. [ ] Click "Choose File" and select your PDF
4. [ ] Verify selected file shows: "Selected: filename.pdf (X MB)"
5. [ ] Click "Upload File" button

**Expected Results:**
- [ ] Button changes to "Uploading..." with spinner
- [ ] Green success message appears: "File 'filename.pdf' uploaded successfully!"
- [ ] File appears in table below with:
  - [ ] File name
  - [ ] Semester: Y3S2
  - [ ] Subject: NLP
  - [ ] Book: TextbookCh1
  - [ ] File size in MB/KB
  - [ ] Delete button
- [ ] Header shows "Your Files (1)"
- [ ] Upload form clears (file input resets)

**Verify in AWS S3:**
1. [ ] Go to AWS S3 Console: https://s3.console.aws.amazon.com/s3/buckets
2. [ ] Open bucket: `studyrag-prototyping-s3-bucket-1`
3. [ ] Navigate to: `users/{user_id}/raw_data/Y3S2/NLP/TextbookCh1/`
   - Replace `{user_id}` with your actual user_id from Supabase
4. [ ] File exists at correct path
5. [ ] File size matches uploaded file

**Browser DevTools Check:**
1. [ ] Open DevTools → Network tab
2. [ ] Look for POST request to `http://localhost:8000/api/files/upload?semester=Y3S2&subject=NLP&book=TextbookCh1`
3. [ ] Check request headers:
   - [ ] `Authorization: Bearer {token}`
   - [ ] `Content-Type: multipart/form-data`
4. [ ] Check response (Status 201):
   ```json
   {
     "message": "File 'filename.pdf' uploaded successfully",
     "details": {
       "s3_key": "users/.../raw_data/Y3S2/NLP/TextbookCh1/filename.pdf",
       "size_bytes": 123456,
       "semester": "Y3S2",
       "subject": "NLP",
       "book": "TextbookCh1"
     }
   }
   ```

---

#### Test 3.2: Upload Multiple Files (Different Metadata)
**Actions:**
1. [ ] Upload 2nd file:
   - Semester: `Y3S2`
   - Subject: `NLP`
   - Book/Chapter: `TextbookCh2`
2. [ ] Upload 3rd file:
   - Semester: `Y3S2`
   - Subject: `TimeSeries`
   - Book/Chapter: `LectureNotes`
3. [ ] Upload 4th file:
   - Semester: `Y4S1`
   - Subject: `MachineLearning`
   - Book/Chapter: `DeepLearning`

**Expected Results:**
- [ ] All 4 files appear in table
- [ ] Header shows "Your Files (4)"
- [ ] Each file has correct metadata
- [ ] Files sorted/displayed correctly

**Verify in S3:**
- [ ] Folder structure created:
  ```
  users/{user_id}/raw_data/
    ├── Y3S2/
    │   ├── NLP/
    │   │   ├── TextbookCh1/
    │   │   │   └── file1.pdf
    │   │   └── TextbookCh2/
    │   │       └── file2.pdf
    │   └── TimeSeries/
    │       └── LectureNotes/
    │           └── file3.pdf
    └── Y4S1/
        └── MachineLearning/
            └── DeepLearning/
                └── file4.pdf
  ```

---

#### Test 3.3: Upload Validation - Invalid File Type
**Actions:**
1. [ ] Try to upload a `.txt` or `.docx` file
2. [ ] Click "Upload File"

**Expected Results:**
- [ ] Red error message appears: "Only PDF files are allowed"
- [ ] File NOT uploaded
- [ ] Table unchanged

---

#### Test 3.4: Upload Validation - Missing Fields
**Actions:**
1. [ ] Leave Semester field empty
2. [ ] Select a PDF file
3. [ ] Click "Upload File"

**Expected Results:**
- [ ] Error message: "Please fill in all fields"
- [ ] File NOT uploaded

---

#### Test 3.5: Upload Validation - No File Selected
**Actions:**
1. [ ] Fill in all fields (Semester, Subject, Book)
2. [ ] Don't select any file
3. [ ] Click "Upload File"

**Expected Results:**
- [ ] Error message: "Please select a file"
- [ ] Upload button stays disabled

---

#### Test 3.6: Refresh Page - Files Persist
**Actions:**
1. [ ] With 4 files uploaded, refresh page (F5)

**Expected Results:**
- [ ] Page reloads
- [ ] Still logged in
- [ ] All 4 files still shown in table
- [ ] "Your Files (4)" header

---

### Phase 4: File Deletion

#### Test 4.1: Delete Single File
**Actions:**
1. [ ] Click "Delete" button on first file in table
2. [ ] Browser shows confirm dialog: "Are you sure you want to delete 'filename.pdf'?"
3. [ ] Click "OK" to confirm

**Expected Results:**
- [ ] Green success message: "File 'filename.pdf' deleted successfully!"
- [ ] File removed from table
- [ ] Header updates: "Your Files (3)"
- [ ] Table shows remaining 3 files

**Verify in S3:**
1. [ ] Go to S3 bucket
2. [ ] Navigate to file location
3. [ ] File no longer exists
4. [ ] Folder structure still exists (empty folder)

**Browser DevTools:**
- [ ] DELETE request to `http://localhost:8000/api/files/users/{user_id}/raw_data/.../filename.pdf`
- [ ] Status 200 response with message: "File deleted successfully"

---

#### Test 4.2: Delete - Cancel Confirmation
**Actions:**
1. [ ] Click "Delete" on any file
2. [ ] Click "Cancel" in confirmation dialog

**Expected Results:**
- [ ] Dialog closes
- [ ] File NOT deleted
- [ ] Table unchanged

---

#### Test 4.3: Delete All Files
**Actions:**
1. [ ] Delete remaining files one by one
2. [ ] Delete until table is empty

**Expected Results:**
- [ ] After deleting last file:
  - [ ] Header shows "Your Files (0)"
  - [ ] Message appears: "No files uploaded yet"
  - [ ] Empty state with prompt: "Upload your first PDF to get started"

---

### Phase 5: Navigation Between Pages

#### Test 5.1: Dashboard ↔ Chat Navigation
**Actions:**
1. [ ] From Dashboard, click "Chat" in navbar
2. [ ] URL changes to http://localhost:3000/chat
3. [ ] Chat page loads with:
   - [ ] "Chat with Your Textbooks" header
   - [ ] Semester and Subject filter inputs
   - [ ] Empty chat area: "No messages yet"
   - [ ] Input box at bottom
   - [ ] Send button
4. [ ] Click "Dashboard" in navbar
5. [ ] Returns to Dashboard page

**Expected Results:**
- [ ] Smooth navigation, no page reload flicker
- [ ] Navbar stays visible
- [ ] Active page highlighted in navbar
- [ ] URL updates correctly

---

#### Test 5.2: Logo Click Navigation
**Actions:**
1. [ ] From Chat page, click "📚 StudyRAG" logo in navbar
2. [ ] Should navigate to Dashboard

**Expected Results:**
- [ ] Logo acts as home button
- [ ] Returns to Dashboard

---

### Phase 6: Chat Interface (Placeholder Testing)

> **Note**: Chat is currently returning a placeholder message explaining that the vector DB is being set up. This is expected behavior until ChromaDB is deployed and PDFs are ingested. See `RAG_IMPLEMENTATION_PLAN.md` for implementation details.

#### Test 6.1: Send Chat Message Without Filters
**Actions:**
1. [ ] Go to Chat page
2. [ ] Type in input: "What is natural language processing?"
3. [ ] Click Send button (or press Enter)

**Expected Results:**
- [ ] Message appears in chat as user message (blue bubble, right side)
- [ ] Loading indicator appears (spinning icon)
- [ ] Bot response appears on left side (gray bubble)
- [ ] Response is a **placeholder message** explaining system status:
  - ✅ Confirms your PDFs are stored in S3
  - ✅ Explains vector DB setup is in progress
  - ✅ Lists next steps to get RAG working
- [ ] Input box clears after sending

**Browser DevTools:**
- [ ] POST request to `http://localhost:8000/api/chat/query`
- [ ] Request body:
  ```json
  {
    "question": "What is natural language processing?"
  }
  ```
- [ ] Response includes placeholder answer and metadata

---

#### Test 6.2: Chat With Filters
**Actions:**
1. [ ] Fill in filters:
   - Semester: `Y3S2`
   - Subject: `NLP`
2. [ ] Verify scope shows: "🎯 Searching in: Y3S2 > NLP"
3. [ ] Send message: "Explain speech recognition"

**Expected Results:**
- [ ] Request includes filters in body:
  ```json
  {
    "question": "Explain speech recognition",
    "semester": "Y3S2",
    "subject": "NLP"
  }
  ```

---

#### Test 6.3: Chat History Persists
**Actions:**
1. [ ] Send 3-4 messages
2. [ ] Navigate to Dashboard
3. [ ] Return to Chat page

**Expected Results:**
- [ ] Chat history cleared (messages don't persist across navigations)
- [ ] This is expected behavior (no chat persistence yet)

---

### Phase 7: Multi-User Isolation Testing

#### Test 7.1: Create Second User
**Actions:**
1. [ ] Logout from `testuser1@example.com`
2. [ ] Go to Signup page
3. [ ] Create new account:
   - Username: `testuser2`
   - Email: `testuser2@example.com`
   - Password: `Password456!`
4. [ ] Auto-login after signup

**Expected Results:**
- [ ] Redirects to Dashboard
- [ ] Navbar shows `testuser2` username
- [ ] Files list is EMPTY: "Your Files (0)"
- [ ] User 1's files NOT visible

**Verify in Supabase:**
- [ ] Second user exists in Authentication → Users
- [ ] Second user profile in user_profiles table
- [ ] Different `user_id` from user 1

---

#### Test 7.2: Upload Files as User 2
**Actions:**
1. [ ] As `testuser2@example.com`, upload 2 PDFs:
   - File 1: Y3S2/NLP/Book1
   - File 2: Y3S2/ComputerVision/Book1

**Expected Results:**
- [ ] Both files appear in User 2's Dashboard
- [ ] Header shows "Your Files (2)"

**Verify in S3:**
1. [ ] Go to S3 bucket
2. [ ] Check folder structure:
   ```
   users/
     ├── {user1_id}/
     │   └── raw_data/
     │       └── Y3S2/... (User 1's files)
     └── {user2_id}/
         └── raw_data/
             └── Y3S2/... (User 2's files)
   ```
3. [ ] Two separate user folders exist
4. [ ] Files isolated per user

---

#### Test 7.3: Switch Between Users - Verify Isolation
**Actions:**
1. [ ] Note User 2's files currently shown
2. [ ] Logout
3. [ ] Login as `testuser1@example.com`
4. [ ] Check Dashboard

**Expected Results:**
- [ ] User 1 sees ONLY their own files
- [ ] User 2's files NOT visible
- [ ] File counts different for each user

**Test Complete Isolation:**
- [ ] User 1 cannot see User 2's files
- [ ] User 1 cannot delete User 2's files (S3 paths different)
- [ ] Each user has separate folder in S3

---

### Phase 8: Error Handling & Edge Cases

#### Test 8.1: Wrong Login Credentials
**Actions:**
1. [ ] Logout
2. [ ] Try to login with:
   - Email: `testuser1@example.com`
   - Password: `WrongPassword123`

**Expected Results:**
- [ ] Red error message appears
- [ ] Message: "Login failed. Please check your credentials."
- [ ] User NOT logged in
- [ ] Stays on login page

---

#### Test 8.2: Signup with Existing Email
**Actions:**
1. [ ] Go to Signup page
2. [ ] Try to create account with existing email:
   - Username: `newuser`
   - Email: `testuser1@example.com` (already exists)
   - Password: `Password789!`

**Expected Results:**
- [ ] Error message appears
- [ ] Message indicates email already in use
- [ ] User NOT created

---

#### Test 8.3: Token Expiration
**Actions:**
1. [ ] Login successfully
2. [ ] Open DevTools → Application → Local Storage
3. [ ] Manually delete `studyrag_token` key
4. [ ] Try to upload a file or navigate to Dashboard

**Expected Results:**
- [ ] Automatically redirects to login page
- [ ] Shows "Please login to continue" or similar
- [ ] User must re-login

---

#### Test 8.4: Backend Offline
**Actions:**
1. [ ] Stop your FastAPI backend server (Ctrl+C in backend terminal)
2. [ ] Try to login from frontend

**Expected Results:**
- [ ] Error message appears
- [ ] Cannot login without backend
- [ ] Frontend shows connection error

**Recovery:**
- [ ] Restart backend: `cd backend && uvicorn main:app --reload --port 8000`
- [ ] Refresh frontend page
- [ ] Login should work again

---

#### Test 8.5: Upload Very Large File
**Actions:**
1. [ ] Try to upload a PDF > 100 MB

**Expected Results:**
- [ ] Upload may be slow but should complete
- [ ] Progress indicator shows
- [ ] File appears in list after upload

**Note**: Check backend for file size limits if upload fails.

---

### Phase 9: UI/UX Testing

#### Test 9.1: Responsive Design - Mobile View
**Actions:**
1. [ ] Open DevTools (F12)
2. [ ] Click "Toggle Device Toolbar" (Ctrl+Shift+M)
3. [ ] Select "iPhone 12 Pro" or similar mobile device
4. [ ] Navigate through all pages

**Expected Results:**
- [ ] Login/Signup forms fit mobile screen
- [ ] Navbar collapses or adapts for mobile
- [ ] Dashboard table scrolls horizontally if needed
- [ ] Upload form stacks vertically
- [ ] Chat interface works on mobile
- [ ] All buttons touchable/tappable

---

#### Test 9.2: Button States & Loading Indicators
**Check all buttons show loading states:**
- [ ] Login button: "Signing in..." while loading
- [ ] Signup button: "Creating account..." while loading
- [ ] Upload button: Shows spinner and "Uploading..."
- [ ] Delete button: Disabled during deletion
- [ ] Send chat button: Shows spinner while waiting

---

#### Test 9.3: Form Validation Visual Feedback
**Check input fields show validation:**
- [ ] Empty required fields highlighted in red
- [ ] Password minimum length enforced (8 chars)
- [ ] Email format validated
- [ ] File type validation (PDF only)

---

### Phase 10: Performance Testing

#### Test 10.1: Page Load Speed
**Actions:**
1. [ ] Open DevTools → Network tab
2. [ ] Refresh Dashboard page
3. [ ] Check "Load" time at bottom

**Expected Results:**
- [ ] Page loads in < 2 seconds
- [ ] No unnecessary API calls
- [ ] Images/assets load quickly

---

#### Test 10.2: API Call Efficiency
**Check API calls are optimized:**
- [ ] Login: Only 1 POST to `/auth/login`
- [ ] Dashboard load: Only 1 GET to `/api/files`
- [ ] Upload: Only 1 POST to `/api/files/upload`
- [ ] Delete: Only 1 DELETE request
- [ ] No duplicate/redundant calls

---

## 🎉 Final Verification Checklist

### Supabase Dashboard
- [ ] 2 users exist in Authentication → Users
- [ ] 2 user profiles in user_profiles table
- [ ] Email and username match for each user

### AWS S3 Console
- [ ] Two user folders: `users/{user1_id}/` and `users/{user2_id}/`
- [ ] Files stored in correct paths with semester/subject/book structure
- [ ] Deleted files no longer exist in S3
- [ ] File sizes match uploaded files

### Frontend LocalStorage
- [ ] Token and user data saved after login
- [ ] Cleared after logout
- [ ] Persists across page refreshes

### Browser Console
- [ ] No JavaScript errors
- [ ] No CORS errors
- [ ] No 404 or 500 errors (except expected ones during error testing)

---

## 📊 Summary Report

After completing all tests, fill in:

| Category | Tests Passed | Tests Failed | Notes |
|----------|-------------|--------------|-------|
| Navigation | __/6 | __/6 | |
| Authentication | __/4 | __/4 | |
| File Upload | __/6 | __/6 | |
| File Deletion | __/3 | __/3 | |
| Page Navigation | __/2 | __/2 | |
| Chat Interface | __/3 | __/3 | |
| Multi-User Isolation | __/3 | __/3 | |
| Error Handling | __/5 | __/5 | |
| UI/UX | __/3 | __/3 | |
| Performance | __/2 | __/2 | |
| **TOTAL** | **__/37** | **__/37** | |

---

## 🐛 Common Issues & Solutions

### Issue: CORS Error
**Symptom**: "Access to XMLHttpRequest blocked by CORS policy"  
**Solution**: Check backend CORS settings in `backend/main.py`:
```python
allow_origins=["http://localhost:3000"]
```

### Issue: Token Expired
**Symptom**: Redirected to login randomly  
**Solution**: Tokens expire after 1 hour. Just login again.

### Issue: Files Not Showing After Upload
**Symptom**: Upload succeeds but file doesn't appear  
**Solution**: 
1. Check backend logs for errors
2. Verify S3 credentials in backend `.env`
3. Check Network tab for failed GET `/api/files` request

### Issue: Cannot Delete Files
**Symptom**: Delete button doesn't work  
**Solution**:
1. Check file path/key in console
2. Verify user owns the file (security check in backend)
3. Check backend logs

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Deploy to Production**
   - Push frontend to Vercel
   - Deploy backend to AWS/Railway/Render
   - Update `NEXT_PUBLIC_API_URL` to production backend

2. **Implement Vector DB**
   - Set up ChromaDB/Pinecone
   - Ingest uploaded PDFs
   - Connect chat endpoint to RAG system

3. **Add Features**
   - File download
   - File preview
   - Batch upload
   - Search/filter files
   - Chat history persistence
   - User settings page

---

## ✅ Testing Complete!

Congratulations! You've thoroughly tested your StudyRAG Next.js frontend.

**Questions or Issues?** Check the README.md files or backend logs for troubleshooting.
