from dotenv import load_dotenv
import os
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.tools import tool
import json
from datetime import datetime

# Global constants
BASE_DIR = Path(__file__).parent
RAW_DATA_DIR = BASE_DIR / "raw_data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
CACHE_DIR = BASE_DIR / "cache"
COLLECTION_NAME = "study_materials"

SYSTEM_PROMPT = """
You are an intelligent study assistant who helps students navigate and learn from their textbook collection.
You have access to a retriever tool that searches the student's textbook library.
The library is organized by semester → subject → book.

When answering questions:
1. Use the retriever tool to find relevant information
2. Always cite specific sources (book name, page number)
3. Provide clear, educational explanations
4. If the answer isn't in the current scope, say so

Current scope: {scope_description}
"""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    active_semester: Optional[str]
    active_subject: Optional[str]
    active_books: List[str]


# ============================================================================
# PHASE 1: INGESTION PIPELINE
# ============================================================================

class IngestionPipeline:
    """Handles PDF ingestion, chunking, and embedding into vector store."""
    
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def scan_library(self) -> Dict[str, List[Dict]]:
        """
        Scan the raw_data directory and return discovered books.
        Structure: raw_data/semester/subject/book/*.pdf
        """
        library_structure = {}
        
        if not RAW_DATA_DIR.exists():
            print(f"Warning: {RAW_DATA_DIR} does not exist")
            return library_structure
        
        # Scan directory structure
        for semester_dir in RAW_DATA_DIR.iterdir():
            if not semester_dir.is_dir():
                continue
            
            semester = semester_dir.name
            library_structure[semester] = []
            
            for subject_dir in semester_dir.iterdir():
                if not subject_dir.is_dir():
                    continue
                
                subject = subject_dir.name
                
                # Look for PDFs in subject/book directories
                for book_dir in subject_dir.iterdir():
                    if not book_dir.is_dir():
                        continue
                    
                    book_id = book_dir.name
                    
                    # Find all PDFs in this book directory
                    pdf_files = list(book_dir.glob("*.pdf"))
                    
                    for pdf_file in pdf_files:
                        library_structure[semester].append({
                            'semester': semester,
                            'subject': subject,
                            'book_id': book_id,
                            'book_title': pdf_file.stem,
                            'pdf_path': str(pdf_file),
                            'source_path': str(pdf_file.relative_to(RAW_DATA_DIR))
                        })
        
        return library_structure
    
    def get_existing_books_in_vectorstore(self, vectorstore) -> set:
        """Query vectorstore to find which books have already been ingested."""
        try:
            # Get a sample of documents to check metadata
            collection = vectorstore._collection
            results = collection.get(limit=1000)  # Sample to find unique books
            
            existing_books = set()
            if results and 'metadatas' in results:
                for metadata in results['metadatas']:
                    if metadata and 'source_path' in metadata:
                        existing_books.add(metadata['source_path'])
            
            return existing_books
        except:
            return set()
    
    def ingest_pdf(self, book_info: Dict) -> int:
        """
        Load a PDF, chunk it, and return documents with metadata.
        Returns number of chunks created.
        """
        pdf_path = book_info['pdf_path']
        
        if not os.path.exists(pdf_path):
            print(f"  ⚠️  PDF not found: {pdf_path}")
            return 0
        
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            # Add metadata to each page
            for page in pages:
                page.metadata.update({
                    'semester': book_info['semester'],
                    'subject': book_info['subject'],
                    'book_id': book_info['book_id'],
                    'book_title': book_info['book_title'],
                    'source_path': book_info['source_path']
                })
            
            # Chunk the pages
            chunks = self.text_splitter.split_documents(pages)
            
            return chunks
            
        except Exception as e:
            print(f"  ❌ Error processing {pdf_path}: {str(e)}")
            return []
    
    def ingest_all(self, force_reingest: bool = False):
        """
        Scan library and ingest all PDFs into the vector store.
        
        Args:
            force_reingest: If True, re-ingest all books. If False, skip already ingested books.
        """
        print("\n" + "="*70)
        print("📚 STARTING INGESTION PIPELINE")
        print("="*70)
        
        # Scan the library
        print("\n🔍 Scanning library structure...")
        library = self.scan_library()
        
        if not library:
            print("❌ No books found in the library structure!")
            print(f"   Make sure PDFs are organized in: {RAW_DATA_DIR}/semester/subject/book/*.pdf")
            return
        
        # Display what was found
        total_books = sum(len(books) for books in library.values())
        print(f"✅ Found {total_books} book(s) across {len(library)} semester(s)")
        
        for semester, books in library.items():
            print(f"\n  📅 {semester}: {len(books)} book(s)")
            for book in books:
                print(f"     - {book['subject']}/{book['book_id']}: {book['book_title']}")
        
        # Load or create vectorstore
        print("\n📊 Setting up vector store...")
        if not VECTORSTORE_DIR.exists():
            VECTORSTORE_DIR.mkdir(parents=True)
        
        try:
            vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=str(VECTORSTORE_DIR)
            )
            print("✅ Vector store loaded")
        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return
        
        # Check which books are already ingested
        if not force_reingest:
            existing_books = self.get_existing_books_in_vectorstore(vectorstore)
            print(f"📋 {len(existing_books)} book(s) already in vector store")
        else:
            existing_books = set()
            print("🔄 Force re-ingestion enabled (will process all books)")
        
        # Process each book
        print("\n" + "="*70)
        print("🔄 PROCESSING BOOKS")
        print("="*70)
        
        all_chunks = []
        processed_count = 0
        skipped_count = 0
        
        # Calculate total books to process
        books_to_process = []
        for semester, books in library.items():
            for book in books:
                if force_reingest or book['source_path'] not in existing_books:
                    books_to_process.append((semester, book))
        
        total_to_process = len(books_to_process)
        current_book_num = 0
        
        for semester, books in library.items():
            for book in books:
                source_path = book['source_path']
                
                # Skip if already ingested
                if not force_reingest and source_path in existing_books:
                    print(f"\n⏭️  Skipping {book['book_title']} (already ingested)")
                    skipped_count += 1
                    continue
                
                current_book_num += 1
                progress_pct = int((current_book_num / total_to_process) * 100) if total_to_process > 0 else 0
                
                print(f"\n📖 Processing [{current_book_num}/{total_to_process}] ({progress_pct}%): {book['book_title']}")
                print(f"   Path: {source_path}")
                
                chunks = self.ingest_pdf(book)
                
                if chunks:
                    all_chunks.extend(chunks)
                    processed_count += 1
                    print(f"   ✅ Created {len(chunks)} chunks")
                else:
                    print("   ⚠️  No chunks created")
        
        # Add all chunks to vectorstore
        if all_chunks:
            print("\n" + "="*70)
            print("💾 STORING EMBEDDINGS")
            print("="*70)
            print(f"Embedding and storing {len(all_chunks)} chunks...")
            
            try:
                vectorstore.add_documents(all_chunks)
                print("✅ All chunks embedded and stored successfully!")
            except Exception as e:
                print(f"❌ Error storing chunks: {e}")
                return
        
        # Summary
        print("\n" + "="*70)
        print("✅ INGESTION COMPLETE")
        print("="*70)
        print("📊 Summary:")
        print(f"   - Books processed: {processed_count}")
        print(f"   - Books skipped: {skipped_count}")
        print(f"   - Total chunks: {len(all_chunks)}")
        print(f"   - Vector store location: {VECTORSTORE_DIR}")
        
        # Save ingestion log
        log_file = CACHE_DIR / "ingestion_log.json"
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'books_processed': processed_count,
            'books_skipped': skipped_count,
            'total_chunks': len(all_chunks),
            'library_structure': library
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"   - Log saved to: {log_file}")


