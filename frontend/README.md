# StudyRAG Frontend

Modern Next.js 14 frontend for StudyRAG - AI Study Assistant

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

The `.env.local` file is already created with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Make sure your FastAPI backend is running on port 8000.

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js 14 App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home (redirects to login/dashboard)
│   ├── globals.css        # Global styles with Tailwind
│   ├── login/
│   │   └── page.tsx       # Login page
│   ├── signup/
│   │   └── page.tsx       # Signup page
│   ├── dashboard/
│   │   └── page.tsx       # File management (upload, list, delete)
│   └── chat/
│       └── page.tsx       # RAG chat interface
├── components/
│   ├── Navbar.tsx         # Navigation bar for authenticated pages
│   └── ProtectedRoute.tsx # Auth wrapper for protected pages
├── lib/
│   ├── api.ts             # API client (axios) for backend communication
│   ├── auth.ts            # JWT token management (localStorage)
│   └── utils.ts           # Utility functions
├── types/
│   └── index.ts           # TypeScript interfaces matching backend models
└── package.json           # Dependencies
```

## 🔐 Authentication Flow

1. **Signup/Login** → User provides credentials
2. **Backend API** → Returns JWT token + user info
3. **Save Token** → Token stored in localStorage
4. **Protected Routes** → All pages check for token
5. **Auto-redirect** → If no token, redirect to /login

## 📄 Pages Overview

### Public Pages (No Auth Required)

- **`/login`** - Sign in page
- **`/signup`** - Create account page

### Protected Pages (Auth Required)

- **`/dashboard`** - File management
  - Upload PDF files (with semester/subject/book metadata)
  - View all uploaded files in a table
  - Delete files with confirmation
- **`/chat`** - RAG chat interface
  - Ask questions about your textbooks
  - Filter by semester/subject
  - View chat history

## 🛠️ Key Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe code
- **TailwindCSS** - Utility-first styling
- **Axios** - HTTP client with interceptors
- **lucide-react** - Icon library

## 🔗 Backend Integration

All API calls are in `lib/api.ts`:

### Auth Endpoints
- `POST /auth/signup` - Create account
- `POST /auth/login` - Sign in
- `GET /auth/me` - Get user profile
- `POST /auth/logout` - Sign out

### File Endpoints
- `GET /api/files` - List user's files
- `POST /api/files/upload` - Upload PDF (multipart/form-data)
- `DELETE /api/files/{fileKey}` - Delete file

### Chat Endpoint
- `POST /api/chat/query` - Send RAG query

## 📝 Usage Examples

### Login
```typescript
import { login, setToken, setUser } from "@/lib/api";

const response = await login(email, password);
setToken(response.access_token);
setUser(response.user);
```

### Upload File
```typescript
import { uploadFile } from "@/lib/api";

await uploadFile(file, "Y3S2", "NLP", "TextbookCh1");
```

### Chat Query
```typescript
import { sendChatQuery } from "@/lib/api";

const response = await sendChatQuery({
  question: "What is NLP?",
  semester: "Y3S2",
  subject: "NLP"
});
```

## 🎨 Styling

Uses Tailwind CSS with custom theme colors:

- **Primary**: Blue (`hsl(221.2 83.2% 53.3%)`)
- **Destructive**: Red for delete actions
- **Muted**: Gray for secondary elements

Customize colors in `tailwind.config.ts`.

## 🚢 Deployment to Vercel

### Option 1: GitHub Integration (Recommended)

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "Import Project"
4. Select your GitHub repo
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your production backend URL
6. Deploy!

### Option 2: Vercel CLI

```bash
npm install -g vercel
vercel
```

Follow prompts, add production API URL when asked.

## 🔧 Development Tips

### Hot Reload
Next.js automatically reloads when you save files. No need to restart!

### TypeScript Errors
Check types with:
```bash
npm run build
```

### API URL Configuration
- Development: `http://localhost:8000` (default)
- Production: Set `NEXT_PUBLIC_API_URL` in Vercel env vars

## 📦 Build for Production

```bash
npm run build
npm start
```

This creates an optimized production build.

## 🐛 Troubleshooting

### CORS Errors
Make sure your FastAPI backend has CORS enabled for your frontend URL:

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Token Expired
Tokens expire after 1 hour. User will be auto-redirected to login.

### File Upload Fails
Check:
1. Backend is running
2. File is PDF format
3. All fields (semester, subject, book) are filled

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 🎉 You're Ready!

Your Next.js frontend is fully set up and connected to your FastAPI backend. Start the dev server and test the authentication flow!
