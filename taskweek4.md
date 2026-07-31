# Week 4 Execution Checklist: The Oracle

## Phase 1: The Indexer Update
- `[x]` Modify `link.py` to generate and export `embeddings.pkl` to cache vector math.
- `[x]` Run the modified script to successfully generate the cache file for the 15 wiki notes.

## Phase 2: The Oracle CLI (`ask.py`)
- `[x]` Create `ask.py` leveraging `sentence-transformers` for local encoding.
- `[x]` Implement Cosine Similarity logic to extract the Top 5 most relevant notes from the cache.
- `[x]` Construct a rigid system prompt forcing Groq to answer strictly from the context.
- `[x]` Format terminal output to cleanly print the generated answer and the citations used.

## Phase 3: Final Verification
- `[x]` Verify the Oracle successfully retrieves factual data from the knowledge base.
- `[x]` Verify the Oracle correctly refuses to answer out-of-bounds questions.
