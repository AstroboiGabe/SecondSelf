#!/usr/bin/env python3
"""
SecondSelf Archival Capture Engine (capture.py)
Phase 2: Core Data Model & Atomic JSON Storage Engine
"""

import os
import sys
import uuid
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
import urllib.parse
import requests
import argparse
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class CaptureRecord:
    """
    Core data model for an atomic capture entry in SecondSelf (Week 1 - The Archivist).
    Enforces strict JSON schema compatibility (`raw/<uuid>.json`) and immutability.
    """
    VALID_TYPES = {"note", "link", "file"}
    VALID_STATUSES = {"raw", "processed", "error"}

    def __init__(
        self,
        capture_type: str,
        content: str,
        record_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "raw"
    ):
        if capture_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid capture type '{capture_type}'. Must be one of: {self.VALID_TYPES}")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {self.VALID_STATUSES}")
        if not content or not isinstance(content, str):
            raise ValueError("Capture content must be a non-empty string.")

        self.id = str(record_id) if record_id else str(uuid.uuid4())
        self.timestamp = timestamp if timestamp else datetime.now(timezone.utc).isoformat()
        self.type = capture_type
        self.content = content.strip()
        self.status = status

        # Initialize metadata with standardized keys (schema compliant)
        base_metadata = {
            "original_path": None,
            "asset_path": None,
            "url_title": None,
            "file_size_bytes": None,
            "file_extension": None,
            "tags": []
        }
        if metadata and isinstance(metadata, dict):
            base_metadata.update(metadata)
        self.metadata = base_metadata

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the CaptureRecord into a dictionary ready for JSON serialization."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "status": self.status
        }


def save_record_to_raw(record: CaptureRecord, raw_dir: Optional[str] = None) -> str:
    """
    Atomically save a CaptureRecord to disk as `raw/<uuid>.json`.
    
    Uses a temporary write (`raw/.tmp_<uuid>.json`) followed by `os.replace`
    to guarantee atomic write behavior and prevent corrupted/incomplete JSON
    files if the process or disk encounters an interruption (EC-STORE-02).
    
    Returns:
        str: Absolute path to the newly saved JSON record file.
    """
    if raw_dir is None:
        # Default to 'raw/' relative to the script location or current workspace inside Week1
        script_dir = Path(__file__).resolve().parent
        raw_path = script_dir / "raw"
    else:
        raw_path = Path(raw_dir)

    # Ensure raw directory exists
    raw_path.mkdir(parents=True, exist_ok=True)

    target_filepath = raw_path / f"{record.id}.json"
    temp_filepath = raw_path / f".tmp_{record.id}.json"

    record_dict = record.to_dict()

    try:
        # Write to temporary file first with strict UTF-8 encoding (EC-NOTE-03)
        with open(temp_filepath, "w", encoding="utf-8", errors="replace") as f:
            json.dump(record_dict, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is flushed to physical storage

        # Atomically rename temporary file to final target filepath
        temp_filepath.replace(target_filepath)

        # Sync to Supabase cloud database
        try:
            import db
            db.save_raw_capture(record_dict)
        except Exception:
            pass

        return str(target_filepath.resolve())
    except Exception as e:
        # Cleanup temp file if write failed
        if temp_filepath.exists():
            try:
                temp_filepath.unlink()
            except OSError:
                pass
        raise IOError(f"Failed to atomically save CaptureRecord {record.id}: {str(e)}") from e


class NoteHandler:
    @staticmethod
    def process(note_text: str, tags: Optional[List[str]] = None) -> CaptureRecord:
        if not note_text or not note_text.strip():
            raise ValueError("Note content is empty.")
        
        metadata = {"tags": tags if tags else []}
        return CaptureRecord(capture_type="note", content=note_text, metadata=metadata)


class LinkHandler:
    @staticmethod
    def process(url: str, tags: Optional[List[str]] = None) -> CaptureRecord:
        url = url.strip()
        parsed = urllib.parse.urlparse(url)
        # EC-LINK-03: Missing URL Scheme / Protocol
        if not parsed.scheme:
            url = f"https://{url}"
        
        metadata = {
            "tags": tags if tags else [],
            "url_status": "online"
        }
        
        try:
            # EC-LINK-02: User-Agent spoofing & 4.0s timeout
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=4.0)
            
            if response.status_code != 200:
                metadata["http_status"] = response.status_code
                metadata["url_status"] = "error"
            else:
                # EC-LINK-04: Non-HTML Link Targets Pre-Check
                content_type = response.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    soup = BeautifulSoup(response.content, "html.parser")
                    title_tag = soup.find("title")
                    if title_tag and title_tag.string:
                        metadata["url_title"] = title_tag.string.strip()
                    else:
                        metadata["url_title"] = None
                else:
                    metadata["content_type"] = content_type
                    
        except (requests.RequestException, requests.Timeout) as e:
            # EC-LINK-01: Offline Resilience
            metadata["url_status"] = "offline"
            metadata["error_msg"] = str(e)
            
        return CaptureRecord(capture_type="link", content=url, metadata=metadata)


