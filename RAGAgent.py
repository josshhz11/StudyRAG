from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.tools import tool

# Global constants
PERSIST_DIRECTORY = r"C:\Users\joshua\OneDrive - Nanyang Technological University\Documents\Working Folder\Self-Study\Tech\Tutorials\LangGraph\ai_agents"
COLLECTION_NAME = "scb_internship_offer"
PDF_PATH = "Offer_of_Employment_Letter_with_Authorisation.pdf"

SYSTEM_PROMPT = """
You are an intelligent AI assistant who answers questions about the PDF document loaded into your knowledge base.
Use the retriever tool available to answer questions about the data and information in the PDF document. You can make multiple calls if needed.
If you need to look up some information before asking a follow up question, you are allowed to do that!
Please always cite the specific parts of the documents you use in your answers.
"""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def initialize_models():
    """Initialize LLM and embeddings models."""
    # Minimize hallucinations - temperature = 0 makes the moddel more deterministic and less stochastic
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0
    )

    # Our Embedding Model - has to also be compatible with our LLM
    # This is what converts our text to vector embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    return llm, embeddings

def load_and_process_pdf(pdf_path: str):
    """Load PDF and split into chunks"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Load the PDF and check below if PDF can be loaded 
    pdf_loader = PyPDFLoader(pdf_path)

    try:
        pages = pdf_loader.load()
        print(f"PDF has been loaded and has {len(pages)} pages")
    except Exception as e:
        raise Exception(f"Error loading PDF: {str(e)}")

    # Chunking Process
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    pages_split = text_splitter.split_documents(pages)
    print(f"Split into {len(pages_split)} chunks")

    return pages_split

def setup_vectorstore(pages_split, embeddings):
    """Create or load ChromaDB vector store"""
    if not os.path.exists(PERSIST_DIRECTORY):
        os.makedirs(PERSIST_DIRECTORY)

    try:
        # Here we create the chroma database using our embeddings model
        vectorstore = Chroma.from_documents(
            documents=pages_split,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY,
            collection_name=COLLECTION_NAME
        )
        print("Created ChromaDB vector store!")
    except Exception as e:
        raise Exception(f"Error setting up ChromaDB: {str(e)}")
    
    return vectorstore

def create_retriever_tool(vectorstore):
    """Create the retriever tool from the vectorstore."""
    # Now create the retriever
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5} # number of chunks to return
    )

    @tool
    def retriever_tool(query: str) -> str:
        """
        This tool searches and returns the information from the Stock Market Performance 2024 document.
        """

        docs = retriever.invoke(query)

        if not docs:
            return "I found no relevant information in the Stock Market Performance 2024 document."
        
        results = []
        for i, doc in enumerate(docs):
            results.append(f"Document {i+1}: \n{doc.page_content}")
        
        return "\n\n".join(results)
    
    return retriever_tool

def should_continue(state: AgentState) -> AgentState:
    """Check if the last message contains tool calls."""
    result = state['messages'][-1]
    return hasattr(result, 'tool_calls') and len(result.tool_calls) > 0

def create_agent_nodes(llm, tools):
    """Create the agent node functions"""
    tools_dict = {our_tool.name: our_tool for our_tool in tools} # Creating a dictionary of our tools for efficient lookup in take_action()

    # LLM Agent
    def call_llm(state: AgentState) -> AgentState:
        """Function to call the LLM with the current state."""
        messages = list(state['messages'])
        messages = [SystemMessage(SYSTEM_PROMPT)] + messages
        message = llm.invoke(messages)

        return {'messages': [message]}

    # Retriever Agent (should_continue function between call_llm and this to ensure the last message was a tool message)
    def take_action(state: AgentState) -> AgentState:
        """Execute tool calls from the LLM's response."""

        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling Tool: {t['name']} with query: {t['args'].get('query', 'No query provided')}")

            if t['name'] not in tools_dict:
                print(f"\nTool: {t['name']} does not exist.")
                result = "Incorrect tool name. Please retry and select the tool from the list of available tools."
            else:
                result = tools_dict[t['name']].invoke(t['args'].get('query', ''))
                print(f"Result length: {len(str(result))}")
            
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

        print("Tools execution complete. Back to the model!")
        return {'messages': results}

    return call_llm, take_action
    
def build_graph(llm, tools):
    """Build and compile the agent graph."""
    call_llm, take_action = create_agent_nodes(llm, tools)

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

def run_agent(rag_agent):
    """Run the interactive agent loop."""
    print("\n=== RAG AGENT===")
    
    while True:
        user_input = input("\nWhat is your question: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
            
        messages = [HumanMessage(content=user_input)]
        result = rag_agent.invoke({"messages": messages})
        
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)

def main():
    """Main function to orchestrate the RAG agent setup"""
    # Load environment variables
    load_dotenv()

    print("Initializing RAG Agent...")

    # Initialize models
    llm, embeddings = initialize_models()

    # Load and process PDF
    pages_split = load_and_process_pdf(PDF_PATH)

    # Set up Vector Store
    vectorstore = setup_vectorstore(pages_split, embeddings)

    # Create retriever tool
    retriever_tool = create_retriever_tool(vectorstore)
    tools = [retriever_tool]

    # Bind tools to LLM
    llm = llm.bind_tools(tools)

    # Build the agent graph
    rag_agent = build_graph(llm, tools)

    print("RAG Agent initialized successfully!")

    # Run the agent
    run_agent(rag_agent)

if __name__ == "__main__":
    main()