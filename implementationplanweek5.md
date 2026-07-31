# SecondSelf Week 5: The Interface & Deployment

This plan covers Week 5 of SecondSelf. The goal is to wrap our Python AI logic into a graphical user interface (GUI) and deploy it to the web so you can access your knowledge base from anywhere. 

We have finalized the architectural decision to use **Streamlit** (abandoning Stitch) for maximum compatibility with our heavy AI/Python backend.

## Proposed Changes

---
### Phase 1: The Streamlit App (`app.py`)
#### [NEW] app.py
- Create a new Streamlit application file.
- **Sidebar**: Embed the interactive `index.html` (The Cartographer Graph) into a collapsible sidebar so you can physically see your brain while you chat.
- **Main View**: Create a sleek ChatGPT-style chat interface using Streamlit's native `st.chat_message()` and `st.chat_input()` components.
- **Backend Integration**: Import the logic from `ask.py` directly into the Streamlit app so it can query the `embeddings.pkl` cache and communicate with the Groq API seamlessly.
- **Styling**: Apply dark mode and custom CSS to match the premium aesthetics defined in Week 3.

#### [MODIFY] requirements.txt
- Add `streamlit` to the dependencies list.

### Phase 2: Local Testing
- Run `streamlit run app.py` locally to ensure the graph loads and the chat engine works perfectly in your browser before pushing to the public internet.

### Phase 3: Cloud Deployment (Streamlit Community Cloud)
Here is the detailed, step-by-step deployment method:

1. **Git Initialization & Upload (MANUAL)**: 
   - **You will manually push this project to GitHub.** 
   - When you are ready, you can create a repository on your own GitHub account and push the `Week1/` folder to it. I will not execute any Git commands for you.
2. **Security Check (CRITICAL)**: 
   - Ensure `.env` (which contains your Groq API key) is listed in your `.gitignore` file so your key is **not** leaked publicly on GitHub.
   - *Note: We WILL push your `wiki/` folder, `graph_data.js`, and `embeddings.pkl` to GitHub so the cloud server has access to your actual data.*
3. **Streamlit Cloud Setup**:
   - Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
   - Click the **"New app"** button.
   - Select your new GitHub repository, set the branch to `main`, and set the Main file path to `app.py`.
4. **Environment Variables**:
   - **Before you click Deploy**, click on **"Advanced Settings"**.
   - Under the "Secrets" text box, paste your Groq API key exactly like this:
     ```toml
     GROQ_API_KEY="your_api_key_here"
     ```
   - Click Save.
5. **Deploy**: 
   - Click **"Deploy!"**. 
   - Streamlit will automatically read your `requirements.txt`, install all the heavy machine learning libraries (PyTorch, sentence-transformers), and host your AI web app on a public URL completely for free.

## Verification Plan

### Automated Tests
- The local Streamlit server should start without crashing and successfully load the HuggingFace embedding model into memory on startup.

### Manual Verification
- Type a query into the web interface and verify the AI responds accurately using the knowledge base context.
- Verify the side panel successfully renders the interactive physics graph from Week 3.
