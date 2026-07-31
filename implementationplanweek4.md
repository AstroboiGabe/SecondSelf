# SecondSelf Week 4: The Oracle (Chat with your Brain)

This plan covers Week 4 of SecondSelf. The objective is to build a Retrieval-Augmented Generation (RAG) engine that allows you to ask questions to your local knowledge base in natural language. The system will semantically search your wiki, extract relevant notes, and use an LLM to synthesize an answer based *purely* on your data.

## Proposed Changes

---
### Phase 1: The Indexer Update
#### [MODIFY] link.py
- Update the script to export the computed document embeddings into an `embeddings.pkl` cache file in the `Week1/` folder.
- This ensures `ask.py` can instantly load the mathematical vectors without re-reading all the markdown files from scratch.

### Phase 2: The Oracle CLI (`ask.py`)
#### [NEW] ask.py
- Takes a natural language query via the terminal (e.g., `python ask.py "What is the PARA method?"`).
- Converts the user query into a vector embedding using `sentence-transformers`.
- Loads the cached `embeddings.pkl` and computes the cosine similarity against all notes.
- Extracts the **Top 5** most relevant `.md` files from the `wiki/` directory.
- Constructs a prompt containing the contents of those 5 files, **strictly commanding the AI to say "I don't know" if the answer is not found in the notes.**
- Calls the Groq API (`llama-3.3-70b-versatile`) to generate a synthesized answer based *only* on the provided context.
- Outputs the answer to the terminal, and prints the filenames it used as citations at the bottom.

## Verification Plan

### Automated Tests
- Run `python ask.py "What did I capture about vector embeddings?"` and verify it successfully connects to Groq and returns a response based on the dummy notes we made earlier.

### Manual Verification
- Ask a question that is definitively NOT in the knowledge base (e.g., "What is the recipe for pancakes?") to verify that the strictness setting works properly and the AI refuses to answer.
