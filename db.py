#!/usr/bin/env python3
"""
SecondSelf: Supabase Database Layer (db.py)
Provides persistent cloud database access for raw captures, wiki notes, and vector cache.
Compatible with local execution and Streamlit Community Cloud.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np
from dotenv import load_dotenv

# Load local .env
load_dotenv()

_supabase_client = None

def get_credentials():
    """
    Extracts Supabase credentials from local environment variables or Streamlit secrets.
    Supports both SUPABASE_* and DATABASE_* naming conventions.
    """
    url = os.getenv("SUPABASE_URL") or os.getenv("DATABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("DATABASE_KEY")

    # If running inside Streamlit, check st.secrets as fallback
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if not url:
                url = st.secrets.get("SUPABASE_URL") or st.secrets.get("DATABASE_URL")
            if not key:
                key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("DATABASE_KEY")
    except ImportError:
        pass

    return url, key


def get_client():
    """Returns an authenticated Supabase client singleton."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url, key = get_credentials()
    if not url or not key:
        print("[ERROR] Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in .env", file=sys.stderr)
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(url, key)
        return _supabase_client
    except ImportError:
        print("[ERROR] 'supabase' package is not installed. Run 'pip install supabase'", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}", file=sys.stderr)
        return None


# --- 1. Raw Captures Operations ---

def save_raw_capture(record: Dict[str, Any]) -> bool:
    """Inserts a raw capture entry into the raw_captures table."""
    client = get_client()
    if not client:
        return False
    try:
        payload = {
            "id": record.get("id"),
            "timestamp": record.get("timestamp"),
            "type": record.get("type"),
            "content": record.get("content"),
            "metadata": record.get("metadata", {}),
            "status": record.get("status", "raw")
        }
        client.table("raw_captures").upsert(payload).execute()
        return True
    except Exception as e:
        print(f"[DB ERROR] save_raw_capture failed: {e}", file=sys.stderr)
        return False


def get_pending_raw_captures() -> List[Dict[str, Any]]:
    """Fetches all unprocessed raw captures (status == 'raw')."""
    client = get_client()
    if not client:
        return []
    try:
        res = client.table("raw_captures").select("*").eq("status", "raw").execute()
        return res.data or []
    except Exception as e:
        print(f"[DB ERROR] get_pending_raw_captures failed: {e}", file=sys.stderr)
        return []


def mark_raw_capture_processed(record_id: str) -> bool:
    """Updates status to 'processed' for a raw capture."""
    client = get_client()
    if not client:
        return False
    try:
        client.table("raw_captures").update({"status": "processed"}).eq("id", record_id).execute()
        return True
    except Exception as e:
        print(f"[DB ERROR] mark_raw_capture_processed failed: {e}", file=sys.stderr)
        return False


# --- 2. Wiki Notes Operations ---

def upsert_wiki_note(note_data: Dict[str, Any]) -> bool:
    """Upserts an enriched PARA note into the wiki_notes table."""
    client = get_client()
    if not client:
        return False
    try:
        payload = {
            "id": note_data.get("id"),
            "timestamp": note_data.get("timestamp"),
            "type": note_data.get("type"),
            "category": note_data.get("category"),
            "tags": note_data.get("tags", []),
            "summary": note_data.get("summary", ""),
            "raw_content": note_data.get("raw_content", ""),
            "links": note_data.get("links", [])
        }
        client.table("wiki_notes").upsert(payload).execute()
        return True
    except Exception as e:
        print(f"[DB ERROR] upsert_wiki_note failed: {e}", file=sys.stderr)
        return False


def get_all_wiki_notes() -> List[Dict[str, Any]]:
    """Retrieves all enriched wiki notes from Supabase."""
    client = get_client()
    if not client:
        return []
    try:
        res = client.table("wiki_notes").select("*").execute()
        return res.data or []
    except Exception as e:
        print(f"[DB ERROR] get_all_wiki_notes failed: {e}", file=sys.stderr)
        return []


def get_wiki_note(note_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single wiki note by ID."""
    client = get_client()
    if not client:
        return None
    try:
        res = client.table("wiki_notes").select("*").eq("id", note_id).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"[DB ERROR] get_wiki_note failed: {e}", file=sys.stderr)
        return None


def delete_wiki_note(note_id: str) -> bool:
    """
    Permanently deletes a note across all tables in Supabase:
    - vector_cache
    - wiki_notes
    - raw_captures
    """
    client = get_client()
    if not client:
        return False
    try:
        # 1. Delete from vector_cache
        try:
            client.table("vector_cache").delete().eq("id", note_id).execute()
        except Exception:
            pass
        # 2. Delete from wiki_notes
        try:
            client.table("wiki_notes").delete().eq("id", note_id).execute()
        except Exception:
            pass
        # 3. Delete from raw_captures table
        try:
            client.table("raw_captures").delete().eq("id", note_id).execute()
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"[DB ERROR] delete_wiki_note failed: {e}", file=sys.stderr)
        return False


# --- 3. Vector Embeddings Cache Operations ---

def save_vector_cache(filenames: List[str], embeddings_matrix: np.ndarray, ids: Optional[List[str]] = None) -> bool:
    """
    Saves computed embeddings into Supabase vector_cache table.
    Takes filenames, a numpy embedding matrix, and matching note UUIDs.
    """
    client = get_client()
    if not client:
        return False
    try:
        rows = []
        for i, filename in enumerate(filenames):
            note_id = ids[i] if ids and i < len(ids) else filename.replace(".md", "")
            vector_list = embeddings_matrix[i].tolist() if hasattr(embeddings_matrix[i], "tolist") else list(embeddings_matrix[i])
            rows.append({
                "id": note_id,
                "filename": filename,
                "embedding": vector_list
            })

        if rows:
            # Batch upsert
            client.table("vector_cache").upsert(rows).execute()
        return True
    except Exception as e:
        print(f"[DB ERROR] save_vector_cache failed: {e}", file=sys.stderr)
        return False


def load_vector_cache() -> Optional[Dict[str, Any]]:
    """
    Loads all vector embeddings from Supabase vector_cache.
    Returns in exact format expected by SecondSelf:
    {'filenames': [...], 'embeddings': np.ndarray}
    """
    client = get_client()
    if not client:
        return None
    try:
        res = client.table("vector_cache").select("id, filename, embedding").execute()
        rows = res.data or []
        if not rows:
            return None

        filenames = [r["filename"] for r in rows]
        embeddings = np.array([r["embedding"] for r in rows], dtype=np.float32)

        return {
            "filenames": filenames,
            "embeddings": embeddings,
            "ids": [r["id"] for r in rows]
        }
    except Exception as e:
        print(f"[DB ERROR] load_vector_cache failed: {e}", file=sys.stderr)
        return None


def test_connection() -> bool:
    """Quick diagnostic test to verify Supabase connection."""
    client = get_client()
    if not client:
        return False
    try:
        res = client.table("raw_captures").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Supabase test_connection failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print("Testing Supabase connection...")
    if test_connection():
        print("[SUCCESS] Successfully connected to Supabase database!")
    else:
        print("[FAILED] Could not connect to Supabase. Check your .env file.")
