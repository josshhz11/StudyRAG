# 🎓 StudyRAG System

A RAG-based study system that helps you organize, navigate, and learn from your textbook collection using LangGraph and ChromaDB.

## 📁 Directory Structure

```
StudyRAG/
├── StudyRAGSystem.py       # Main application
├── RAGAgent.py            # Original single-doc RAG agent
├── library.yaml           # Library configuration
├── requirements.txt       # Python dependencies
├── raw_data/             # Your textbooks (organized by semester/subject/book)
│   └── Y3S2/            # Example: Year 3 Semester 2
│       └── Stats/       # Subject
│           └── ISLR2/   # Book folder
│               └── islr2.pdf
├── vectorstore/          # ChromaDB vector store (auto-created)
└── cache/               # Ingestion logs and cache (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

### 3. Organize Your Textbooks
Place your PDFs in the following structure:
```
raw_data/
  <semester>/           # e.g., Y3S2, Y4S1
    <subject>/         # e.g., Stats, OS, Marketing
      <book>/         # e.g., ISLR2, OSTEP
        *.pdf        # One or more PDF files
```

Example:
```
raw_data/
  Y3S2/
    Stats/
      ISLR2/
        islr2.pdf
      ESL/
        esl.pdf
    OS/
      OSTEP/
        ostep.pdf
```

### 4. Run the System
```bash
python StudyRAGSystem.py
```

## 📚 Features

### Feature 1: Ingestion Pipeline
Automatically discovers and embeds textbooks into the vector store.

**How it works:**
- Scans `raw_data/` directory recursively
- Detects semester → subject → book structure
- Chunks PDFs (1000 chars, 200 overlap)
- Embeds and stores with metadata
- Skips already-ingested books (smart incremental updates)

**Usage:**
1. Select "Ingestion Mode" from main menu
2. Choose:
   - Option 1: Ingest new books only (recommended)
   - Option 2: Re-ingest all books (force update)

### Feature 2: Study Agent with Navigation
Interactive study assistant with scope-based filtering.

**Navigation Commands:**
```
semesters          - List all available semesters
subjects           - List subjects in current semester
books              - List books in current scope

use <semester>     - Set active semester (e.g., "use Y3S2")
open <subject>     - Set active subject (e.g., "open Stats")
select <book>      - Add book to active scope (e.g., "select ISLR2")

clear              - Clear all filters (search everything)
ask <question>     - Ask a single question
chat               - Enter interactive chat mode
back               - Return to main menu
```

**Usage Examples:**

**Example 1: Study a specific subject**
```
> use Y3S2
> open Stats
> books
> chat
You: Explain the bias-variance tradeoff
```

**Example 2: Study a specific book**
```
> use Y3S2
> open Stats
> select ISLR2
> ask What is ridge regression?
```

**Example 3: Search across all materials**
```
> clear
> chat
You: What are operating system processes?
```

## 🔍 How Retrieval Works

### Metadata-Based Filtering
Each text chunk is stored with metadata:
- `semester`: e.g., "Y3S2"
- `subject`: e.g., "Stats"
- `book_id`: e.g., "ISLR2"
- `book_title`: e.g., "An Introduction to Statistical Learning"
- `source_path`: relative path from `raw_data/`
- `page`: page number in PDF

When you set an active scope, the system **automatically filters** the vector search:
- Active semester → searches only that semester
- Active subject → searches only that subject
- Active books → searches only those books
- No scope → searches everything

### Single Vector Store with Namespacing
All textbooks are stored in **one ChromaDB collection** with metadata filters. This is more efficient than separate databases and allows:
- Cross-book search within a subject
- Cross-subject search within a semester
- Global search across all materials

## 💾 Storage Estimates

### Per Textbook (rough estimate):
- Embeddings (1536-dim): ~30-50 MB
- Text + metadata + index: ~20-30 MB
- **Total: ~50-80 MB per 600-page textbook**

### For Your Library:
- 10 textbooks: ~500 MB - 800 MB
- 20 textbooks: ~1 GB - 1.6 GB
- 50 textbooks: ~2.5 GB - 4 GB

All stored locally in `vectorstore/` folder (visible in File Explorer).

## 🛠️ System Architecture

### Two-Phase Design

**Phase 1: Ingestion**
```
Raw PDFs → Load → Chunk → Add Metadata → Embed → Store in ChromaDB
```

**Phase 2: Study Agent**
```
User Query → Scope Filters → Vector Search → LLM Response → User
                ↑
        Navigation Commands (use/open/select)
```

### LangGraph Flow
```
User Input → LLM Node → Tool Call? → Retriever Node → LLM Node → Answer
                            ↓ No
                          Answer
```

### Scope State
```python
{
    'active_semester': 'Y3S2',      # Optional
    'active_subject': 'Stats',       # Optional
    'active_books': ['ISLR2', 'ESL'] # Optional (empty = all books)
}
```

## 📊 Vector Store Details

- **Location**: `./vectorstore/` (ChromaDB persistent directory)
- **Collection**: `study_materials` (single collection for all books)
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Visible in File Explorer**: Yes! Browse `C:\...\StudyRAG\vectorstore\`

## 🔄 Adding New Textbooks

1. Copy PDFs into `raw_data/<semester>/<subject>/<book>/`
2. Run the application
3. Select "Ingestion Mode"
4. Choose "Ingest new books only"
5. System automatically detects and processes new books

**No manual specification needed!** The system scans the directory structure automatically.

## 🎯 Design Decisions

### Why Single Vector Store (Pattern A)?
- ✅ Cross-book search within subjects
- ✅ Global search across all materials
- ✅ Efficient metadata filtering
- ✅ Easier to manage and backup
- ❌ Slightly more complex filtering logic

### Why Not Separate Databases (Pattern B)?
- ❌ Hard to search across multiple books/subjects
- ❌ More files to manage
- ❌ Duplicated overhead per database
- ✅ Simpler mental model (but impractical at scale)

### Why Incremental Ingestion?
- Saves time and API costs
- Only processes new/changed books
- Uses source_path as unique identifier
- Can force re-ingest when needed

## 🐛 Troubleshooting

### "Vector store not found"
- Run Ingestion Mode first to create the vector store

### "No books found in library"
- Check that PDFs are in `raw_data/<semester>/<subject>/<book>/*.pdf`
- Ensure the directory structure is correct (3 levels)

### "No relevant information found"
- Check your active scope (use `clear` to search everything)
- Verify the book was ingested successfully

### Ingestion takes too long
- This is normal for large PDFs (embedding is expensive)
- Use "Ingest new books only" to skip already-processed books

## 📝 Future Enhancements

- [ ] Web UI (Streamlit/Gradio)
- [ ] Multi-modal support (images, diagrams)
- [ ] Cross-reference detection (citations between books)
- [ ] Study notes and annotations
- [ ] Flashcard generation
- [ ] Progress tracking per subject
- [ ] Export study summaries

## 🤝 Contributing

This is a personal study tool, but feel free to fork and adapt for your needs!

## 📄 License

MIT License - Free to use and modify

---

**Built with:**
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
- [LangChain](https://github.com/langchain-ai/langchain) - LLM orchestration
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [OpenAI](https://openai.com/) - Embeddings and LLM

**Happy studying! 📖✨**
