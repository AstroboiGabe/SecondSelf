# SecondSelf: Corner Scenarios & Edge-Case Catalog (`edgecase.md`)

## Executive Summary & Philosophy
In the **SecondSelf** architecture, Week 1 (**The Archivist**) acts as the immutable gateway for all downstream processing. If the archival capture pipeline crashes, corrupts data, or fails to handle corner cases gracefully, downstream layers (Week 2 AI sorting, Week 3 graph rendering, and Week 4 RAG synthesis) will suffer from cascading failures. 

This document provides an exhaustive catalog of all potential corner scenarios, boundary conditions, and edge cases across the capture pipeline (`capture.py`), filesystem storage (`raw/`), and downstream interfaces, along with concrete engineering mitigations.

---

## 1. Modality-Specific Edge Cases (`capture.py` Handlers)

### 1.1 Text Notes (`NoteHandler`)

| Edge Case ID | Scenario & Boundary Condition | Potential Impact | Engineering Mitigation & Handling Strategy |
| :--- | :--- | :--- | :--- |
| **EC-NOTE-01** | **Empty or Whitespace-Only Note**<br>Command: `python capture.py --note "   "` | Generation of useless, zero-information records that waste LLM tokens during Week 2 classification. | **Pre-Validation**: Strip leading/trailing whitespace (`note.strip()`). If `len(note) == 0`, abort capture immediately and output an informative CLI warning (`[WARNING] Note content is empty. Nothing captured.`). |
| **EC-NOTE-02** | **Multi-Line & Escaped Shell Characters**<br>Notes containing `\n`, `\t`, `"`, `'`, `$var`, or Windows CMD/PowerShell escape characters. | Shell parsing errors, variable expansion surprises (`$var`), or broken JSON strings during serialization. | **Input Normalization & Raw Serialization**: Ensure `CaptureRecord` serializes strings using `json.dump(ensure_ascii=False)` which automatically handles internal quotes and newlines. Document Windows PowerShell safe-quoting practices (`--note '...'` vs `--note "..."`). |
| **EC-NOTE-03** | **Unicode, Emojis & RTL (Right-to-Left) Text**<br>Notes with rich emojis (💡🚀🧠), Japanese/Kanji, or Arabic/Hebrew text. | `UnicodeEncodeError` on Windows terminal outputs or ASCII corruption (`????`) when writing to disk. | **Strict UTF-8 Enforcement**: Open target files with `open(path, 'w', encoding='utf-8', errors='replace')`. Configure stdout wrapping if necessary (`sys.stdout.reconfigure(encoding='utf-8')`). |
| **EC-NOTE-04** | **Massive String Input (Megabyte Notes)**<br>Piping a 10MB log dump directly into `--note`. | High memory usage, UI lag during Week 3 graph rendering, or exceeding LLM context limits in Week 2. | **Payload Size Threshold**: If `len(note_text) > 100_000` (~20k words), emit a terminal warning: `[WARNING] Large note detected (X KB). Consider saving as a --file instead.` Proceed with capture but flag `metadata.large_payload: true`. |

---

### 1.2 Web Links (`LinkHandler`)

| Edge Case ID | Scenario & Boundary Condition | Potential Impact | Engineering Mitigation & Handling Strategy |
| :--- | :--- | :--- | :--- |
| **EC-LINK-01** | **Complete Offline / Network Unavailability**<br>Capturing a link while disconnected from Wi-Fi. | `requests.ConnectionError` causes the capture tool to crash, violating `"Capture Everything, Lose Nothing"`. | **Offline Resilience**: Wrap `requests.get()` in a `try...except (requests.RequestException, Timeout)` block. On exception, log a silent warning, set `url_title: null`, `url_status: "offline"`, and save the raw URL string immediately. |
| **EC-LINK-02** | **HTTP Error Responses (403/404/500 & Cloudflare)**<br>Target site blocks scrapers, returns 404 Not Found, or requires Javascript/login. | `<title>` scraper throws errors or returns generic Cloudflare block pages (`"Attention Required! | Cloudflare"`). | **User-Agent Spoofing & Header Checks**: Send standard browser headers (`{'User-Agent': 'Mozilla/5.0 ...'}`). Check `response.status_code == 200` before `BeautifulSoup` parsing. If blocked or non-200, set `metadata.http_status = status_code` and fallback to `url_title: null`. |
| **EC-LINK-03** | **Missing URL Scheme / Protocol**<br>Input: `--link "lilianweng.github.io/posts/"` vs `https://...` | `requests.get()` fails with `MissingSchema` or `InvalidURL`. | **URL Normalization**: Inspect URL using `urllib.parse.urlparse`. If `scheme` (`http`/`https`) is missing, automatically prepend `https://` prior to validation and fetching. |
| **EC-LINK-04** | **Non-HTML Link Targets (`.pdf`, `.zip`, `.mp4`)**<br>Input: `--link "https://example.com/paper.pdf"` | `BeautifulSoup` attempts to parse raw binary PDF data as HTML, causing slow hangs or encoding crashes. | **Content-Type Pre-Check**: Inspect `response.headers.get('Content-Type', '')` after a `stream=True` or `HEAD` request. If `text/html` is absent, skip HTML parsing, extract filename from URL, and record `metadata.content_type: "application/pdf"`. |
| **EC-LINK-05** | **Massive Dynamic Query Strings & Session Tokens**<br>URLs $> 2048$ chars containing temporary tracking tokens (`?utm_source=...&token=xyz`). | Cluttered graph nodes and expired session links in `wiki/`. | **Canonical URL Preservation**: Store exact original URL in `content`. Optionally extract `<link rel="canonical" href="...">` if HTML parsing succeeds, storing it under `metadata.canonical_url`. |