# ============================================================================
# PHASE 2: CATALOG & NAVIGATION
# ============================================================================

class Catalog:
    """Manages library navigation and metadata queries."""
    
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self._cache = None
    
    def _get_all_metadata(self) -> List[Dict]:
        """Fetch all metadata from vectorstore (cached)."""
        if self._cache is not None:
            return self._cache
        
        try:
            collection = self.vectorstore._collection
            results = collection.get()
            
            if results and 'metadatas' in results:
                self._cache = [m for m in results['metadatas'] if m]
                return self._cache
        except:
            pass
        
        return []
    
    def list_semesters(self) -> List[str]:
        """Get all unique semesters in the library."""
        metadata = self._get_all_metadata()
        semesters = sorted(set(m.get('semester', '') for m in metadata if m.get('semester')))
        return semesters
    
    def list_subjects(self, semester: Optional[str] = None) -> List[str]:
        """Get all subjects, optionally filtered by semester."""
        metadata = self._get_all_metadata()
        
        if semester:
            # Case-insensitive comparison - compare both in lowercase
            metadata = [m for m in metadata if m.get('semester', '').lower() == semester.lower()]
        
        subjects = sorted(set(m.get('subject', '') for m in metadata if m.get('subject')))
        return subjects
    
    def list_books(self, semester: Optional[str] = None, subject: Optional[str] = None) -> List[Dict]:
        """Get all books, optionally filtered by semester and/or subject."""
        metadata = self._get_all_metadata()
        
        if semester:
            # Case-insensitive comparison
            metadata = [m for m in metadata if m.get('semester', '').lower() == semester.lower()]
        
        if subject:
            # Case-insensitive comparison
            metadata = [m for m in metadata if m.get('subject', '').lower() == subject.lower()]
        
        # Get unique books
        books_dict = {}
        for m in metadata:
            book_id = m.get('book_id', '')
            if book_id and book_id not in books_dict:
                books_dict[book_id] = {
                    'book_id': book_id,
                    'book_title': m.get('book_title', ''),
                    'subject': m.get('subject', ''),
                    'semester': m.get('semester', '')
                }
        
        return sorted(books_dict.values(), key=lambda x: x['book_id'])
    
    def get_scope_description(self, state: AgentState) -> str:
        """Generate a human-readable description of the current scope."""
        parts = []
        
        if state.get('active_semester'):
            parts.append(f"Semester: {state['active_semester']}")
        
        if state.get('active_subject'):
            parts.append(f"Subject: {state['active_subject']}")
        
        if state.get('active_books') and len(state['active_books']) > 0:
            if len(state['active_books']) == 1:
                parts.append(f"Book: {state['active_books'][0]}")
            else:
                parts.append(f"Books: {', '.join(state['active_books'])}")
        
        if not parts:
            return "All materials (no active scope)"
        
        return " | ".join(parts)


