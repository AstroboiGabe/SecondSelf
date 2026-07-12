# SecondSelf: Phase-Wise Implementation Plan (Week 1 — The Archivist)

## Executive Summary
This implementation plan breaks down the construction of the **Week 1 Capture Pipeline ("The Archivist")** into 6 actionable, modular phases based on `problemstatement.md` and `architecture.md`. By executing this plan phase-by-phase, you will build a robust, local-first ingestion engine capable of capturing notes, web links, and local files into atomic, immutable JSON records (`raw/<uuid>.json`) alongside asset copies (`raw/assets/`), preparing a clean foundation for Week 2's AI self-organization pipeline.

---

## Phase 1: Project Environment & Workspace Initialization

### 1.1 Objectives
- Establish the standardized directory tree required by the SecondSelf architecture (`raw/`, `raw/assets/`, `wiki/`).
- Set up Python virtual environment and dependency tracking.
- Create git exclusion rules to safeguard local assets and credentials while preserving directory hierarchy.

### 1.2 Action Items
1. **Directory Structure Creation**:
   - Create `raw/` directory (immutable ingestion zone).
   - Create `raw/assets/` subdirectory (local file storage).
   - Create `wiki/` directory (target structured workspace for Week 2).
   - Place `.gitkeep` inside `raw/assets/` and `wiki/` so empty folders are tracked by Git.
2. **Dependency Configuration (`requirements.txt`)**:
   Create a clean `requirements.txt` specifying lightweight dependencies:
   ```text
   requests>=2.31.0
   beautifulsoup4>=4.12.0
   ```
3. **Version Control (`.gitignore`)**:
   Create a `.gitignore` configured for Python and SecondSelf:
   ```text
   # Python
   __pycache__/
   *.py[cod]
   *.egg-info/
   .venv/
   venv/
   
   # SecondSelf Data (Optional: comment out if syncing raw data to private git repo)
   # raw/*.json
   # raw/assets/*
   # !raw/assets/.gitkeep
   ```

### 1.3 Phase 1 Verification Checklist
- [ ] Folder tree (`raw/`, `raw/assets/`, `wiki/`) exists locally.
- [ ] `pip install -r requirements.txt` runs cleanly without errors.

---

## Phase 2: Core Data Model & JSON Storage Layer (`capture.py` Engine)

### 2.1 Objectives
- Implement the atomic data model (`CaptureRecord`) enforcing strict schema compliance.
- Implement robust filesystem helpers for atomic JSON writes and safe file copying.

### 2.2 Action Items
1. **Create `CaptureRecord` Data Class (`capture.py`)**:
   Define the core data class or dict generator encapsulating:
   - `id`: Generated via `uuid.uuid4()`.
   - `timestamp`: Current UTC time formatted in strict ISO 8601 (`datetime.now(timezone.utc).isoformat()`).
   - `type`: Enforced enum (`"note"`, `"link"`, or `"file"`).
   - `content`: Primary payload string (note body, URL, or local file description).
   - `metadata`: Dictionary storing `original_path`, `asset_path`, `url_title`, `file_size_bytes`, `file_extension`.
   - `status`: Defaulted to `"raw"` (to be consumed by `classify.py` in Week 2).
2. **Implement Atomic Storage Engine**:
   - Write `save_record_to_raw(record: dict) -> str`:
     - Serializes `record` to `raw/<uuid>.json` with `indent=2` and `ensure_ascii=False`.
     - Uses UTF-8 encoding (`encoding='utf-8', errors='replace'`) to handle emojis and international text safely.
     - Returns the exact absolute path of the created JSON file for confirmation.

### 2.3 Phase 2 Verification Checklist
- [ ] Unit test: Generating and saving a dummy `CaptureRecord` creates a valid JSON file in `raw/` matching the schema exactly.

---

## Phase 3: Modality Handlers (`capture.py` Handlers Layer)

### 3.1 Objectives
- Build specialized input handlers (`NoteHandler`, `LinkHandler`, `FileHandler`) capable of processing and enriching each specific capture type.

### 3.2 Action Items
1. **Implement `NoteHandler.process(note_text: str) -> dict`**:
   - Validates that `note_text` is non-empty.
   - Sets `type = "note"`, `content = note_text.strip()`.
   - Sets empty/null metadata (`original_path = None`, `asset_path = None`, etc.).
2. **Implement `LinkHandler.process(url: str) -> dict`**:
   - Validates basic URL formatting (`http://` or `https://`).
   - Implements `fetch_link_metadata(url: str, timeout=4.0) -> dict`:
     - Sends HTTP GET request with a standard User-Agent header and a strict 4-second timeout.
     - Uses `BeautifulSoup` to extract `<title>` and `<meta name="description" content="...">`.
     - **Offline/Error Resilience**: If the request times out, returns 404/500, or if offline, catches `RequestException`, sets `url_title = None`, and logs a warning *without crashing*.
   - Sets `type = "link"`, `content = url`.
3. **Implement `FileHandler.process(file_path: str) -> dict`**:
   - Validates `os.path.exists(file_path)` and checks `os.path.isfile(file_path)`.
   - Extracts metadata: `file_size_bytes = os.path.getsize(...)`, `file_extension = os.path.splitext(...)[1]`.
   - Generates a unique asset filename: `asset_filename = f"{uuid_str}_{os.path.basename(file_path)}"`.
   - Copies the file securely to `raw/assets/{asset_filename}` using `shutil.copy2()`.
   - Sets `type = "file"`, `content = os.path.basename(file_path)`, and populates `metadata.asset_path` and `metadata.original_path`.

