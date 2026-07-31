import streamlit as st
import os
import pickle
import numpy as np
from pathlib import Path
from groq import Groq
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

# Load env for local testing
load_dotenv()

st.set_page_config(page_title="SecondSelf Oracle", page_icon="🧠", layout="wide")

# Initialize directories
script_dir = Path(__file__).resolve().parent
wiki_dir = script_dir / "wiki"
cache_path = script_dir / "embeddings.pkl"

# --- Backend Setup (Cached) ---
@st.cache_resource
def load_ai_models():
    # Only loads once on server startup
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

@st.cache_data
def load_knowledge_base():
    if not cache_path.exists():
        return None
    with open(cache_path, "rb") as f:
        return pickle.load(f)

model = load_ai_models()
cache_data = load_knowledge_base()

# Client (assumes GROQ_API_KEY is in secrets or .env)
client = Groq()

def read_wiki_file(filename: str) -> str:
    path = wiki_dir / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def search_knowledge_base(query: str, top_k: int = 5):
    if not cache_data:
        return "Error: Knowledge base cache not found.", []
    
    query_embedding = model.encode(query, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, cache_data["embeddings"])[0].cpu().numpy()
    
    top_indices = np.argsort(cosine_scores)[::-1][:top_k]
    filenames = cache_data["filenames"]
    
    context = ""
    citations = []
    
    for idx in top_indices:
        filename = filenames[idx]
        score = cosine_scores[idx]
        content = read_wiki_file(filename)
        context += f"\n--- NOTE: {filename} ---\n{content}\n"
        citations.append(f"{filename}")
        
    return context, citations

def generate_response(query: str, context: str):
    system_prompt = (
        "You are 'The Oracle', an AI assistant for the user's personal knowledge base.\n"
        "You will be provided with a set of notes retrieved from their wiki.\n"
        "Your task is to answer the user's query STRICTLY based on the provided notes.\n"
        "CRITICAL INSTRUCTION: If the answer cannot be found in the provided notes, you MUST say "
        "'I don't know based on the provided notes.' Do NOT use outside knowledge to fill in gaps."
    )
    user_prompt = f"USER QUERY: {query}\n\nRELEVANT NOTES:\n{context}"
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to Groq API: {str(e)}"

# --- UI Setup ---
st.title("🧠 SecondSelf: The Oracle")

# Sidebar: The Cartographer Graph
with st.sidebar:
    st.header("The Cartographer")
    st.write("Visual Knowledge Graph")
    
    # Read the graph data and HTML and inject to bypass iframe static file issues
    html_path = script_dir / "index.html"
    js_path = script_dir / "graph_data.js"
    
    if html_path.exists() and js_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
            
        # Inject JS directly into HTML to avoid local iframe CORS/path issues
        injected_html = html_content.replace(
            '<script src="graph_data.js"></script>',
            f"<script>{js_content}</script>"
        )
        
        st.components.v1.html(injected_html, height=600, scrolling=True)
    else:
        st.warning("Run build_graph.py first to generate the visualization.")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            with st.expander("Sources"):
                for c in message["citations"]:
                    st.markdown(f"- `{c}`")

# React to user input
if prompt := st.chat_input("Ask your knowledge base..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Searching your brain..."):
            context, citations = search_knowledge_base(prompt)
            answer = generate_response(prompt, context)
            
            st.markdown(answer)
            if citations:
                with st.expander("Sources"):
                    for c in citations:
                        st.markdown(f"- `{c}`")
                        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations})
