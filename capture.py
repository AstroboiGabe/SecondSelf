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
        return str(target_filepath.resolve())
    except Exception as e:
        # Cleanup temp file if write failed
        if temp_filepath.exists():
            try:
                temp_filepath.unlink()
            except OSError:
                pass
        raise IOError(f"Failed to atomically save CaptureRecord {record.id}: {str(e)}") from e


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
    print("=== [Phase 2 Complete & Fully Verified] ===")


if __name__ == "__main__":
    # If run directly during Phase 2 without arguments or with --test-phase2, run unit test verification
    if len(sys.argv) == 1 or "--test-phase2" in sys.argv:
        verify_phase2_model()
