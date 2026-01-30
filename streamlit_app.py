import streamlit as st
from dotenv import load_dotenv
from StudyRAGSystem import (
    initialize_models,
    Catalog,
    build_study_agent,
    VECTORSTORE_DIR,
    COLLECTION_NAME
)
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="StudyRAG - AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .scope-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: #e8f4f8;
        border-radius: 1rem;
        font-size: 0.875rem;
        margin: 0.25rem;
        color: #1e88e5;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.messages = []
    st.session_state.active_semester = None
    st.session_state.active_subject = None
    st.session_state.active_books = []

@st.cache_resource
def load_system():
    """Load the RAG system components (cached)."""
    if not VECTORSTORE_DIR.exists():
        return None, None, None
    
    llm, embeddings = initialize_models()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR)
    )
    catalog = Catalog(vectorstore)
    study_agent = build_study_agent(llm, vectorstore, catalog)
    
    return catalog, study_agent, vectorstore

# Load system
catalog, study_agent, vectorstore = load_system()

if catalog is None:
    st.error("⚠️ Vector store not found. Please run ingestion first using `python StudyRAGSystem.py`")
    st.stop()

st.session_state.initialized = True

# Sidebar - Filters
with st.sidebar:
    st.title("📚 StudyRAG")
    st.markdown("### AI Study Assistant")
    st.divider()
    
    st.markdown("### 🎯 Scope Filters")
    
    # Get all available options
    all_semesters = ["All"] + catalog.list_semesters()
    
    # Semester filter
    semester_idx = 0
    if st.session_state.active_semester:
        try:
            semester_idx = all_semesters.index(st.session_state.active_semester)
        except ValueError:
            pass
    
    selected_semester = st.selectbox(
        "📅 Semester",
        options=all_semesters,
        index=semester_idx,
        help="Select a semester to filter subjects and books"
    )
    
    # Update semester in state
    if selected_semester == "All":
        st.session_state.active_semester = None
        current_semester = None
    else:
        st.session_state.active_semester = selected_semester
        current_semester = selected_semester
    
    # Subject filter (filtered by semester)
    subjects = catalog.list_subjects(current_semester)
    all_subjects = ["All"] + subjects
    
    subject_idx = 0
    if st.session_state.active_subject:
        try:
            subject_idx = all_subjects.index(st.session_state.active_subject)
        except ValueError:
            pass
    
    selected_subject = st.selectbox(
        "📖 Subject",
        options=all_subjects,
        index=subject_idx,
        help="Select a subject to filter books"
    )
    
    # Update subject in state
    if selected_subject == "All":
        st.session_state.active_subject = None
        current_subject = None
    else:
        st.session_state.active_subject = selected_subject
        current_subject = selected_subject
    
    # Books filter (filtered by semester and subject)
    books = catalog.list_books(current_semester, current_subject)
    book_options = [book['book_id'] for book in books]
    
    selected_books = st.multiselect(
        "📗 Books (optional)",
        options=book_options,
        default=st.session_state.active_books if st.session_state.active_books else [],
        help="Select specific books to search (leave empty for all)"
    )
    
    st.session_state.active_books = selected_books
    
    st.divider()
    
    # Show current scope
    st.markdown("### 📍 Current Scope")
    if st.session_state.active_semester:
        st.markdown(f'<span class="scope-badge">🗓️ {st.session_state.active_semester}</span>', unsafe_allow_html=True)
    if st.session_state.active_subject:
        st.markdown(f'<span class="scope-badge">📚 {st.session_state.active_subject}</span>', unsafe_allow_html=True)
    if st.session_state.active_books:
        for book in st.session_state.active_books:
            st.markdown(f'<span class="scope-badge">📖 {book}</span>', unsafe_allow_html=True)
    
    if not st.session_state.active_semester and not st.session_state.active_subject and not st.session_state.active_books:
        st.info("🌍 Searching all materials")
    
    # Clear button
    if st.button("🔄 Clear All Filters", use_container_width=True):
        st.session_state.active_semester = None
        st.session_state.active_subject = None
        st.session_state.active_books = []
        st.rerun()
    
    st.divider()
    
    # Statistics
    st.markdown("### 📊 Library Stats")
    total_semesters = len(catalog.list_semesters())
    total_subjects = len(catalog.list_subjects())
    total_books = len(catalog.list_books())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Semesters", total_semesters)
    with col2:
        st.metric("Subjects", total_subjects)
    with col3:
        st.metric("Books", total_books)

# Main area - Chat interface
st.title("💬 Chat with Your Textbooks")

# Display scope description
scope_parts = []
if st.session_state.active_semester:
    scope_parts.append(f"**{st.session_state.active_semester}**")
if st.session_state.active_subject:
    scope_parts.append(f"**{st.session_state.active_subject}**")
if st.session_state.active_books:
    scope_parts.append(f"Books: **{', '.join(st.session_state.active_books)}**")

if scope_parts:
    st.info(f"🎯 Searching in: {' | '.join(scope_parts)}")
else:
    st.info("🌍 Searching across all materials")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your textbooks..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        # Capture execution details
        import sys
        from io import StringIO
        
        # Create a string buffer to capture print statements
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        with st.spinner("🤔 Thinking..."):
            # Build state for agent
            state = {
                'messages': [HumanMessage(content=prompt)],
                'active_semester': st.session_state.active_semester,
                'active_subject': st.session_state.active_subject,
                'active_books': st.session_state.active_books
            }
            
            # Invoke agent
            result = study_agent.invoke(state)
            answer = result['messages'][-1].content
        
        # Restore stdout and get captured output
        sys.stdout = old_stdout
        debug_output = captured_output.getvalue()
        
        # Display debug info in expandable section
        if debug_output:
            with st.expander("🔍 View Execution Details", expanded=False):
                st.code(debug_output, language="text")
        
        # Display answer
        st.markdown(answer)
        
        # Add to chat history
        st.session_state.messages.append({"role": "assistant", "content": answer})

# Clear chat button
if st.session_state.messages:
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
