# SecondSelf Week 2: The Librarian (Auto-Classify & Auto-Link)

This plan covers Week 2 of SecondSelf, which introduces AI to autonomously organize and interlink the raw knowledge captured in Week 1.

## User Review Required

> [!IMPORTANT]
> - **LLM Provider Choice**: The original prompt suggests using Groq (Llama 3) for the auto-classification step. To proceed with this, we will need to add a `GROQ_API_KEY` to your `.env` file. 
> - **Embeddings Choice**: The prompt suggests `sentence-transformers`, which runs 100% locally and free. This requires installing PyTorch and downloading the embedding model.

## Open Questions

> [!WARNING]
> 1. Do you already have a Groq API key, or would you prefer to use a different provider like OpenAI or a local Ollama instance?
> 2. Should `classify.py` and `link.py` be executed as separate terminal commands, or would you prefer a unified `organize.py` script that runs both in sequence?

## Proposed Changes

---
### AI Auto-Classifier (Week 2.1)

#### [NEW] classify.py
- Connects to the chosen LLM API.
- Scans `raw/*.json` for records where `status == "raw"`.
- Prompts the LLM to output a strict JSON response containing a PARA category (Projects, Areas, Resources, Archives), a 1-line summary, and tags.
- Writes an enriched Markdown file to the `wiki/` directory (e.g., `wiki/<uuid>.md` or `wiki/<title>.md`) with YAML frontmatter.
- Updates the original `raw/<uuid>.json` to `status: "processed"`.

---
### Semantic Linker (Week 2.2)

#### [NEW] link.py
- Uses `sentence-transformers/all-MiniLM-L6-v2` to compute vector embeddings for all notes in `wiki/`.
- Computes cosine similarity between new captures and existing notes.
- Automatically inserts bidirectional Markdown links (e.g., `[[Related Note]]`) at the bottom of the Markdown files when similarity exceeds a defined threshold (e.g., 0.65).

#### [MODIFY] requirements.txt
- Add `groq` (or the SDK for your chosen LLM).
- Add `sentence-transformers` and its dependencies for local embeddings.

## Verification Plan

### Automated Tests
- Run `classify.py` on a single test capture to verify the LLM correctly follows the PARA JSON schema and handles API timeouts gracefully.
- Run `link.py` on two semantically related test notes to verify that the cosine similarity crosses the threshold and a link is appended.

### Manual Verification
- We currently have 11 items in the `raw/` folder. We will need to capture 4 more to hit the **15+ real items** requirement.
- Execute the full Week 2 pipeline on all 15+ items.
- Visually inspect the `wiki/` folder to confirm the Markdown files are properly categorized and cross-linked without any manual tagging.