---

### 1.3 Local Files (`FileHandler`)

| Edge Case ID | Scenario & Boundary Condition | Potential Impact | Engineering Mitigation & Handling Strategy |
| :--- | :--- | :--- | :--- |
| **EC-FILE-01** | **Non-Existent Path or Directory Target**<br>Command: `--file "C:/Downloads/ghost.pdf"` or `--file "C:/Windows"` | `FileNotFoundError` or `IsADirectoryError` during asset copy. | **Pre-Flight Validation**: Check `os.path.exists(path)` and `os.path.isfile(path)`. If false, abort immediately with clear terminal error: `[ERROR] Target file does not exist or is a directory: <path>`. |
| **EC-FILE-02** | **Filename Collisions & Special/Reserved Names**<br>Capturing two different `report.pdf` files over time; Windows reserved names (`CON.txt`, `AUX.doc`); paths with spaces. | Overwriting earlier `report.pdf` inside `raw/assets/`, causing permanent data loss for older captures. | **UUID-Prefixed Asset Names**: Always copy assets to `raw/assets/<uuid>_<sanitized_filename>`. Use `re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)` to sanitize special characters on Windows NTFS. |
| **EC-FILE-03** | **Zero-Byte / Empty Files**<br>Command: `--file "C:/temp/empty.txt"` where size is 0 bytes. | Downstream `classify.py` passes empty string to LLM, generating hallucinated summaries. | **Byte-Size Check**: Check `os.path.getsize(path)`. If `0`, warn user: `[WARNING] File size is 0 bytes.` Allow capture (to preserve archival record) but set `metadata.empty_file: true`. |
| **EC-FILE-04** | **File Locked by Another Process (Word/Excel/System)**<br>Capturing a `.docx` file currently open and locked by Microsoft Word (`PermissionError`). | `shutil.copy2()` fails with `PermissionError: [Errno 13] Permission denied`. | **Exception Handling & Retry Strategy**: Catch `PermissionError` during copy. Inform user clearly: `[ERROR] File is currently open or locked by another application. Please close the file and retry.` |
| **EC-FILE-05** | **Gigantic Files (Video / Archive / ISO Inputs)**<br>Command: `--file "D:/Backups/4K_Movie.mp4"` (4 GB). | Freezing terminal for several minutes during copy; exhausting local disk space in `raw/assets/`. | **Size Threshold Warning**: Check if `getsize() > 50_000_000` (50 MB). If true, prompt confirmation or emit warning: `[WARNING] Large file (X MB). Copying to raw/assets/ may take time and disk space.` Use chunked buffered copy (`shutil.copyfileobj(f_in, f_out, length=1024*1024)`). |

---

## 2. Filesystem & Storage Edge Cases (`raw/<uuid>.json`)