# ============================================================================
# PHASE 2: STUDY AGENT
# ============================================================================

def create_retriever_tool(vectorstore, state_getter):
    """Create the retriever tool with scope-aware filtering."""
    
    @tool
    def retriever_tool(query: str) -> str:
        """
        Search the textbook library for relevant information.
        This tool automatically respects the current active scope (semester/subject/books).
        """
        # Get current state
        state = state_getter()
        
        # Build metadata filter with proper ChromaDB format
        filter_conditions = []
        
        if state.get('active_semester'):
            # Case-insensitive: get actual value from vectorstore
            filter_conditions.append({'semester': state['active_semester']})
        
        if state.get('active_subject'):
            # Case-insensitive: get actual value from vectorstore
            filter_conditions.append({'subject': state['active_subject']})
        
        if state.get('active_books') and len(state['active_books']) > 0:
            filter_conditions.append({'book_id': {'$in': state['active_books']}})
        
        # Debug print: show what filters are being applied
        print("\n🔍 Search Debug Info:")
        print(f"   Query: '{query}'")
        
        # ChromaDB requires $and operator for multiple conditions
        where_filter = None
        if len(filter_conditions) == 0:
            where_filter = None
            print("   Active Filters: None (searching all materials)")
        elif len(filter_conditions) == 1:
            where_filter = filter_conditions[0]
            print(f"   Active Filters: {where_filter}")
        else:
            where_filter = {'$and': filter_conditions}
            print(f"   Active Filters: {where_filter}")
        
        # Perform retrieval
        try:
            if where_filter:
                docs = vectorstore.similarity_search(
                    query,
                    k=5,
                    filter=where_filter
                )
            else:
                docs = vectorstore.similarity_search(query, k=5)
            
            # Debug print: show results count
            print(f"   Results Found: {len(docs)} documents")
            if docs:
                # Show which books the results came from
                books_found = set(doc.metadata.get('book_title', 'Unknown') for doc in docs)
                print(f"   Sources: {', '.join(books_found)}")
            else:
                print("   ⚠️  No results matched your scope filters!")
            
            if not docs:
                return "No relevant information found in the current scope. Try using 'clear' to search all materials or adjust your scope."
            
            # Format results
            results = []
            for i, doc in enumerate(docs):
                metadata = doc.metadata
                book_title = metadata.get('book_title', 'Unknown')
                page_num = metadata.get('page', 'N/A')
                subject = metadata.get('subject', 'Unknown')
                semester = metadata.get('semester', 'Unknown')
                
                # Enhanced source info with clear page number
                source_info = f"📚 {book_title} | 📄 Page {page_num} | 📁 {semester}/{subject}"
                results.append(f"[{source_info}]\n{doc.page_content}")
            
            return "\n\n---\n\n".join(results)
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return f"Error during retrieval: {str(e)}"
    
    return retriever_tool