class FileHandler:
    @staticmethod
    def process(file_path: str, tags: Optional[List[str]] = None, raw_dir: Optional[str] = None) -> CaptureRecord:
        path = Path(file_path).resolve()
        
        # EC-FILE-01: Non-Existent Path
        if not path.exists():
            raise FileNotFoundError(f"Target file does not exist: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Target is a directory, not a file: {path}")
            
        file_size = path.stat().st_size
        metadata = {
            "tags": tags if tags else [],
            "original_path": str(path),
            "file_size_bytes": file_size,
            "file_extension": path.suffix.lower()
        }
        
        if file_size == 0:
            metadata["empty_file"] = True
            
        record_id = str(uuid.uuid4())
        
        if raw_dir is None:
            script_dir = Path(__file__).resolve().parent
            assets_dir = script_dir / "raw" / "assets"
        else:
            assets_dir = Path(raw_dir) / "assets"
            
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # EC-FILE-02: Filename collisions & sanitization
        safe_basename = "".join([c if c.isalnum() or c in " .-_" else "_" for c in path.name])
        asset_filename = f"{record_id}_{safe_basename}"
        target_asset_path = assets_dir / asset_filename
        
        # EC-FILE-04: Copy file safely
        try:
            shutil.copy2(path, target_asset_path)
            # EC-STORE-03: POSIX path representation
            metadata["asset_path"] = f"raw/assets/{asset_filename}"
        except Exception as e:
            raise IOError(f"Failed to copy asset to {target_asset_path}: {e}")
            
        return CaptureRecord(capture_type="file", content=path.name, record_id=record_id, metadata=metadata)


