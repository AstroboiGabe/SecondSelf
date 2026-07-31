#!/usr/bin/env python3
"""
SecondSelf: The Cartographer (Prep) - Semantic Linker (link.py)
Uses sentence-transformers to auto-discover relationships between wiki notes.
"""

import sys
from pathlib import Path
import numpy as np
import pickle

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    print("[ERROR] 'sentence-transformers' not found. Run 'pip install -r requirements.txt'", file=sys.stderr)
    sys.exit(1)

# Similarity threshold to consider two notes "related"
SIMILARITY_THRESHOLD = 0.35

def extract_content(md_text: str) -> str:
    """Extracts the actual content of the markdown file, ignoring YAML frontmatter."""
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return md_text.strip()

def strip_existing_links(md_text: str) -> str:
    """Removes the old '## Related Notes' section to cleanly rebuild it."""
    if "## Related Notes" in md_text:
        return md_text.split("## Related Notes")[0].strip()
    return md_text.strip()

def process_links():
    script_dir = Path(__file__).resolve().parent
    wiki_dir = script_dir / "wiki"
    
    if not wiki_dir.exists():
        print(f"[ERROR] wiki/ directory not found at {wiki_dir}")
        return
        
    md_files = list(wiki_dir.glob("*.md"))
    if len(md_files) < 2:
        print("[INFO] Not enough files in wiki/ to form relationships.")
        return
        
    print(f"=== Starting Semantic Linker on {len(md_files)} wiki files ===")
    print("Loading SentenceTransformer model (this takes a moment)...")
    # all-MiniLM-L6-v2 is small, fast, and excellent for semantic similarity
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 1. Parse and extract text
    documents = []
    file_map = {}
    
    for i, filepath in enumerate(md_files):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        clean_text = strip_existing_links(raw_text)
        content_for_embedding = extract_content(clean_text)
        
        # Save clean text back to dictionary so we can append to it later
        file_map[i] = {
            "path": filepath,
            "clean_text": clean_text,
            "filename": filepath.name
        }
        documents.append(content_for_embedding)
        
    # 2. Compute embeddings
    print("Computing embeddings...")
    embeddings = model.encode(documents, convert_to_tensor=True)
    
    # 2.5 Export Embeddings Cache for ask.py
    print("Saving embeddings to cache (embeddings.pkl)...")
    cache_data = {
        "filenames": [file_map[i]["filename"] for i in range(len(md_files))],
        "embeddings": embeddings.cpu().numpy()
    }
    with open(script_dir / "embeddings.pkl", "wb") as f:
        pickle.dump(cache_data, f)
    
    # 3. Compute cosine similarity matrix
    print("Calculating cosine similarities...")
    cosine_scores = util.cos_sim(embeddings, embeddings).cpu().numpy()
    
    # 4. Generate Links
    links_added = 0
    for i in range(len(md_files)):
        related_files = []
        # We iterate over all other files (j) to find similarities
        for j in range(len(md_files)):
            if i == j:
                continue
                
            score = cosine_scores[i][j]
            if score >= SIMILARITY_THRESHOLD:
                # Found a related note!
                related_files.append((file_map[j]["filename"], score))
                
        # If we found links, append them to the file
        if related_files:
            # Sort by similarity score descending
            related_files.sort(key=lambda x: x[1], reverse=True)
            
            link_section = "\n\n## Related Notes\n"
            for rel_file, score in related_files:
                # We format it as a markdown wikilink for easy reading
                link_section += f"- [[{rel_file}]] *(Similarity: {score:.2f})*\n"
                
            new_content = file_map[i]["clean_text"] + link_section
            
            with open(file_map[i]["path"], "w", encoding="utf-8") as f:
                f.write(new_content)
                
            links_added += len(related_files)
            print(f"[{file_map[i]['filename']}] -> Linked {len(related_files)} related notes.")
            
    print(f"=== Semantic Linking Complete! Added {links_added} cross-links. ===")

if __name__ == "__main__":
    process_links()