### 3.3 Phase 3 Verification Checklist
- [ ] `NoteHandler` correctly trims multiline strings and produces accurate JSON.
- [ ] `LinkHandler` extracts page titles when online and gracefully falls back when offline or given invalid URLs.
- [ ] `FileHandler` copies target documents into `raw/assets/` and records precise byte sizes.

---

## Phase 4: Command-Line Interface & Router (`capture.py` CLI Layer)

### 4.1 Objectives
- Provide a unified, elegant terminal interface allowing one command to capture anything (`python capture.py --note "..."`).

### 4.2 Action Items
1. **Configure CLI Argument Parser (`argparse`)**:
   - Set up `argparse.ArgumentParser(description="SecondSelf Archival Capture Engine")`.
   - Create a mutually exclusive group (`group = parser.add_mutually_exclusive_group(required=True)`) containing:
     - `-n, --note`: String argument for quick note captures.
     - `-l, --link`: String argument for URL captures.
     - `-f, --file`: Path argument for local file ingestions.
   - Add optional flags:
     - `-t, --tags`: Optional comma-separated user tags (stored in `metadata.initial_tags`).
2. **Implement Router & Terminal Reporting**:
   - Route CLI input to the appropriate handler based on which flag is invoked.
   - Output a clean, structured confirmation to stdout upon successful capture:
     ```text
     [SUCCESS] Captured [NOTE] -> raw/3f0e81b2-11c3-4d40-8b1a-98126b8e21a0.json
     ID:        3f0e81b2-11c3-4d40-8b1a-98126b8e21a0
     Timestamp: 2026-07-12T08:45:10+00:00
     Content:   Idea: Use graph centrality to identify key concepts.
     ```

### 4.3 Phase 4 Verification Checklist
- [ ] Running `python capture.py --help` displays clean, descriptive usage options.
- [ ] Invoking multiple flags simultaneously (e.g., `--note "a" --link "b"`) raises a clear `--help` validation error.

---

## Phase 5: Real Data Ingestion & System Testing (The Archivist Milestone)

### 5.1 Objectives
- Rigorously test the end-to-end capture pipeline against real personal knowledge items.
- Satisfy all acceptance criteria to achieve **The Archivist** milestone badge.

### 5.2 Action Items
1. **Ingest 10+ Real Personal Items**:
   - **Notes (4+ items)**: Capture actual project ideas, code snippets, or thoughts.
     - *Example*: `python capture.py --note "PARA structure separates actionable projects from long-term areas of responsibility."`
   - **Links (3+ items)**: Capture real web articles, documentation pages, or GitHub repos.
     - *Example*: `python capture.py --link "https://github.com/langchain-ai/langchain"`
   - **Files (3+ items)**: Capture real PDFs, text files, or diagrams on your machine.
     - *Example*: `python capture.py --file "C:/Users/dep6g/Documents/sample_research.pdf"`
2. **Automated Verification Check (`verify_capture.py`)**:
   - Create a lightweight diagnostic script (`verify_capture.py`) that scans `raw/`, parses every `.json` file, verifies schema validation (`uuid`, `timestamp`, `type`), checks that asset files in `raw/assets/` exist, and prints an audit report.

### 5.3 Phase 5 Acceptance Criteria Checklist
- [ ] `raw/` and `wiki/` folder structure exists.
- [ ] One command (`capture.py`) captures a **note**, a **link**, AND a **file**.
- [ ] Every capture has a valid **timestamp** and **unique ID**.
- [ ] **10+ real items** captured and verified inside `raw/`.
- [ ] **🏅 Badge Earned**: **The Archivist**.

---

## Phase 6: Roadmap & Preparation for Week 2 (The Librarian Handoff)

### 6.1 Objectives
- Establish clear interfaces and data contracts for how Week 2's `classify.py` and `link.py` will consume the Week 1 `raw/` archive.

### 6.2 Action Items & Handoff Specification
1. **Processing Loop Contract (`classify.py`)**:
   - In Week 2, `classify.py` will iterate through `os.listdir('raw/')`, filter for `status == "raw"`, query the Groq/Llama-3 LLM to assign `PARA` categories/tags/summaries, and write structured Markdown files to `wiki/<uuid>.md` (or `wiki/<clean-title>.md`).
   - Once successfully processed, `classify.py` will update the raw JSON record in `raw/<uuid>.json` to `status: "processed"`.
2. **Immutability Guarantee**:
   - The original `content` and `metadata` in `raw/<uuid>.json` and copied files in `raw/assets/` will **never** be deleted or modified by Week 2 scripts, preserving full pipeline replayability.

---

## Summary Implementation Schedule

| Phase | Milestone / Component | Core Deliverable | Estimated Effort |
| :---: | :--- | :--- | :---: |
| **Phase 1** | Workspace & Environment | `raw/`, `wiki/`, `requirements.txt`, `.gitignore` | ~15 mins |
| **Phase 2** | Core Data Model | `CaptureRecord` class & atomic `save_record()` | ~30 mins |
| **Phase 3** | Modality Handlers | `NoteHandler`, `LinkHandler`, `FileHandler` | ~45 mins |
| **Phase 4** | CLI Router | `capture.py` (`argparse` engine & stdout formatting) | ~30 mins |
| **Phase 5** | Real Data Verification | 10+ real items captured in `raw/` & `verify_capture.py` | ~45 mins |
| **Phase 6** | Week 2 Handoff Setup | Handoff documentation & schema readiness | ~15 mins |
