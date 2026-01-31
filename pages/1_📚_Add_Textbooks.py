import streamlit as st
from dotenv import load_dotenv
from backend.services.StudyRAGSystem import (
    IngestionPipeline,
    initialize_models,
    RAW_DATA_DIR,
    VECTORSTORE_DIR,
    CACHE_DIR,
    COLLECTION_NAME
)
from langchain_chroma import Chroma
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Add Textbooks - StudyRAG",
    page_icon="📚",
    layout="wide"
)

# ===== AUTHENTICATION CHECK =====
if not st.session_state.get('authenticated'):
    st.warning("⚠️ Please login to access this page")
    st.info("👉 Go to the **🔐 Login** page to sign in or create an account")
    
    if st.button("Go to Login Page", type="primary"):
        st.switch_page("pages/0_🔐_Login.py")
    
    st.stop()
# ================================

# Custom CSS
st.markdown("""
    <style>
    .book-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        margin: 0.5rem 0;
        border-left: 4px solid #1e88e5;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ingestion_log' not in st.session_state:
    st.session_state.ingestion_log = []
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None

@st.cache_resource
def load_embeddings():
    """Load embeddings model (cached)."""
    _, embeddings = initialize_models()
    return embeddings

def scan_library():
    """Scan the library and return structure."""
    embeddings = load_embeddings()
    pipeline = IngestionPipeline(embeddings)
    return pipeline.scan_library()

def get_existing_books():
    """Get books already in vectorstore."""
    embeddings = load_embeddings()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR)
    )
    
    collection = vectorstore._collection
    results = collection.get(limit=1000)
    
    existing_books = set()
    if results and 'metadatas' in results:
        for metadata in results['metadatas']:
            if metadata and 'source_path' in metadata:
                existing_books.add(metadata['source_path'])
    
    return existing_books

def run_ingestion(force_reingest=False):
    """Run the ingestion pipeline with UI updates."""
    embeddings = load_embeddings()
    pipeline = IngestionPipeline(embeddings)
    
    # Create progress containers
    progress_container = st.container()
    log_container = st.container()
    
    with progress_container:
        st.info("🔍 Scanning library structure...")
    
    # Scan library
    library = pipeline.scan_library()
    
    if not library:
        st.error("❌ No books found in the library structure!")
        st.info(f"Make sure PDFs are organized in: `{RAW_DATA_DIR}/semester/subject/book/*.pdf`")
        return
    
    total_books = sum(len(books) for books in library.values())
    
    with progress_container:
        st.success(f"✅ Found {total_books} book(s) across {len(library)} semester(s)")
    
    # Show what was found
    with st.expander("📋 Discovered Books", expanded=True):
        for semester, books in library.items():
            st.markdown(f"**📅 {semester}**: {len(books)} book(s)")
            for book in books:
                st.markdown(f"  - `{book['subject']}/{book['book_id']}`: {book['book_title']}")
    
    # Load or create vectorstore
    with progress_container:
        st.info("📊 Setting up vector store...")
    
    if not VECTORSTORE_DIR.exists():
        VECTORSTORE_DIR.mkdir(parents=True)
    
    try:
        vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(VECTORSTORE_DIR)
        )
    except Exception as e:
        st.error(f"❌ Error loading vector store: {e}")
        return
    
    # Check existing books
    if not force_reingest:
        existing_books = pipeline.get_existing_books_in_vectorstore(vectorstore)
        with progress_container:
            st.info(f"📋 {len(existing_books)} book(s) already in vector store")
    else:
        existing_books = set()
        with progress_container:
            st.warning("🔄 Force re-ingestion enabled (will process all books)")
    
    # Determine books to process
    books_to_process = []
    for semester, books in library.items():
        for book in books:
            if force_reingest or book['source_path'] not in existing_books:
                books_to_process.append((semester, book))
    
    if not books_to_process:
        st.success("✅ All books are already ingested!")
        return
    
    total_to_process = len(books_to_process)
    
    with progress_container:
        st.info(f"🔄 Processing {total_to_process} book(s)...")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_chunks = []
    processed_count = 0
    skipped_count = 0
    
    # Process each book
    for idx, (semester, book) in enumerate(books_to_process):
        current_book_num = idx + 1
        progress_pct = int((current_book_num / total_to_process) * 100)
        
        status_text.text(f"📖 Processing [{current_book_num}/{total_to_process}]: {book['book_title']}")
        progress_bar.progress(progress_pct / 100)
        
        # Log to container
        with log_container:
            with st.expander(f"📖 {book['book_title']}", expanded=False):
                st.text(f"Path: {book['source_path']}")
                
                chunks = pipeline.ingest_pdf(book)
                
                if chunks:
                    all_chunks.extend(chunks)
                    processed_count += 1
                    st.success(f"✅ Created {len(chunks)} chunks")
                else:
                    st.warning("⚠️ No chunks created")
    
    # Store embeddings
    if all_chunks:
        status_text.text("💾 Storing embeddings...")
        progress_bar.progress(100)
        
        try:
            vectorstore.add_documents(all_chunks)
            st.success("✅ All chunks embedded and stored successfully!")
        except Exception as e:
            st.error(f"❌ Error storing chunks: {e}")
            return
    
    # Summary
    st.markdown("---")
    st.markdown("### ✅ Ingestion Complete")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Books Processed", processed_count)
    with col2:
        st.metric("Books Skipped", skipped_count)
    with col3:
        st.metric("Total Chunks", len(all_chunks))
    
    # Save log
    log_file = CACHE_DIR / "ingestion_log.json"
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'books_processed': processed_count,
        'books_skipped': skipped_count,
        'total_chunks': len(all_chunks),
        'library_structure': library
    }
    
    CACHE_DIR.mkdir(exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    st.info(f"📝 Log saved to: `{log_file}`")
    
    # Clear cache to reload system
    st.cache_resource.clear()

# Main UI
st.title("📚 Add Textbooks")
st.markdown("Manage your textbook library and ingest new materials into the RAG system.")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📂 Library Overview", "➕ Add Books", "📊 Ingestion History"])

with tab1:
    st.markdown("### 📂 Current Library Structure")
    
    if st.button("🔄 Scan Library", use_container_width=True):
        with st.spinner("Scanning..."):
            st.session_state.last_scan = scan_library()
    
    if st.session_state.last_scan:
        library = st.session_state.last_scan
        
        if not library:
            st.warning("⚠️ No books found in the library!")
            st.info(f"📁 Add PDFs to: `{RAW_DATA_DIR}/semester/subject/book/*.pdf`")
        else:
            # Summary stats
            total_books = sum(len(books) for books in library.values())
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Semesters", len(library))
            with col2:
                st.metric("Total Books", total_books)
            
            st.markdown("---")
            
            # Show structure
            for semester, books in library.items():
                with st.expander(f"📅 {semester} ({len(books)} books)", expanded=False):
                    for book in books:
                        st.markdown(f"""
                        <div class="book-card">
                            <strong>📖 {book['book_title']}</strong><br>
                            📚 Subject: {book['subject']}<br>
                            🆔 Book ID: {book['book_id']}<br>
                            📁 Path: <code>{book['source_path']}</code>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Check what's already ingested
            st.markdown("---")
            st.markdown("### 📊 Ingestion Status")
            
            existing_books = get_existing_books()
            
            if existing_books:
                st.success(f"✅ {len(existing_books)} book(s) already ingested")
                
                new_books = []
                for semester, books in library.items():
                    for book in books:
                        if book['source_path'] not in existing_books:
                            new_books.append(book)
                
                if new_books:
                    st.info(f"📥 {len(new_books)} new book(s) ready to ingest")
                else:
                    st.success("✅ All discovered books are already ingested!")
            else:
                st.warning("⚠️ No books ingested yet. Use the 'Add Books' tab to start ingestion.")
    else:
        st.info("👆 Click 'Scan Library' to see your current library structure")
        
        st.markdown("---")
        st.markdown("### 📁 Expected Directory Structure")
        st.code("""
raw_data/
├── Y3S2/
│   ├── Time Series/
│   │   └── Textbook A/
│   │       └── textbook.pdf
│   └── Machine Learning/
│       └── Textbook B/
│           └── ml_book.pdf
└── Y4S1/
    └── Deep Learning/
        └── DL Fundamentals/
            └── dl_book.pdf
        """, language="text")

with tab2:
    st.markdown("### ➕ Ingest Textbooks")
    
    st.markdown("""
    Choose how to ingest your textbooks:
    - **Ingest New Books Only**: Only process books that haven't been added yet (recommended)
    - **Re-ingest All Books**: Process all books from scratch (overwrites existing data)
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Ingest New Books Only", use_container_width=True, type="primary"):
            run_ingestion(force_reingest=False)
    
    with col2:
        if st.button("🔄 Re-ingest All Books", use_container_width=True):
            with st.expander("⚠️ Confirmation Required", expanded=True):
                st.warning("This will re-process all books from scratch. This may take a while.")
                if st.button("✅ Yes, Re-ingest All", use_container_width=True, type="secondary"):
                    run_ingestion(force_reingest=True)

with tab3:
    st.markdown("### 📊 Ingestion History")
    
    log_file = CACHE_DIR / "ingestion_log.json"
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        st.markdown(f"**Last Ingestion**: {log_data['timestamp']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Books Processed", log_data['books_processed'])
        with col2:
            st.metric("Books Skipped", log_data['books_skipped'])
        with col3:
            st.metric("Total Chunks", log_data['total_chunks'])
        
        st.markdown("---")
        st.markdown("### 📚 Library Structure at Time of Ingestion")
        
        with st.expander("View Details", expanded=False):
            st.json(log_data['library_structure'])
    else:
        st.info("📝 No ingestion history found. Run an ingestion to create logs.")

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    This page allows you to manage your textbook library:
    
    1. **Scan** your `raw_data/` directory
    2. **Review** discovered books
    3. **Ingest** new books into the RAG system
    4. **Monitor** ingestion progress
    
    After ingestion, return to the main chat page to ask questions!
    """)
    
    st.markdown("---")
    st.markdown(f"**Data Directory**: `{RAW_DATA_DIR}`")
    st.markdown(f"**Vector Store**: `{VECTORSTORE_DIR}`")