def initialize_models():
    """Initialize LLM and embeddings models."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return llm, embeddings


def create_agent_nodes(llm, tools, catalog, current_state_ref):
    """Create the agent node functions with navigation capabilities."""
    tools_dict = {t.name: t for t in tools}
    
    def call_llm(state: AgentState) -> AgentState:
        """Function to call the LLM with the current state."""
        messages = list(state['messages'])
        
        # Get scope description
        scope_desc = catalog.get_scope_description(state)
        system_prompt = SYSTEM_PROMPT.format(scope_description=scope_desc)
        
        messages = [SystemMessage(system_prompt)] + messages
        message = llm.invoke(messages)
        
        return {'messages': [message]}
    
    def take_action(state: AgentState) -> AgentState:
        """Execute tool calls from the LLM's response."""
        # Update the current state reference for tools
        current_state_ref['state'] = state
        
        tool_calls = state['messages'][-1].tool_calls
        results = []
        
        for t in tool_calls:
            print(f"\n🔧 Calling Tool: {t['name']}")
            
            if t['name'] not in tools_dict:
                result = f"Error: Tool '{t['name']}' does not exist."
            else:
                result = tools_dict[t['name']].invoke(t['args'])
            
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        
        return {'messages': results}
    
    return call_llm, take_action


def should_continue(state: AgentState) -> bool:
    """Check if the last message contains tool calls."""
    result = state['messages'][-1]
    return hasattr(result, 'tool_calls') and len(result.tool_calls) > 0


def build_study_agent(llm, vectorstore, catalog):
    """Build and compile the study agent graph."""
    # Create a mutable reference to hold current state
    current_state_ref = {'state': None}
    
    # State getter for the retriever tool
    def get_current_state():
        return current_state_ref['state'] or {}
    
    # Create tools
    retriever_tool = create_retriever_tool(vectorstore, get_current_state)
    tools = [retriever_tool]
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Create nodes
    call_llm, take_action = create_agent_nodes(llm_with_tools, tools, catalog, current_state_ref)
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("retriever_agent", take_action)
    
    graph.add_edge(START, "llm")
    graph.add_conditional_edges(
        "llm",
        should_continue,
        {
            True: "retriever_agent",
            False: END
        }
    )
    graph.add_edge("retriever_agent", "llm")
    
    return graph.compile()


# ============================================================================
# MAIN INTERFACE
# ============================================================================

