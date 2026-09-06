#!/usr/bin/env python3
"""
SecondSelf: Supabase Data Migration Tool (migrate_to_supabase.py)
Clones all existing local files (raw captures, wiki notes, and vector cache)
directly into your Supabase database so no previous work is lost.
"""

import os
import json
import re
import pickle
from pathlib import Path
import numpy as np

import db

def parse_markdown_note(filepath: Path) -> dict:
    """Parses frontmatter, summary, raw content, and links from a wiki markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Frontmatter
    frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    metadata = {}
    tags = []
    if frontmatter_match:
        lines = frontmatter_match.group(1).split("\n")
        in_tags = False
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("tags:"):
                in_tags = True
                continue
            if in_tags:
                if line_str.startswith("-"):
                    tag_val = line_str.lstrip("-").strip()
                    if tag_val:
                        tags.append(tag_val)
                elif ":" in line:
                    in_tags = False
            if ":" in line and not in_tags:
                k, v = line.split(":", 1)
                metadata[k.strip()] = v.strip()

    note_id = metadata.get("id") or filepath.stem

    # 2. Summary
    summary_match = re.search(r"# Summary\n(.*?)\n---", content, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    # 3. Raw Content
    raw_content_match = re.search(r"## Raw Content\n(.*?)(?=\n## Related Notes|\Z)", content, re.DOTALL)
    raw_content = raw_content_match.group(1).strip() if raw_content_match else ""

    # 4. Related Links
    links = []
    links_match = re.search(r"## Related Notes\n(.*)", content, re.DOTALL)
    if links_match:
        for line in links_match.group(1).split("\n"):
            m = re.search(r"\[\[(.*?)\]\]", line)
            if m:
                links.append(m.group(1).strip())

    return {
        "id": note_id,
        "timestamp": metadata.get("timestamp"),
        "type": metadata.get("type", "note"),
        "category": metadata.get("category", "Resources"),
        "tags": tags,
        "summary": summary,
        "raw_content": raw_content,
        "links": links
    }


def migrate():
    script_dir = Path(__file__).resolve().parent
    raw_dir = script_dir / "raw"
    wiki_dir = script_dir / "wiki"
    cache_path = script_dir / "embeddings.pkl"

    client = db.get_client()
    if not client:
        print("[ERROR] Cannot connect to Supabase. Aborting migration.")
        return

    print("==========================================")
    print("  SecondSelf: Migrating Data to Supabase  ")
    print("==========================================")

    # 1. Migrate raw captures
    raw_files = list(raw_dir.glob("*.json")) if raw_dir.exists() else []
    print(f"\n[1/3] Found {len(raw_files)} raw JSON files...")
    migrated_raw = 0
    for rf in raw_files:
        if rf.name.startswith(".tmp_"):
            continue
        try:
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if db.save_raw_capture(data):
                migrated_raw += 1
        except Exception as e:
            print(f"  [WARN] Failed to migrate {rf.name}: {e}")

    print(f"  -> Successfully migrated {migrated_raw}/{len(raw_files)} raw captures.")

    # 2. Migrate wiki notes
    wiki_files = list(wiki_dir.glob("*.md")) if wiki_dir.exists() else []
    print(f"\n[2/3] Found {len(wiki_files)} wiki markdown files...")
    migrated_wiki = 0
    for wf in wiki_files:
        try:
            note_record = parse_markdown_note(wf)
            if db.upsert_wiki_note(note_record):
                migrated_wiki += 1
        except Exception as e:
            print(f"  [WARN] Failed to migrate {wf.name}: {e}")

    print(f"  -> Successfully migrated {migrated_wiki}/{len(wiki_files)} wiki notes.")

    # 3. Migrate vector cache
    print(f"\n[3/3] Checking embeddings cache ({cache_path.name})...")
    migrated_vectors = 0
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)
            filenames = cache_data.get("filenames", [])
            embeddings = cache_data.get("embeddings", [])

            if len(filenames) > 0 and len(embeddings) > 0:
                if db.save_vector_cache(filenames, embeddings):
                    migrated_vectors = len(filenames)
                    print(f"  -> Successfully migrated {migrated_vectors} vector embeddings.")
                else:
                    print("  [WARN] Failed to save vector cache to Supabase.")
        except Exception as e:
            print(f"  [WARN] Error reading embeddings cache: {e}")
    else:
        print("  -> No embeddings.pkl found. Vector cache will be generated during pipeline run.")

    print("\n==========================================")
    print("  Migration Complete! Summary:")
    print(f"  - Raw Captures:   {migrated_raw}")
    print(f"  - Wiki Notes:     {migrated_wiki}")
    print(f"  - Vector Entries: {migrated_vectors}")
    print("==========================================")


if __name__ == "__main__":
    migrate()
