# Week 2 Execution Checklist: The Librarian

## Phase 1: Environment & Dependencies
- `[x]` Add `groq` and `sentence-transformers` to `requirements.txt`.
- `[x]` Run `pip install` to ensure all Week 2 dependencies are installed.

## Phase 2: AI Auto-Classifier (`classify.py`)
- `[x]` Create `classify.py` with Groq API integration.
- `[x]` Implement JSON file parser to read `raw/` captures with `status == "raw"`.
- `[x]` Write LLM prompt for PARA categorization, summary, and tagging.
- `[x]` Implement Markdown writer for the `wiki/` folder with YAML frontmatter.
- `[x]` Implement atomic update mechanism to mark original JSON records as `status: "processed"`.
- `[x]` Test `classify.py` on the 11 captured items.

## Phase 3: Semantic Linker (`link.py`)
- `[x]` Create `link.py` to initialize local `sentence-transformers` embeddings.
- `[x]` Implement Markdown parser to extract text/summaries from `wiki/` files.
- `[x]` Compute cosine similarity matrix between all notes.
- `[x]` Auto-insert bi-directional `[[Links]]` for notes exceeding similarity threshold.
- `[x]` Test `link.py` to ensure it successfully discovers relationships.

## Phase 4: Final Verification
- `[x]` Capture 4 additional test items (bringing total to 15+).
- `[x]` Verify entire pipeline success for **The Librarian** milestone.