class StudyRAGInterface:
    """Main interface for the Study RAG system."""
    
    def __init__(self):
        load_dotenv()
        self.llm, self.embeddings = initialize_models()
        self.ingestion_pipeline = IngestionPipeline(self.embeddings)
        self.vectorstore = None
        self.catalog = None
        self.study_agent = None
        self.state = {
            'messages': [],
            'active_semester': None,
            'active_subject': None,
            'active_books': []
        }
    
    def initialize_vectorstore(self):
        """Load the vectorstore (required before using study mode)."""
        if not VECTORSTORE_DIR.exists():
            print("⚠️  Vector store not found. Please run ingestion first.")
            return False
        
        try:
            self.vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=str(VECTORSTORE_DIR)
            )
            self.catalog = Catalog(self.vectorstore)
            self.study_agent = build_study_agent(self.llm, self.vectorstore, self.catalog)
            return True
        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            return False
    
    def run_ingestion_mode(self):
        """Run the ingestion pipeline."""
        print("\n" + "="*70)
        print("📚 INGESTION MODE")
        print("="*70)
        print("\nOptions:")
        print("1. Ingest new books only (skip already ingested)")
        print("2. Re-ingest all books (force)")
        print("0. Back to main menu")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            self.ingestion_pipeline.ingest_all(force_reingest=False)
        elif choice == "2":
            confirm = input("⚠️  This will re-process all books. Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                self.ingestion_pipeline.ingest_all(force_reingest=True)
        elif choice == "0":
            return
        else:
            print("Invalid option")
        
        input("\nPress Enter to continue...")
    
    def display_navigation_menu(self):
        """Display current scope and navigation options."""
        print("\n" + "="*70)
        print("📚 STUDY MODE - NAVIGATION")
        print("="*70)
        
        # Show current scope
        print(f"\n📍 Current Scope: {self.catalog.get_scope_description(self.state)}")
        
        print("\nNavigation Commands:")
        print("  semesters       - List all semesters")
        print("  subjects        - List subjects (in current semester)")
        print("  books           - List books (in current scope)")
        print("  use <semester>  - Set active semester")
        print("  open <subject>  - Set active subject")
        print("  select <book>   - Add book to active books")
        print("  clear           - Clear all scope filters")
        print("  back            - Return to main menu")
        print("\n  ask <question>  - Ask a question (uses current scope)")
        print("  chat            - Enter chat mode")
    
    def handle_navigation_command(self, command: str):
        """Handle navigation commands."""
        parts = command.strip().lower().split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None
        
        if cmd == "semesters":
            semesters = self.catalog.list_semesters()
            print(f"\n📅 Available semesters: {', '.join(semesters)}")
        
        elif cmd == "subjects":
            subjects = self.catalog.list_subjects(self.state.get('active_semester'))
            print(f"\n📚 Available subjects: {', '.join(subjects)}")
        
        elif cmd == "books":
            books = self.catalog.list_books(
                self.state.get('active_semester'),
                self.state.get('active_subject')
            )
            print("\n📖 Available books:")
            for book in books:
                print(f"   - {book['book_id']}: {book['book_title']}")
        
        elif cmd == "use" and arg:
            # Find the actual case-matched semester from vectorstore
            available = self.catalog.list_semesters()
            matched_semester = None
            for s in available:
                if s.lower() == arg.lower():
                    matched_semester = s
                    break
            
            if matched_semester:
                self.state['active_semester'] = matched_semester
                print(f"✅ Active semester: {matched_semester}")
            else:
                self.state['active_semester'] = arg
                if available:
                    print(f"⚠️  Note: '{arg}' not found. Available semesters: {', '.join(available)}")
                print(f"✅ Active semester set to: {arg}")
        
        elif cmd == "open" and arg:
            # Find the actual case-matched subject from vectorstore
            available = self.catalog.list_subjects(self.state.get('active_semester'))
            matched_subject = None
            for s in available:
                if s.lower() == arg.lower():
                    matched_subject = s
                    break
            
            if matched_subject:
                self.state['active_subject'] = matched_subject
                print(f"✅ Active subject: {matched_subject}")
            else:
                self.state['active_subject'] = arg
                if available:
                    print(f"⚠️  Note: '{arg}' not found. Available subjects: {', '.join(available)}")
                print(f"✅ Active subject set to: {arg}")
        
        elif cmd == "select" and arg:
            if arg not in self.state['active_books']:
                self.state['active_books'].append(arg)
            print(f"✅ Active books: {', '.join(self.state['active_books'])}")
        
        elif cmd == "clear":
            self.state['active_semester'] = None
            self.state['active_subject'] = None
            self.state['active_books'] = []
            print("✅ Scope cleared")
        
        elif cmd == "ask" and arg:
            self.ask_question(arg)
        
        elif cmd == "chat":
            self.run_chat_mode()
        
        elif cmd == "back":
            return False
        
        else:
            print("❌ Unknown command or missing argument")
        
        return True
    
    def ask_question(self, question: str):
        """Ask a single question to the agent."""
        print(f"\n💭 Question: {question}")
        print("🤔 Thinking...\n")
        
        messages = self.state['messages'] + [HumanMessage(content=question)]
        state_copy = {**self.state, 'messages': messages}
        
        result = self.study_agent.invoke(state_copy)
        answer = result['messages'][-1].content
        
        print("="*70)
        print("📝 ANSWER")
        print("="*70)
        print(answer)
        print("="*70)
    
    def run_chat_mode(self):
        """Enter interactive chat mode."""
        print("\n" + "="*70)
        print("💬 CHAT MODE")
        print("="*70)
        print(f"📍 Scope: {self.catalog.get_scope_description(self.state)}")
        print("Type 'exit' to return to navigation menu\n")
        
        while True:
            user_input = input("\n📖 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'back']:
                break
            
            if not user_input:
                continue
            
            self.state['messages'].append(HumanMessage(content=user_input))
            
            print("🤔 Assistant: ", end="", flush=True)
            result = self.study_agent.invoke(self.state)
            
            answer = result['messages'][-1].content
            print(answer)
            
            # Update state with the conversation
            self.state['messages'] = result['messages']
    
    def run_study_mode(self):
        """Run the study mode with navigation and chat."""
        if not self.initialize_vectorstore():
            input("\nPress Enter to continue...")
            return
        
        print("✅ Study mode initialized!")
        
        while True:
            self.display_navigation_menu()
            command = input("\n> ").strip()
            
            if not command:
                continue
            
            should_continue = self.handle_navigation_command(command)
            if not should_continue:
                break
    
    def run(self):
        """Main entry point."""
        print("\n" + "="*70)
        print("🎓 STUDY RAG SYSTEM")
        print("="*70)
        
        while True:
            print("\n" + "="*70)
            print("MAIN MENU")
            print("="*70)
            print("\n1. Ingestion Mode (Add/Update textbooks)")
            print("2. Study Mode (Navigate and ask questions)")
            print("0. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self.run_ingestion_mode()
            elif choice == "2":
                self.run_study_mode()
            elif choice == "0":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")


def main():
    """Main function."""
    interface = StudyRAGInterface()
    interface.run()


if __name__ == "__main__":
    main()
