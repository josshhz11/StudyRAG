# 🚀 Quick Start Guide

## First Time Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create .env file
```
OPENAI_API_KEY=your-api-key-here
```

### 3. Add Your First Textbook
```bash
# Create the structure
raw_data/Y3S2/Stats/ISLR2/

# Copy your PDF
# Place islr2.pdf in that folder
```

### 4. Run the System
```bash
python StudyRAGSystem.py
```

---

## Typical Workflow

### 📥 Adding New Books

1. **Organize PDFs in directory structure:**
   ```
   raw_data/
     Y3S2/              ← Semester
       Stats/           ← Subject
         ISLR2/         ← Book ID
           islr2.pdf    ← PDF file
   ```

2. **Run Ingestion:**
   - Start application → Select "1. Ingestion Mode"
   - Choose "1. Ingest new books only"
   - Wait for processing (shows progress)
   - Done! Books are now searchable

### 📖 Studying

1. **Start Study Mode:**
   - Start application → Select "2. Study Mode"

2. **Navigate to your scope:**
   ```
   > semesters          # See what semesters exist
   > use Y3S2          # Set active semester
   > subjects          # See subjects in Y3S2
   > open Stats        # Set active subject
   > books             # See books in Stats
   ```

3. **Ask questions:**
   ```
   > ask What is linear regression?
   ```
   
   Or enter chat mode:
   ```
   > chat
   You: Explain the bias-variance tradeoff
   Assistant: [Searches Stats books and answers]
   You: Give me an example with code
   Assistant: [Provides example]
   ```

---

## Common Commands

### Navigation
| Command | Description | Example |
|---------|-------------|---------|
| `semesters` | List all semesters | Shows: Y3S2, Y4S1 |
| `subjects` | List subjects in scope | Shows: Stats, OS |
| `books` | List books in scope | Shows available books |
| `use <semester>` | Set active semester | `use Y3S2` |
| `open <subject>` | Set active subject | `open Stats` |
| `select <book>` | Add book to scope | `select ISLR2` |
| `clear` | Clear all filters | Searches everything |

### Asking Questions
| Command | Description |
|---------|-------------|
| `ask <question>` | Ask a single question |
| `chat` | Enter interactive chat mode |
| `back` / `exit` | Return to previous menu |

---

## Usage Patterns

### Pattern 1: Focus on One Book
```
> use Y3S2
> open Stats
> select ISLR2
> chat
[Now you're only searching ISLR2]
```

### Pattern 2: Search Entire Subject
```
> use Y3S2
> open Stats
> chat
[Searches all Stats books in Y3S2]
```

### Pattern 3: Search Everything
```
> clear
> chat
[Searches all materials in library]
```

### Pattern 4: Compare Across Books
```
> use Y3S2
> open Stats
[Don't use 'select' - will search all Stats books]
> ask Compare how ISLR and ESL explain regularization
```

---

## Directory Structure Reference

```
StudyRAG/
├── 📄 StudyRAGSystem.py    # ← Run this file
├── 📄 README.md
├── 📄 library.yaml
├── 📄 requirements.txt
├── 📄 .env                 # Your API key (create this)
│
├── 📁 raw_data/            # ← Put your PDFs here
│   └── Y3S2/              # Semester folder
│       ├── Stats/         # Subject folder
│       │   ├── ISLR2/     # Book folder
│       │   │   └── islr2.pdf
│       │   └── ESL/
│       │       └── esl.pdf
│       └── OS/
│           └── OSTEP/
│               └── ostep.pdf
│
├── 📁 vectorstore/         # Auto-created (ChromaDB)
└── 📁 cache/              # Auto-created (logs)
```

---

## Tips & Tricks

### 💡 Efficient Ingestion
- **First time**: All books will be processed
- **Adding new books**: Use "Ingest new books only" - skips existing
- **Updating a book**: Use "Re-ingest all" or delete vectorstore folder

### 💡 Smart Searching
- **Specific questions**: Narrow scope (use + open + select)
- **Broad questions**: Wide scope (just use semester or subject)
- **Comparison**: Wide scope (search multiple books)

### 💡 Best Practices
- Use descriptive book folder names (ISLR2, not book1)
- Keep semester naming consistent (Y3S2, Y4S1, etc.)
- One main PDF per book folder (or split by chapters)

### 💡 Storage Management
- Each 600-page textbook ≈ 50-80 MB in vectorstore
- 10 books ≈ 500 MB - 800 MB
- All stored locally in vectorstore/

---

## Example Session

```
$ python StudyRAGSystem.py

=============================================================
🎓 STUDY RAG SYSTEM
=============================================================

MAIN MENU
=============================================================
1. Ingestion Mode (Add/Update textbooks)
2. Study Mode (Navigate and ask questions)
0. Exit

Select option: 2

✅ Study mode initialized!

=============================================================
📚 STUDY MODE - NAVIGATION
=============================================================

📍 Current Scope: All materials (no active scope)

> semesters
📅 Available semesters: Y3S2

> use Y3S2
✅ Active semester: Y3S2

> subjects
📚 Available subjects: Stats, OS

> open Stats
✅ Active subject: Stats

> books
📖 Available books:
   - ISLR2: An Introduction to Statistical Learning
   - ESL: Elements of Statistical Learning

> chat

💬 CHAT MODE
================================================================
📍 Scope: Semester: Y3S2 | Subject: Stats
Type 'exit' to return to navigation menu

📖 You: What is the bias-variance tradeoff?
🤔 Assistant: The bias-variance tradeoff is a fundamental concept 
in statistical learning...

[Citation: ISLR2, Chapter 2, p. 34]

📖 You: Give me an example
🤔 Assistant: Consider a linear regression model...

📖 You: exit

> back

MAIN MENU
=============================================================
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Vector store not found" | Run Ingestion Mode first |
| "No books found" | Check PDF location: raw_data/semester/subject/book/*.pdf |
| "No relevant information" | Use `clear` to search all materials |
| Ingestion is slow | Normal! Embedding is expensive. Use incremental mode. |
| Import errors | Run `pip install -r requirements.txt` |

---

## Next Steps

1. ✅ Set up the system
2. ✅ Add your first textbook
3. ✅ Run ingestion
4. ✅ Try study mode
5. 📚 Add more textbooks as needed
6. 🎓 Study efficiently!

**For detailed info, see [README.md](README.md)**
