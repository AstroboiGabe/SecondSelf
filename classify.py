#!/usr/bin/env python3
"""
SecondSelf: The Librarian - AI Auto-Classifier (classify.py)
Reads raw captures, queries Groq (Llama-3), assigns PARA categories, and writes to wiki/.
"""

import os
import json
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    print("[ERROR] 'groq' package not found. Did you run 'pip install -r requirements.txt'?", file=sys.stderr)
    sys.exit(1)

# Load environment variables
load_dotenv()

# Check API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("[ERROR] GROQ_API_KEY not found in environment or .env file.", file=sys.stderr)
    sys.exit(1)

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)

# PARA Categories allowed
VALID_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]

def get_system_prompt() -> str:
    return """You are the Librarian of the 'SecondSelf' personal knowledge base.
Your job is to read a raw capture (a note, a web link, or a file snippet) and autonomously classify it according to the PARA method.

PARA Categories:
1. Projects: Short-term efforts in your work or life that you're working on now.
2. Areas: Long-term responsibilities you want to manage over time.
3. Resources: Topics or interests that may be useful in the future.
4. Archives: Inactive items from the other three categories.

Instructions:
1. Analyze the provided content.
2. Choose exactly ONE of the PARA categories. If you are unsure, default to 'Resources'.
3. Generate a 1-sentence concise summary of the content.
4. Generate 2 to 5 relevant tags.

You MUST respond ONLY with valid JSON in the exact structure below, with no markdown formatting or conversational text outside the JSON:
{
  "category": "Projects | Areas | Resources | Archives",
  "summary": "1-sentence summary",
  "tags": ["tag1", "tag2"]
}"""


def query_llm_classification(content: str) -> dict:
    """Sends the content to Groq and parses the JSON response."""
    # Truncate content to avoid exceeding context window (keep it lightweight)
    safe_content = content[:8000] if content else "Empty content"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Updated to current supported model
        messages=[
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": f"Classify this capture:\n\n{safe_content}"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    raw_output = response.choices[0].message.content.strip()
    
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        # Fallback extraction if LLM still wraps in markdown
        match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"Failed to parse LLM response as JSON: {raw_output}")
            
    # Validate PARA category
    if data.get("category") not in VALID_CATEGORIES:
        data["category"] = "Resources"
        
    return data


def write_to_wiki(record: dict, classification: dict, wiki_dir: Path):
    """Writes the enriched record as a Markdown file with YAML frontmatter."""
    wiki_dir.mkdir(parents=True, exist_ok=True)
    
    uuid_str = record.get("id")
    target_md = wiki_dir / f"{uuid_str}.md"
    
    # Safely extract existing user tags and merge with AI tags
    user_tags = record.get("metadata", {}).get("tags", [])
    ai_tags = classification.get("tags", [])
    all_tags = list(set([str(t).lower().strip() for t in (user_tags + ai_tags)]))
    
    # Build YAML Frontmatter
    md_content = "---\n"
    md_content += f"id: {uuid_str}\n"
    md_content += f"timestamp: {record.get('timestamp')}\n"
    md_content += f"type: {record.get('type')}\n"
    md_content += f"category: {classification.get('category')}\n"
    
    # Handle tags cleanly
    if all_tags:
        md_content += "tags:\n"
        for t in all_tags:
            md_content += f"  - {t}\n"
    else:
        md_content += "tags: []\n"
        
    # Inject source file references if available
    asset_path = record.get("metadata", {}).get("asset_path")
    if asset_path:
        md_content += f"asset_path: {asset_path}\n"
        
    md_content += "---\n\n"
    
    # Write the Markdown Body
    md_content += f"# Summary\n{classification.get('summary', 'No summary provided.')}\n\n"
    md_content += "---\n\n"
    md_content += f"## Raw Content\n{record.get('content', '')}\n"
    
    with open(target_md, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    return target_md


def process_raw_captures():
    script_dir = Path(__file__).resolve().parent
    raw_dir = script_dir / "raw"
    wiki_dir = script_dir / "wiki"
    
    if not raw_dir.exists():
        print(f"[ERROR] raw/ directory not found at {raw_dir}")
        return
        
    # Find all unprocessed JSON files
    json_files = list(raw_dir.glob("*.json"))
    pending_files = []
    
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("status") == "raw":
                pending_files.append((jf, data))
        except Exception:
            pass
            
    if not pending_files:
        print("[INFO] No pending raw captures to process.")
        return
        
    print(f"=== Starting Auto-Classification on {len(pending_files)} records ===")
    
    for filepath, record in pending_files:
        print(f"Processing {record.get('id')} ({record.get('type')})...", end=" ", flush=True)
        
        try:
            # 1. Ask LLM to classify
            classification = query_llm_classification(record.get("content", ""))
            
            # 2. Write to Wiki
            wiki_path = write_to_wiki(record, classification, wiki_dir)
            
            # 3. Mark raw record as processed (Atomic update)
            record["status"] = "processed"
            tmp_path = filepath.with_name(f".tmp_{filepath.name}")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            tmp_path.replace(filepath)
            
            print(f"[OK] -> {classification.get('category')} | {wiki_path.name}")
            
        except Exception as e:
            print(f"[FAILED] {str(e)}")
            
    print("=== Auto-Classification Complete ===")

if __name__ == "__main__":
    process_raw_captures()
