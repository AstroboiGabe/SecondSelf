# SecondSelf: Frontend GUI Redesign & Pipeline Integration

This plan maps out a massive upgrade to `app.py`. The goal is to move the Cartographer graph to the main view and transform the sidebar into a fully functional "Command Center" where you can capture ideas and trigger the AI processing pipeline directly from the UI.

## System Memory Information (Your Question)
You asked about the total memory storage available through the Streamlit launch. Because you are currently running Streamlit locally on your machine, it has access to **your computer's entire RAM and Hard Drive**. 
- *If/when we deploy this to Streamlit Community Cloud*, the free tier provides exactly **1 GB of RAM** and limited disk space.
- To help you monitor this, I will add a live "System Diagnostics" metric directly into your new sidebar so you can see exactly how much memory/storage the app is using in real-time!

## Proposed Changes

---
### [MODIFY] app.py
1. **Main View Restructuring**:
   - Move the Cartographer visual map out of the sidebar and place it in the center of the screen, beneath the chat interface.
2. **Sidebar - Capture Engine**:
   - Add a `st.text_area` with the heading **"Capture Quick Note"**.
   - Add a **"Capture note"** button. When clicked, it will securely save your text to the `raw/` folder using our existing `capture.py` logic.
3. **Sidebar - Pipeline Engine**:
   - Add a horizontal line (`st.divider()`) and the heading **"Pipeline"**.
   - Add the **"force re-process"** checkbox. *(As agreed, if this is checked, it will forcefully delete `embeddings.pkl` and rebuild the math links/graph from scratch).*
   - Add the **"Process new captures"** button.
   - When clicked, this button will sequentially trigger `classify.py`, `link.py`, and `build_graph.py`.
   - Once all three finish successfully, it will trigger a `st.success("Wiki, links and graphs updated")` green banner.
4. **Sidebar - Diagnostics**:
   - Add a small widget at the very bottom using `shutil` and `psutil` to display available memory/disk storage.

### [MODIFY] requirements.txt
- Add `psutil` to the dependencies so we can fetch live RAM usage metrics for the UI.

## Verification Plan

### Automated Tests
- The Streamlit server should restart without errors and render the new layout.

### Manual Verification
- Type a test note into the sidebar and hit "Capture note".
- Hit "Process new captures" and verify the green success bar appears.
- Verify the main view updates the graph to include the newly captured note.
