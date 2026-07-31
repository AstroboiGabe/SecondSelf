#!/usr/bin/env python3
"""
Diagnostic Audit Script: verify_capture.py
Phase 5 Automated Verification Check
"""

import os
import json
from pathlib import Path

def run_audit():
    script_dir = Path(__file__).resolve().parent
    raw_dir = script_dir / "raw"
    assets_dir = raw_dir / "assets"
    
    if not raw_dir.exists():
        print("[FAIL] raw/ directory does not exist.")
        return
        
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        print("[FAIL] No JSON records found in raw/.")
        return
        
    print(f"=== Starting Audit of {len(json_files)} capture records ===")
    
    passed_count = 0
    failed_count = 0
    
    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # 1. Schema Validation
            assert "id" in data, "Missing 'id'"
            assert "timestamp" in data, "Missing 'timestamp'"
            assert "type" in data and data["type"] in {"note", "link", "file"}, f"Invalid type: {data.get('type')}"
            assert "content" in data, "Missing 'content'"
            assert data["status"] == "raw", f"Status not raw: {data.get('status')}"
            
            # 2. Asset Verification
            if data["type"] == "file":
                asset_path_str = data.get("metadata", {}).get("asset_path")
                assert asset_path_str, "File record missing asset_path metadata"
                
                # Resolve the relative asset path
                asset_abs_path = script_dir / asset_path_str
                assert asset_abs_path.exists(), f"Asset file missing on disk: {asset_abs_path}"
                
            passed_count += 1
            
        except Exception as e:
            failed_count += 1
            print(f"[ERROR] Record {filepath.name} failed audit: {e}")
            
    print("\n=== Audit Report ===")
    print(f"Total Records: {len(json_files)}")
    print(f"Passed:        {passed_count}")
    print(f"Failed:        {failed_count}")
    
    if passed_count >= 10 and failed_count == 0:
        print("\n[AUDIT PASS] 10+ JSON records valid. Schema and asset integrity fully verified!")
        print("[Milestone Earned] The Archivist")
    else:
        print("\n[AUDIT FAIL] Did not meet criteria for The Archivist badge.")

if __name__ == "__main__":
    run_audit()
