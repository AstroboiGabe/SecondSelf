#!/usr/bin/env python3
"""
SecondSelf: The Oracle (ask.py)
Natural language Q&A engine for the knowledge base using local RAG and Groq.
"""

import sys
import os
import pickle
import argparse
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    print("[ERROR] 'sentence-transformers' not found. Run 'pip install -r requirements.txt'")
    sys.exit(1)

try:
    from groq import Groq
except ImportError:
    print("[ERROR] 'groq' not found. Run 'pip install -r requirements.txt'")
    sys.exit(1)

# Check for API key
from dotenv import load_dotenv
load_dotenv()

if not os.environ.get("GROQ_API_KEY"):
    print("[ERROR] GROQ_API_KEY is missing from .env")
    sys.exit(1)

client = Groq()

def load_cache(cache_path: Path):
    if not cache_path.exists():
        print(f"[ERROR] Embeddings cache not found at {cache_path}. Run link.py first.")
        sys.exit(1)
    with open(cache_path, "rb") as f:
        return pickle.load(f)

def read_wiki_file(wiki_dir: Path, filename: str) -> str:
    path = wiki_dir / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def main():
    parser = argparse.ArgumentParser(description="Ask a question to your SecondSelf knowledge base.")
    parser.add_argument("query", type=str, help="The question you want to ask")
    args = parser.parse_args()
    
    script_dir = Path(__file__).resolve().parent
    wiki_dir = script_dir / "wiki"
    cache_path = script_dir / "embeddings.pkl"
    
    print("Loading AI embeddings model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Loading knowledge base cache...")
    cache_data = load_cache(cache_path)
    filenames = cache_data["filenames"]
    embeddings = cache_data["embeddings"]
    
    print("Searching for relevant notes...")
    # Encode query
    query_embedding = model.encode(args.query, convert_to_tensor=True)
    
    # Compute similarity against cache
    cosine_scores = util.cos_sim(query_embedding, embeddings)[0].cpu().numpy()
    
    # Get top 5 indices
    top_k = min(5, len(filenames))
    top_indices = np.argsort(cosine_scores)[::-1][:top_k]
    
    # Collect context from the top 5 files
    context_text = ""
    citations = []
    
    for idx in top_indices:
        filename = filenames[idx]
        score = cosine_scores[idx]
        content = read_wiki_file(wiki_dir, filename)
        context_text += f"\n--- NOTE: {filename} ---\n{content}\n"
        citations.append(f"{filename} (Relevance: {score:.2f})")
        
    print(f"Synthesizing answer using {len(citations)} notes...")
    
    system_prompt = (
        "You are 'The Oracle', an AI assistant for the user's personal knowledge base.\n"
        "You will be provided with a set of notes retrieved from their wiki.\n"
        "Your task is to answer the user's query STRICTLY based on the provided notes.\n"
        "CRITICAL INSTRUCTION: If the answer cannot be found in the provided notes, you MUST say "
        "'I don't know based on the provided notes.' Do NOT use outside knowledge to fill in gaps."
    )
    
    user_prompt = f"USER QUERY: {args.query}\n\nRELEVANT NOTES:\n{context_text}"
    
    try:
        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, # Low temperature for factual extraction
            max_tokens=1024
        )
        answer = response.choices[0].message.content
        
        print("\n=== THE ORACLE'S ANSWER ===")
        print(answer)
        print("\n=== CITATIONS (Top 5 Sources) ===")
        for c in citations:
            print(f"- {c}")
            
    except Exception as e:
        print(f"\n[FAILED] Error querying Groq API: {e}")

if __name__ == "__main__":
    main()
