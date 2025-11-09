import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os

# Set page
st.set_page_config(page_title="RAG Agent", page_icon="🤖", layout="wide")

# Load credentials ONLY from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = os.getenv("TABLE_NAME", "documents")

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ✅ Sidebar - no sensitive fields shown
with st.sidebar:
    st.title("⚙️ Settings")
    table_name = st.text_input("Table Name", value=TABLE_NAME)
    st.slider("Memory length", 3, 12, 6, key="memory_length")

    if st.button("❌ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()


@st.cache_resource
def initialize_clients():
    if not GEMINI_API_KEY:
        st.error("❌ Missing GEMINI_API_KEY environment variable")
        return None, None

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Missing Supabase environment variables")
        return None, None

    genai.configure(api_key=GEMINI_API_KEY.strip())
    model = genai.GenerativeModel("gemini-2.5-flash")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    st.success("✅ Backend services connected")
    return model, supabase


# ✅ Main App
st.title("📚 Memory RAG Agent (Secured Keys ✅)")

model, supabase_client = initialize_clients()

if not model or not supabase_client:
    st.warning("""
    ⚠️ Please set these in Render environment variables:

    - GEMINI_API_KEY
    - SUPABASE_URL
    - SUPABASE_KEY
    - TABLE_NAME (optional)
    """)
    st.stop()

# ✅ Show chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])




# Client initialization
@st.cache_resource
def initialize_clients(_gemini_key, _supabase_url, _supabase_key):
    try:
        if not _gemini_key:
            raise ValueError("Gemini API key missing")

        genai.configure(api_key=_gemini_key.strip())
        model = genai.GenerativeModel("gemini-2.5-flash")

        if not _supabase_url or not _supabase_key:
            raise ValueError("Supabase credentials missing")

        supabase = create_client(_supabase_url, _supabase_key)
        return model, supabase

    except Exception as e:
        st.error(f"❌ Client initialization failed: {str(e)}")
        return None, None


def fetch_documents(supabase: Client, table: str) -> List[Dict]:
    try:
        response = supabase.table(table).select("content").execute()
        return response.data or []
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []


def retrieve_context(query: str, docs: List[Dict], top_k: int = 5) -> str:
    words = set(query.lower().split())
    ranked = []

    for d in docs:
        c = d.get("content", "").lower()
        score = sum(1 for w in words if w in c)
        if score > 0:
            ranked.append((score, d["content"]))

    ranked.sort(reverse=True, key=lambda x: x[0])
    top = [t for _, t in ranked[:top_k]]
    return "\n\n".join(top) if top else "No relevant documents found."


def generate_chat_response(model, query: str, context: str, history: List[Dict]) -> str:
    last_messages = history[-st.session_state.memory_length:]
    conversation_block = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in last_messages])

    prompt = f"""
You are a helpful AI assistant with memory and retrieval. Always use:
1️⃣ The conversation history  
2️⃣ Retrieved database context  

Conversation history:
{conversation_block}

Retrieved Context:
{context}

USER: {query}
ASSISTANT:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Failed to generate response: {str(e)}"


# Main UI
st.title("📚 Memory RAG Agent with Gemini + Supabase")

if not all([gemini_api_key, supabase_url, supabase_key]):
    st.warning("Enter API keys to begin…")
else:
    model, supabase_client = initialize_clients(gemini_api_key, supabase_url, supabase_key)

    if model and supabase_client:

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if prompt := st.chat_input("Ask me anything…"):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Thinking with memory…"):
                    docs = fetch_documents(supabase_client, table_name)
                    context = retrieve_context(prompt, docs)

                    response = generate_chat_response(model, prompt, context, st.session_state.messages)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                with st.expander("🔍 View Retrieved Context"):
                    st.text(context)

st.divider()
st.caption("⚡ Powered by Gemini + Supabase + Streamlit")
