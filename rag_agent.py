import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

# Configuration
st.set_page_config(page_title="RAG Agent", page_icon="🤖", layout="wide")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar for API keys and configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Try to get from environment variables first, then allow manual input
    gemini_api_key = st.text_input(
        "Gemini API Key", 
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password", 
        key="gemini_key"
    )
    supabase_url = st.text_input(
        "Supabase URL", 
        value=os.getenv("SUPABASE_URL", ""),
        key="supabase_url"
    )
    supabase_key = st.text_input(
        "Supabase Key", 
        value=os.getenv("SUPABASE_KEY", ""),
        type="password", 
        key="supabase_key"
    )
    table_name = st.text_input(
        "Table Name", 
        value=os.getenv("TABLE_NAME", "documents"),
        key="table_name"
    )
    
    st.divider()
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Initialize clients
@st.cache_resource
def initialize_clients(_gemini_key, _supabase_url, _supabase_key):
    """Initialize Gemini and Supabase clients"""
    try:
        # Configure Gemini
        genai.configure(api_key=_gemini_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Initialize Supabase
        supabase: Client = create_client(_supabase_url, _supabase_key)
        
        return model, supabase
    except Exception as e:
        st.error(f"Error initializing clients: {str(e)}")
        return None, None

@st.cache_resource
def load_embedding_model():
    """Load sentence transformer model for embeddings"""
    return SentenceTransformer('all-MiniLM-L6-v2')

def fetch_data_from_supabase(supabase: Client, table: str, query: str = None) -> List[Dict]:
    """Fetch data from Supabase table"""
    try:
        if query:
            # If you have a search query, you can filter
            response = supabase.table(table).select("*").execute()
        else:
            response = supabase.table(table).select("*").execute()
        
        return response.data
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return []

def create_embeddings(texts: List[str], model: SentenceTransformer) -> np.ndarray:
    """Create embeddings for texts"""
    return model.encode(texts)

def retrieve_relevant_context(query: str, documents: List[Dict], embedding_model: SentenceTransformer, top_k: int = 3) -> str:
    """Retrieve most relevant documents based on query"""
    if not documents:
        return "No documents found in the database."
    
    # Assuming documents have a 'content' or 'text' field
    # Adjust field name based on your schema
    doc_texts = []
    for doc in documents:
        # Try common field names
        text = doc.get('content') or doc.get('text') or doc.get('description') or str(doc)
        doc_texts.append(text)
    
    # Create embeddings
    query_embedding = embedding_model.encode([query])[0]
    doc_embeddings = embedding_model.encode(doc_texts)
    
    # Calculate cosine similarity
    similarities = np.dot(doc_embeddings, query_embedding) / (
        np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top k documents
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    relevant_docs = [doc_texts[i] for i in top_indices if similarities[i] > 0.1]  # Threshold
    
    return "\n\n".join(relevant_docs) if relevant_docs else "No relevant context found."

def generate_response(model, query: str, context: str) -> str:
    """Generate response using Gemini with retrieved context"""
    prompt = f"""You are a helpful AI assistant. Use the following context from the database to answer the user's question. 
If the context doesn't contain relevant information, say so and provide a general answer if possible.

Context from database:
{context}

User Question: {query}

Answer:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Main UI
st.title("🤖 RAG Agent with Gemini & Supabase")
st.markdown("Ask questions and get answers based on your Supabase database!")

# Check if all credentials are provided
if not all([gemini_api_key, supabase_url, supabase_key]):
    st.warning("⚠️ Please provide all credentials in the sidebar to start.")
    st.info("""
    **Setup Instructions:**
    1. Enter your Google Gemini API key
    2. Enter your Supabase URL and API key
    3. Specify the table name containing your documents
    4. Make sure your table has a text/content column with the data to search
    """)
else:
    # Initialize clients
    gemini_model, supabase_client = initialize_clients(gemini_api_key, supabase_url, supabase_key)
    
    if gemini_model and supabase_client:
        embedding_model = load_embedding_model()
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about your data..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Fetch data from Supabase
                    documents = fetch_data_from_supabase(supabase_client, table_name)
                    
                    if documents:
                        st.info(f"📊 Retrieved {len(documents)} documents from database")
                        
                        # Retrieve relevant context
                        context = retrieve_relevant_context(prompt, documents, embedding_model)
                        
                        # Generate response
                        response = generate_response(gemini_model, prompt, context)
                        
                        st.markdown(response)
                        
                        # Show retrieved context in expander
                        with st.expander("View Retrieved Context"):
                            st.text(context)
                    else:
                        response = "No documents found in the database. Please check your table name and ensure it contains data."
                        st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.markdown("""
### 📝 Database Schema Notes:
- Ensure your Supabase table has a column with text content (e.g., 'content', 'text', or 'description')
- The agent will search across all rows in the specified table
- Adjust the `top_k` parameter in the code to retrieve more/fewer documents
""")
