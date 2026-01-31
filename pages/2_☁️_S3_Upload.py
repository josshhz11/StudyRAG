import streamlit as st
from dotenv import load_dotenv
from storage_adapter import get_storage_adapter, S3StorageAdapter
import os
from collections import defaultdict
from pathlib import Path

load_dotenv()

st.set_page_config(
    page_title="S3 File Manager - StudyRAG",
    page_icon="☁️",
    layout="wide"
)

# Custom CSS for drag-drop and folder tree
st.markdown("""
    <style>
    .upload-zone {
        border: 2px dashed #1e88e5;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        transition: all 0.3s;
    }
    .upload-zone:hover {
        background-color: #e3f2fd;
        border-color: #1565c0;
    }
    .folder-tree {
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        padding: 1rem;
        background-color: #f5f5f5;
        border-radius: 5px;
        max-height: 500px;
        overflow-y: auto;
    }
    .folder-item {
        padding: 0.25rem 0;
        cursor: pointer;
    }
    .folder-item:hover {
        background-color: #e0e0e0;
    }
    .file-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
        transition: box-shadow 0.2s;
    }
    .file-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title("☁️ S3 File Manager")

# Check storage mode and initialize
storage_mode = os.getenv('STORAGE_MODE', 'local')

if storage_mode != 's3':
    st.warning("⚠️ Storage mode is set to 'local'. Change STORAGE_MODE='s3' in .env to use S3.")
    
    # Show toggle to switch
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Switch to S3 mode to enable cloud storage features.")
    with col2:
        if st.button("🔄 Switch to S3"):
            st.code("Update your .env file:\nSTORAGE_MODE=s3", language="bash")
    st.stop()

# Initialize S3 adapter
try:
    storage = get_storage_adapter('s3')
    st.success(f"✅ Connected to S3: {os.getenv('S3_BUCKET_NAME')}")
except Exception as e:
    st.error(f"❌ Failed to connect to S3: {e}")
    with st.expander("🔍 Troubleshooting"):
        st.markdown("""
        **Check your .env file has:**
        - `AWS_ACCESS_KEY_ID=AKIA...`
        - `AWS_SECRET_ACCESS_KEY=...`
        - `AWS_REGION=us-east-2`
        - `S3_BUCKET_NAME=studyrag-prototyping-s3-bucket-1`
        
        **Test connection:**
        ```bash
        python test_connection.py
        ```
        """)
    st.stop()

# Initialize session state for folder selection
if 'selected_semester' not in st.session_state:
    st.session_state.selected_semester = None
if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None
if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

# Helper function to build folder tree
def build_folder_tree(pdfs):
    """Build a nested folder structure from PDFs."""
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for pdf in pdfs:
        semester = pdf['semester']
        subject = pdf['subject']
        book_id = pdf['book_id']
        tree[semester][subject][book_id].append(pdf)
    
    return tree

# Helper function to display folder tree
def display_folder_tree(tree, selectable=False):
    """Display folder tree with optional selection."""
    if not tree:
        st.info("📁 No files found. Upload your first textbook!")
        return
    
    st.markdown('<div class="folder-tree">', unsafe_allow_html=True)
    
    for semester in sorted(tree.keys()):
        # Semester level
        semester_expanded = st.expander(f"📅 {semester}", expanded=True)
        
        with semester_expanded:
            for subject in sorted(tree[semester].keys()):
                # Subject level
                st.markdown(f"**📚 {subject}**")
                
                for book_id in sorted(tree[semester][subject].keys()):
                    # Book level
                    files = tree[semester][subject][book_id]
                    file_count = len(files)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;📖 {book_id} ({file_count} file{'s' if file_count > 1 else ''})")
                    
                    with col2:
                        if selectable:
                            if st.button("📂 Select", key=f"select_{semester}_{subject}_{book_id}"):
                                st.session_state.selected_semester = semester
                                st.session_state.selected_subject = subject
                                st.session_state.selected_book = book_id
                                st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_folder_{semester}_{subject}_{book_id}"):
                            # Delete all files in this folder
                            for file in files:
                                storage.delete_file(file['key'])
                            st.success(f"Deleted {book_id}")
                            st.session_state.refresh_trigger += 1
                            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["📤 Upload Files", "📂 Browse Files", "⚙️ File Operations"])

# ============================================================================
# TAB 1: UPLOAD FILES
# ============================================================================
with tab1:
    st.markdown("### 📤 Upload New Textbook")
    
    # Get current files to populate folder options
    existing_pdfs = storage.list_pdfs()
    folder_tree = build_folder_tree(existing_pdfs)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📁 Destination Folder")
        
        # Option: Select or create folder
        folder_mode = st.radio(
            "Choose folder option:",
            ["Select Existing Folder", "Create New Folder"],
            key="folder_mode"
        )
        
        if folder_mode == "Select Existing Folder" and folder_tree:
            all_semesters = sorted(folder_tree.keys())
            semester = st.selectbox("📅 Semester", options=all_semesters, key="sel_semester")
            
            if semester:
                all_subjects = sorted(folder_tree[semester].keys())
                subject = st.selectbox("📚 Subject", options=all_subjects, key="sel_subject")
                
                if subject:
                    all_books = sorted(folder_tree[semester][subject].keys())
                    book_id = st.selectbox("📖 Book", options=all_books, key="sel_book")
                else:
                    book_id = None
            else:
                subject = None
                book_id = None
        
        elif folder_mode == "Create New Folder" or not folder_tree:
            semester = st.text_input("📅 Semester (e.g., Y3S2)", key="new_semester")
            subject = st.text_input("📚 Subject (e.g., NLP)", key="new_subject")
            book_id = st.text_input("📖 Book ID (e.g., NLTK_Book)", key="new_book")
        else:
            semester = None
            subject = None
            book_id = None
    
    with col2:
        st.markdown("#### 📄 Select File(s)")
        
        # File uploader with drag-drop
        uploaded_files = st.file_uploader(
            "Drag and drop PDF files here",
            type=['pdf'],
            accept_multiple_files=True,
            key="file_uploader",
            help="You can select multiple PDF files at once"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) selected")
            with st.expander("📋 File List", expanded=True):
                for f in uploaded_files:
                    st.text(f"📄 {f.name} ({f.size / 1024:.1f} KB)")
    
    # Upload button
    st.markdown("---")
    
    if semester and subject and book_id:
        target_path = f"{semester}/{subject}/{book_id}"
        st.info(f"📍 Target: **{target_path}**")
        
        can_upload = uploaded_files and semester and subject and book_id
        
        if st.button("📤 Upload to S3", type="primary", disabled=not can_upload, use_container_width=True):
            progress_bar = st.progress(0)
            status = st.empty()
            
            success_count = 0
            for idx, file in enumerate(uploaded_files):
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status.text(f"Uploading {file.name}...")
                
                s3_key = f"{target_path}/{file.name}"
                file.seek(0)
                if storage.upload_file(file, s3_key):
                    success_count += 1
            
            status.text("Complete!")
            st.success(f"✅ Uploaded {success_count}/{len(uploaded_files)} file(s)")
            st.info("💡 Go to **Add Textbooks** page to ingest into vector store")
            st.session_state.refresh_trigger += 1
    else:
        st.warning("⚠️ Please fill in semester, subject, and book ID")

# ============================================================================
# TAB 2: BROWSE FILES
# ============================================================================
with tab2:
    st.markdown("### 📂 Browse Files in S3")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Browse your file library organized by semester, subject, and book.")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.refresh_trigger += 1
            st.rerun()
    
    # Get and display files
    pdfs = storage.list_pdfs()
    
    if pdfs:
        tree = build_folder_tree(pdfs)
        
        st.markdown(f"**Total:** {len(pdfs)} file(s) across {len(tree)} semester(s)")
        st.markdown("---")
        
        # Display folder tree
        display_folder_tree(tree, selectable=False)
        
    else:
        st.info("📁 No files found. Go to **Upload Files** tab to add your first textbook!")

# ============================================================================
# TAB 3: FILE OPERATIONS
# ============================================================================
with tab3:
    st.markdown("### ⚙️ File Operations")
    
    pdfs = storage.list_pdfs()
    
    if not pdfs:
        st.info("No files to manage. Upload files first!")
    else:
        st.markdown("#### 🔍 Search and Manage Files")
        
        # Search box
        search_term = st.text_input("🔎 Search files", placeholder="Type to filter files...")
        
        # Filter PDFs
        filtered_pdfs = pdfs
        if search_term:
            filtered_pdfs = [
                pdf for pdf in pdfs
                if search_term.lower() in pdf['book_title'].lower()
                or search_term.lower() in pdf['subject'].lower()
                or search_term.lower() in pdf['semester'].lower()
            ]
        
        st.write(f"Showing {len(filtered_pdfs)} of {len(pdfs)} files")
        
        # Display files as cards
        for pdf in filtered_pdfs:
            with st.container():
                st.markdown(f"""
                <div class="file-card">
                    <strong>📄 {pdf['book_title']}</strong><br>
                    <small>📅 {pdf['semester']} | 📚 {pdf['subject']} | 📖 {pdf['book_id']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.text(f"Size: {pdf['size'] / 1024:.1f} KB")
                    with st.expander("🔗 S3 Details"):
                        st.code(pdf['key'], language="text")
                
                with col2:
                    st.text("")  # Spacing
                
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{pdf['key']}"):
                        if storage.delete_file(pdf['key']):
                            st.success("Deleted!")
                            st.session_state.refresh_trigger += 1
                            st.rerun()
                        else:
                            st.error("Delete failed")