| Edge Case ID | Scenario & Boundary Condition | Potential Impact | Engineering Mitigation & Handling Strategy |
| :--- | :--- | :--- | :--- |
| **EC-STORE-01** | **Concurrent CLI Ingestions (Race Conditions)**<br>Two automated scripts or terminal tabs running `capture.py` at the exact same millisecond. | File corruption or ID collision if sequential IDs or timestamps were used for naming. | **Strict UUIDv4 Atomic Naming**: By naming every record `raw/<uuid.uuid4()>.json`, collision probability is $1 \text{ in } 2^{122}$ (mathematically zero). Each capture writes to an isolated file path without locks. |
| **EC-STORE-02** | **Disk Full / Out of Storage (`ENOSPC`)**<br>System runs out of hard drive space mid-way through writing the JSON file or copying a large asset. | Creation of half-written, corrupted `.json` files or incomplete `.pdf` files that break JSON parsers (`json.load`) in Week 2. | **Atomic Write via Temporary Files**: Write JSON data to `raw/.tmp_<uuid>.json` first. Once `file.flush()` and `file.close()` complete successfully, perform an atomic filesystem rename using `os.replace('.tmp_<uuid>.json', '<uuid>.json')`. |
| **EC-STORE-03** | **Cross-Platform Path Separators (`\` vs `/`)**<br>Windows storing `C:\path\to\file.pdf` in JSON metadata, which breaks if the repository is later run or inspected on Linux/macOS. | Broken asset links or `FileNotFoundError` when downstream Python scripts read `metadata.asset_path`. | **POSIX Normalization**: Always store relative asset paths using POSIX-style forward slashes inside JSON records: `asset_path: "raw/assets/<uuid>_file.pdf"` (`pathlib.Path(path).as_posix()`). |

---

## 3. Downstream Ripple & Integration Edge Cases (Weeks 2, 3, 4)

While Week 1 focuses on archival ingestion, capturing pristine data prevents the following downstream corner scenarios:

### 3.1 Week 2 (`classify.py` & `link.py`) Corner Scenarios
- **EC-DOWN-01 (LLM Hallucination / Malformed JSON API Return)**:
  - *Scenario*: Groq / Llama-3 returns conversational text (`"Here is your classification: ... {json}"`) instead of pure JSON, causing `json.loads()` to throw `JSONDecodeError` in `classify.py`.
  - *Mitigation*: Use regex JSON extraction (`re.search(r'\{.*\}', response, re.DOTALL)`) or strict JSON response formatting (`response_format={"type": "json_object"}`). If parsing still fails after 2 retries, fallback to default PARA categorization: `Category: Resources, Tags: ["unclassified"], status: "error"`.
- **EC-DOWN-02 (Token Window Overflow during Embedding Computation)**:
  - *Scenario*: A captured 100-page PDF document in `raw/assets/` exceeds the 384/512 token window of `all-MiniLM-L6-v2` during embedding generation in `link.py`.
  - *Mitigation*: In `link.py`, compute embeddings over the LLM-generated **summary** (from `classify.py`) plus the first 1000 characters of raw content, or apply sliding-window mean pooling across chunks.

### 3.2 Week 3 (`build_graph.py` & UI Rendering) Corner Scenarios
- **EC-DOWN-03 (Disconnected / Orphan Nodes & Graph Clutter)**:
  - *Scenario*: A captured note has no cosine similarity matches above threshold $\theta$ against existing notes, creating an isolated "floating" node in the Vis-Network visualization.
  - *Mitigation*: In `build_graph.py`, group orphan nodes under their PARA category node (`Project Cluster`, `Area Cluster`) with weak structural edges, ensuring every node is reachable and visually grounded.
- **EC-DOWN-04 (Graph Rendering Lag with $>1,000$ Nodes)**:
  - *Scenario*: Vis-Network force-directed physics simulation freezes the browser tab when node count exceeds 1,000.
  - *Mitigation*: Disable real-time physics once stabilization completes (`physics: { stabilization: { enabled: true, iterations: 150 } }`) or implement zoom/cluster-based pagination.

### 3.3 Week 4 (`ask.py` & Streamlit Deployment) Corner Scenarios
- **EC-DOWN-05 (Out-of-Scope Q&A Queries & Empty Retrieval)**:
  - *Scenario*: User asks `ask.py`: *"What is the weather in Tokyo today?"* when no captures exist about Tokyo weather.
  - *Mitigation*: Ensure the RAG system prompt mandates strict grounding: *"You must answer based ONLY on the provided retrieved notes. If the notes do not contain the answer, state clearly: 'I don't have information about this in your captured notes.'"*

---

## 4. Comprehensive Verification & Diagnostic Matrix

To verify that the capture engine successfully mitigates these edge cases, run the following diagnostic test suite using terminal commands:

| Edge Case ID | Diagnostic Test Command | Expected Terminal Output & Verification Status |
| :--- | :--- | :--- |
| **EC-NOTE-01** | `python capture.py --note "   "` | `[WARNING] Note content is empty. Nothing captured.` (Zero files created in `raw/`). |
| **EC-NOTE-02** | `python capture.py --note "Line 1\nLine 2 with \"quotes\" & 'apostrophes'"` | `[SUCCESS] Captured [NOTE] -> raw/<uuid>.json`. Inspect JSON: string must contain properly escaped `\n` and `\"`. |
| **EC-LINK-01** | *(Disable Wi-Fi)* $\rightarrow$ `python capture.py --link "https://example.com/test"` | `[SUCCESS] Captured [LINK] (Offline mode) -> raw/<uuid>.json`. JSON shows `url_title: null`, `url_status: "offline"`. |
| **EC-LINK-03** | `python capture.py --link "github.com"` | `[SUCCESS] Captured [LINK] -> raw/<uuid>.json`. JSON shows `content: "https://github.com"`. |
| **EC-FILE-01** | `python capture.py --file "C:/NonExistent/file.pdf"` | `[ERROR] Target file does not exist or is a directory: C:/NonExistent/file.pdf`. |
| **EC-FILE-02** | Create two `test.txt` files and capture both: `python capture.py --file "test.txt"` ($\times 2$) | Two distinct JSON records generated. `raw/assets/` contains `<uuid1>_test.txt` and `<uuid2>_test.txt` without collision. |
| **EC-STORE-02** | Diagnostic script check: verify all `raw/*.json` files have `status: "raw"` and valid JSON structure (`verify_capture.py`). | `[AUDIT PASS] 10/10 JSON records valid. No partial/corrupted `.tmp_` files found.` |
