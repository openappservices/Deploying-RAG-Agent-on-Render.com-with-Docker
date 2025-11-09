import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from typing import List, Dict

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
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Initialize Supabase
        supabase: Client = create_client(_supabase_url, _supabase_key)
        
        return model, supabase
    except Exception as e:
        st.error(f"Error initializing clients: {str(e)}")
        return None, None

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

def simple_keyword_match(query: str, documents: List[Dict], top_k: int = 5) -> str:
    """Simple keyword matching without embeddings (memory efficient)"""
    if not documents:
        return "No documents found in the database."
    
    query_words = set(query.lower().split())
    scored_docs = []
    
    for doc in documents:
        # Try common field names
        text = doc.get('content') or doc.get('text') or doc.get('description') or str(doc)
        text_lower = text.lower()
        
        # Count matching words
        score = sum(1 for word in query_words if word in text_lower)
        
        if score > 0:
            scored_docs.append((score, text))
    
    # Sort by score and get top k
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    top_docs = [text for _, text in scored_docs[:top_k]]
    
    return "\n\n".join(top_docs) if top_docs else "No relevant documents found."

def generate_response(model, query: str, context: str) -> str:
    """Generate response using Gemini with retrieved context"""
    prompt = f"""You are a helpful AI assistant. Use the following context from the database to answer the user's question. 
If the context doesn't contain relevant information, say so and provide a general answer if possible.

Context from database:
{context}

User Question: {query}

Answer:"""
    
    try:
        response = model.generate_content([prompt])
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
                        
                        # Retrieve relevant context using simple keyword matching
                        context = simple_keyword_match(prompt, documents)
                        
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
- This lightweight version uses keyword matching instead of embeddings (lower memory usage)
- The agent will search across all rows in the specified table
""")