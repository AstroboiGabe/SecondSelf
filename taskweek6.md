# Week 6 Execution Checklist: Frontend Command Center

## Phase 1: Dependencies & Prep
- `[x]` Add `psutil` to `requirements.txt`.
- `[x]` Install `psutil` via pip.

## Phase 2: App Refactoring (`app.py`)
- `[x]` Move the Cartographer Graph to the main view under the chat.
- `[x]` Implement "Capture Quick Note" UI and connect to `capture.py`.
- `[x]` Implement "Pipeline" UI with "force re-process" checkbox.
- `[x]` Connect Pipeline button to `classify.py`, `link.py`, and `build_graph.py`.
- `[x]` Implement memory/disk storage diagnostics using `psutil`/`shutil`.

## Phase 3: Validation
- `[ ]` Verify local Streamlit restart handles the layout properly.
- `[ ]` Verify the capture and pipeline buttons work flawlessly.
