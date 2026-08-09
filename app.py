import streamlit as st
import os
import pickle
import numpy as np
import shutil
import psutil
from pathlib import Path
from groq import Groq
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

# Import local backend scripts
import capture
import classify
import link
import build_graph

# Load env for local testing
load_dotenv()

st.set_page_config(page_title="SecondSelf Oracle", page_icon="🧠", layout="wide")

# --- Custom Styling: Search Bar Height & Green Focus Border ---
st.markdown("""
<style>
/* 1. Force 54px height across all container wrappers for stTextInput */
div[data-testid="stTextInput"],
div[data-testid="stTextInput"] > div,
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
    min-height: 54px !important;
    height: 54px !important;
}

/* 2. Default state: subtle glass border, NO red border */
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
    background-color: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    transition: all 0.25s ease-in-out !important;
}

/* 3. OVERRIDE RED FOCUS RING: Force Green border on Focus/Click/Active across all BaseWeb selectors */
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextInput"] input:focus-visible,
div[data-testid="stTextInput"] input:active {
    border: 2px solid #10b981 !important; /* Force Green */
    border-color: #10b981 !important;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.5) !important;
    outline: none !important;
}

/* 4. Formatting input text inside */
div[data-testid="stTextInput"] input {
    height: 100% !important;
    color: #f8fafc !important;
    font-size: 1.1rem !important;
    padding: 0 16px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize directories
script_dir = Path(__file__).resolve().parent
wiki_dir = script_dir / "wiki"
raw_dir = script_dir / "raw"
cache_path = script_dir / "embeddings.pkl"

# --- Backend Setup (Cached) ---
@st.cache_resource
def load_ai_models():
    # Only loads once on server startup
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

@st.cache_data
def load_knowledge_base(force_reload=0):
    if not cache_path.exists():
        # Automatically generate embeddings cache if missing
        link.process_links()
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    return None

model = load_ai_models()

# Client (assumes GROQ_API_KEY is in secrets or .env)
client = Groq()

def read_wiki_file(filename: str) -> str:
    path = wiki_dir / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def search_knowledge_base(query: str, top_k: int = 5):
    kb = load_knowledge_base(st.session_state.get("force_reload", 0))
    if not kb or "embeddings" not in kb or len(kb.get("filenames", [])) == 0:
        return "Error: Knowledge base is empty or cache not found.", []
    
    query_embedding = model.encode(query, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, kb["embeddings"])[0].cpu().numpy()
    
    top_indices = np.argsort(cosine_scores)[::-1][:top_k]
    filenames = kb["filenames"]
    
    context = ""
    citations = []
    
    for idx in top_indices:
        if idx < len(filenames):
            filename = filenames[idx]
            score = cosine_scores[idx]
            content = read_wiki_file(filename)
            context += f"\n--- NOTE: {filename} ---\n{content}\n"
            citations.append({
                "filename": filename,
                "score": float(score),
                "content": content
            })
        
    return context, citations

def delete_node_permanently(filename: str):
    try:
        # 1. Delete Markdown file from wiki/
        target_file = wiki_dir / filename
        if target_file.exists():
            target_file.unlink()
            
        # 2. Invalidate and rebuild embeddings cache immediately
        if cache_path.exists():
            cache_path.unlink()
        link.process_links()
            
        # 3. Rebuild the graph_data.js to reflect node deletion immediately
        build_graph.build_graph()
        
        # 4. Immediately purge deleted file from active citations in session state
        if "messages" in st.session_state:
            for item in st.session_state.messages:
                if isinstance(item, dict) and "citations" in item and item["citations"]:
                    item["citations"] = [
                        c for c in item["citations"]
                        if (isinstance(c, dict) and c.get("filename") != filename)
                        or (isinstance(c, str) and c != filename)
                    ]
        
        # 5. Clear Streamlit cache & increment force_reload to trigger graph iframe remount
        load_knowledge_base.clear()
        st.session_state.force_reload = st.session_state.get("force_reload", 0) + 1
        
        st.toast(f"🗑️ Node {filename} permanently deleted!", icon="🗑️")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to delete node {filename}: {e}")

def render_sources_ui(citations, prefix_key=""):
    if not citations:
        return
        
    with st.expander(f"📚 Referenced Sources ({len(citations)} Files)", expanded=False):
        for idx, item in enumerate(citations, 1):
            if isinstance(item, dict):
                filename = item.get("filename", "Unknown File")
                score = item.get("score", 0.0)
                content = item.get("content", "")
            else:
                filename = str(item)
                score = 0.0
                content = read_wiki_file(filename)
                
            # Render individual source file details
            with st.expander(f"📄 Source #{idx}: `{filename}`", expanded=False):
                if content:
                    st.markdown(content)
                else:
                    st.caption("No content available for this note.")
                
                st.divider()
                delete_key = f"delete_node_{prefix_key}_{filename}_{idx}"
                if st.button(f"🗑️ Delete Node `{filename}` Permanently", key=delete_key, help="Permanently remove this note from wiki, cache, and knowledge graph."):
                    delete_node_permanently(filename)

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

# --- SIDEBAR: Command Center ---
with st.sidebar:
    st.header("Command Center")
    
    # 1. Capture Engine
    st.subheader("Capture Quick Note")
    quick_note = st.text_area("Write your idea here...", height=100, label_visibility="collapsed", placeholder="Type a new thought...")
    if st.button("Capture note"):
        if quick_note.strip():
            try:
                record = capture.NoteHandler.process(quick_note)
                capture.save_record_to_raw(record)
                st.success("Note captured successfully!")
            except Exception as e:
                st.error(f"Failed to capture note: {e}")
        else:
            st.warning("Note is empty.")
            
    st.divider()
    
    # 2. Pipeline Engine
    st.subheader("Pipeline")
    force_reprocess = st.checkbox("force re-process")
    if st.button("Process new captures"):
        with st.spinner("Running AI Pipeline..."):
            try:
                if force_reprocess:
                    if cache_path.exists():
                        cache_path.unlink()
                    js_path = script_dir / "graph_data.js"
                    if js_path.exists():
                        js_path.unlink()
                
                # Execute Pipeline
                classify.process_raw_captures()
                link.process_links()
                build_graph.build_graph()
                
                # Force reload of cache in Streamlit
                st.session_state.force_reload = st.session_state.get("force_reload", 0) + 1
                load_knowledge_base.clear()
                cache_data = load_knowledge_base(st.session_state.force_reload)
                
                st.write("pipeline completed")
                st.success("Wiki, links and graphs updated")
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                
    st.divider()
    
    # 3. System Diagnostics
    st.subheader("System Diagnostics")
    total, used, free = shutil.disk_usage("/")
    ram = psutil.virtual_memory()
    
    # Formatting to GB
    total_gb = total // (2**30)
    used_gb = used // (2**30)
    free_gb = free // (2**30)
    
    st.metric("Total Storage Available", f"{total_gb} GB")
    st.metric("System RAM Utilization", f"{ram.percent}%")
    st.caption(f"Storage Used: {used_gb} GB / Free: {free_gb} GB")


# --- MAIN VIEW: Chat & Graph ---
st.markdown("### Search & Chat")

# Chat Interface History Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Callback for clean Enter-key submission without any search button
def submit_query():
    query = st.session_state.get("search_input_box", "").strip()
    if query:
        st.session_state["pending_prompt"] = query
        st.session_state["search_input_box"] = ""

# Single, full-width search bar right under "Search & Chat" heading
st.text_input(
    "Search",
    placeholder="Ask your knowledge base...",
    label_visibility="collapsed",
    key="search_input_box",
    on_change=submit_query
)

prompt = st.session_state.pop("pending_prompt", None)

# Process new search query if submitted (inserts at top)
if prompt:
    with st.spinner("Searching your brain..."):
        context, citations = search_knowledge_base(prompt)
        answer = generate_response(prompt, context)
        
        # Insert newest Q&A exchange at the top (index 0)
        new_exchange = {
            "user": prompt,
            "assistant": answer,
            "citations": citations
        }
        st.session_state.messages.insert(0, new_exchange)

# Display chat history (Newest search displayed on top)
for idx, item in enumerate(st.session_state.messages):
    if isinstance(item, dict) and "user" in item:
        with st.chat_message("user"):
            st.markdown(item["user"])
        with st.chat_message("assistant"):
            st.markdown(item["assistant"])
            if item.get("citations"):
                render_sources_ui(item["citations"], prefix_key=f"top_{idx}")
    elif isinstance(item, dict) and "role" in item:
        with st.chat_message(item.get("role", "assistant")):
            st.markdown(item.get("content", ""))
            if item.get("citations"):
                render_sources_ui(item.get("citations"), prefix_key=f"legacy_{idx}")

st.divider()

# Cartographer Graph (Main View)
st.markdown("### The Cartographer")

# PARA Color Legend
st.markdown("""
<div style="display: flex; gap: 20px; align-items: center; margin-bottom: 15px; flex-wrap: wrap; background-color: rgba(30, 41, 59, 0.5); padding: 12px 18px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.1);">
    <span style="font-weight: 600; color: #94a3b8; font-size: 0.9rem;">Graph Legend:</span>
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="height: 12px; width: 12px; background-color: #ef4444; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.85rem; color: #f8fafc; font-weight: 500;">Projects (Red)</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="height: 12px; width: 12px; background-color: #3b82f6; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.85rem; color: #f8fafc; font-weight: 500;">Areas (Blue)</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="height: 12px; width: 12px; background-color: #10b981; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.85rem; color: #f8fafc; font-weight: 500;">Resources (Green)</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="height: 12px; width: 12px; background-color: #64748b; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.85rem; color: #f8fafc; font-weight: 500;">Archives (Gray)</span>
    </div>
</div>
""", unsafe_allow_html=True)

html_path = script_dir / "index.html"
js_path = script_dir / "graph_data.js"

if html_path.exists() and js_path.exists():
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()
        
    # Inject JS directly into HTML to avoid local iframe CORS/path issues & force re-render on reload
    injected_html = html_content.replace(
        '<script src="graph_data.js"></script>',
        f"<script>{js_content}</script>"
    ) + f"\n<!-- reload_{st.session_state.get('force_reload', 0)} -->"
    
    st.components.v1.html(injected_html, height=600, scrolling=True)
else:
    st.info("Run the Pipeline to generate the visual knowledge graph.")
