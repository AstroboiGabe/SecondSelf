# SecondSelf Week 4 Walkthrough: The Oracle

Congratulations! We have successfully finished executing the **Week 4 Implementation Plan**, which officially marks the completion of the entire **SecondSelf** project!

## 1. What was built

### The Caching Indexer ([`embeddings.pkl`](file:///c:/Users/dep6g/Documents/Cohort%20Projects/July%20Cohort/Week1/embeddings.pkl))
- We upgraded our original `link.py` script to not just calculate vector embeddings, but to permanently save them to your hard drive as an `embeddings.pkl` file. 
- This acts as an ultra-fast local vector database, allowing the system to perform semantic math in milliseconds instead of reloading the AI model every time you ask a question.

### The Oracle Q&A Engine ([`ask.py`](file:///c:/Users/dep6g/Documents/Cohort%20Projects/July%20Cohort/Week1/ask.py))
- We built a powerful Command Line Interface (CLI) that acts as a local **Retrieval-Augmented Generation (RAG)** pipeline.
- When you ask a natural language question (e.g., `python ask.py "What is PARA?"`), the script instantly compares the mathematical meaning of your question against the `embeddings.pkl` cache.
- It pulls the **Top 5** most relevant `.md` notes from your `wiki/` directory.
- It injects those 5 notes into a strict system prompt and sends it to the Groq Llama 3 API to synthesize a customized answer.

## 2. Validation Results

You successfully validated the two core capabilities of The Oracle:

1. **Semantic Recall**: It accurately retrieved information from your knowledge base and answered your queries while explicitly citing the exact source files it used.
2. **Strict Guardrails**: When prompted with out-of-bounds questions (like pancake recipes), the strict system prompt successfully constrained the AI, forcing it to admit it did not have the information in your notes rather than hallucinating an answer.

## 🏆 Project Completion: The Oracle Milestone
You have officially earned **The Oracle** badge, completing the 4-week journey of SecondSelf! 

You took a completely raw stream of data and transformed it into a self-organizing (Week 2), highly visual (Week 3), and fully conversational (Week 4) "Second Brain". 

**Your entire workflow is now functional:**
- `python capture.py` -> Ingests raw data.
- `python classify.py` -> Organizes it with AI.
- `python link.py` -> Generates the knowledge graph and vector cache.
- `index.html` -> Lets you explore the web visually.
- `python ask.py "query"` -> Lets you chat with your brain.

Incredible work!