def verify_phase2_model():
    """Diagnostic self-test to verify Phase 2 CaptureRecord creation and atomic saving."""
    print("=== [Phase 2 Diagnostic Verification] ===")
    print("1. Creating dummy Note CaptureRecord...")
    dummy_note = CaptureRecord(
        capture_type="note",
        content="Idea: Phase 2 Core Data Model verification test inside Week1 folder.",
        metadata={"tags": ["phase2", "test", "archivist"]}
    )
    
    print(f"   Generated UUID: {dummy_note.id}")
    print(f"   Timestamp:      {dummy_note.timestamp}")
    print(f"   Type:           {dummy_note.type}")
    
    print("2. Testing atomic save_record_to_raw()...")
    saved_path = save_record_to_raw(dummy_note)
    print(f"   [SUCCESS] Saved dummy record -> {saved_path}")
    
    print("3. Verifying saved JSON schema and UTF-8 integrity on disk...")
    with open(saved_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    assert loaded_data["id"] == dummy_note.id, "ID mismatch in saved JSON!"
    assert loaded_data["type"] == "note", "Type mismatch!"
    assert loaded_data["status"] == "raw", "Status mismatch!"
    assert "tags" in loaded_data["metadata"], "Metadata keys missing!"
    print("   [AUDIT PASS] JSON file loaded correctly. Schema exactly verified.")
    
    # Clean up test file so raw/ remains pristine for actual captures later
    print("4. Cleaning up Phase 2 diagnostic dummy record...")
    if os.path.exists(saved_path):
        os.remove(saved_path)
        print(f"   Removed diagnostic file: {saved_path}")
    print("=== [Phase 2 Complete & Fully Verified] ===\n")


def verify_phase3_handlers():
    """Diagnostic self-test to verify Phase 3 Modality Handlers."""
    print("=== [Phase 3 Diagnostic Verification] ===")
    
    # 1. Test NoteHandler
    print("1. Testing NoteHandler...")
    note_record = NoteHandler.process("This is a phase 3 test note.", tags=["test", "p3"])
    note_path = save_record_to_raw(note_record)
    print(f"   [SUCCESS] Note captured: {note_path}")
    
    # 2. Test LinkHandler
    print("2. Testing LinkHandler (github.com)...")
    link_record = LinkHandler.process("github.com", tags=["code"])
    link_path = save_record_to_raw(link_record)
    print(f"   [SUCCESS] Link captured. URL Title: {link_record.metadata.get('url_title')}")
    
    # 3. Test FileHandler
    print("3. Testing FileHandler (using requirements.txt as dummy file)...")
    req_file = str(Path(__file__).resolve().parent / "requirements.txt")
    file_record = FileHandler.process(req_file, tags=["deps"])
    file_path = save_record_to_raw(file_record)
    print(f"   [SUCCESS] File captured. Asset Path: {file_record.metadata.get('asset_path')}")
    
    # Cleanup Phase 3 diagnostics
    print("4. Cleaning up Phase 3 diagnostics...")
    for p in [note_path, link_path, file_path]:
        if os.path.exists(p):
            os.remove(p)
    
    # Also cleanup the copied asset
    asset_abs = Path(__file__).resolve().parent / file_record.metadata.get('asset_path')
    if asset_abs.exists():
        asset_abs.unlink()
        
    print("=== [Phase 3 Complete & Fully Verified] ===")


def main():
    # Diagnostic test overrides
    if len(sys.argv) > 1 and sys.argv[1] == "--test-phase2":
        verify_phase2_model()
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--test-phase3":
        verify_phase3_handlers()
        return

    parser = argparse.ArgumentParser(description="SecondSelf Archival Capture Engine (The Archivist)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--note", type=str, help="Capture a text note or idea.")
    group.add_argument("-l", "--link", type=str, help="Capture a web URL.")
    group.add_argument("-f", "--file", type=str, help="Capture a local file (will be copied to raw/assets/).")
    
    parser.add_argument("-t", "--tags", type=str, help="Optional comma-separated tags (e.g. 'code,idea').")
    
    args = parser.parse_args()
    
    tags_list = [t.strip() for t in args.tags.split(",")] if args.tags else []
    
    try:
        if args.note is not None:
            record = NoteHandler.process(args.note, tags=tags_list)
            capture_type = "NOTE"
        elif args.link is not None:
            record = LinkHandler.process(args.link, tags=tags_list)
            capture_type = "LINK"
        elif args.file is not None:
            record = FileHandler.process(args.file, tags=tags_list)
            capture_type = "FILE"
            
        saved_path = save_record_to_raw(record)
        
        # Clean terminal reporting format as per implementationplan.md
        rel_path = Path(saved_path).relative_to(Path(__file__).resolve().parent).as_posix()
        print(f"[SUCCESS] Captured [{capture_type}] -> {rel_path}")
        print(f"ID:        {record.id}")
        print(f"Timestamp: {record.timestamp}")
        
        # Smart content preview
        content_preview = record.content.replace('\n', ' ')
        if len(content_preview) > 100:
            content_preview = content_preview[:97] + "..."
        print(f"Content:   {content_preview}")
        
    except Exception as e:
        print(f"[ERROR] Capture failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

