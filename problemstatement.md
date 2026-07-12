# Week 1 Problem Statement — The Archivist: "Capture Everything, Lose Nothing"

## 1. Executive Summary & Overarching Context

### The Core Problem
Every notes app fails the same way: you capture hundreds of notes, bookmarks, PDFs, and ideas — and then you never find them again. Information goes in, but nothing comes back out. Notes sit in folders nobody re-reads. Bookmarks pile up unread. Knowledge doesn't compound.

### The Overarching Goal: SecondSelf
Build an end-to-end system where you can capture anything (a note, a link, a file), have AI automatically classify and file it, auto-link it to related knowledge, render it as a live interactive graph you can explore, and — most importantly — ask it any question in plain English and get an answer synthesized from your own accumulated knowledge. Then deploy it to a public URL anyone can open.

**Not a notes app. Not a chatbot. A brain that organizes itself and answers for you.**

---

## 2. The Final System Pipeline (4-Week Roadmap)

```
Capture any note/link/file
           ↓
AI classifies & files it (PARA method)
           ↓
AI auto-links it to related notes (embeddings)
           ↓
Everything renders as a live, interactive, hoverable graph
           ↓
Ask it anything in plain English → answer pulled from YOUR notes
           ↓
Deployed on a public URL anyone can open
```

Each week is a self-contained problem. You will build it, test it on **real data** (your own notes — not test data), and each week's output becomes the next week's input.

---

## 3. Week 1 Problem Statement — The Archivist

### The Problem
You have no single place to put things. Ideas, links, and files scatter across different applications, browser tabs, local folders, and your memory. Without a reliable, frictionless capture system, valuable information is lost at the point of entry before it can ever be organized.

### The Objective
Build the foundation of the **SecondSelf** brain: a single, unified capture pipeline where one command saves **anything** (a quick thought, a web link, or a document file) into a structured local repository with unique tracking metadata.

---

## 4. Technical Build Requirements

### 1. Project Structure Setup
Set up the initial project workspace from scratch with two core directories:
- **`raw/`**: The immutable ingestion zone where every raw capture lands.
- **`wiki/`**: The structured repository (used starting in Week 2 for organized, linked notes).

### 2. Capture Script (`capture.py`)
Write a Python command-line script capable of taking any note, link, or file path and saving it into the `raw/` directory. Each captured entry must automatically generate and store:
- **A Timestamp**: Standardized date and time of capture (e.g., ISO 8601 format).
- **A Unique ID**: A distinct identifier (`UUID` or hash-based ID) to ensure no collisions.
- **The Raw Content**: The actual text, URL, or file contents/reference along with metadata distinguishing the capture type (`note`, `link`, or `file`).

### 3. Real Data Testing
Run the capture tool against your own scattered information. You must ingest at least **10+ real pieces of personal knowledge** (actual notes, real bookmarks, or real documents you use), rather than dummy or placeholder test data.

---

## 5. Deliverables ("Ship the Capture Pipeline")

1. **A Working Capture Script (`capture.py`)**: One unified command that saves anything (`note`, `link`, `file`) directly to `raw/` with a timestamp and unique ID.
2. **Populated `raw/` Directory**: Contains **10+ real captured items** from your actual digital life.
3. **🏅 Badge Earned**: **The Archivist**

---

## 6. Acceptance Criteria

- [ ] `raw/` and `wiki/` folder structure exists.
- [ ] One command (`capture.py`) can successfully capture a **note**, a **link**, AND a **file**.
- [ ] Every captured item in `raw/` has a **timestamp** and a **unique ID**.
- [ ] **10+ real items** are captured and stored in the `raw/` directory.

---

## 7. Suggested Repository Structure for Week 1

```
secondself/
├── raw/                # Week 1: Raw captures (timestamp + unique ID)
├── wiki/               # Week 2: Classified + auto-linked notes
├── capture.py          # Week 1: One-command capture script
├── requirements.txt    # Project dependencies
└── README.md           # Documentation & setup instructions
```

---

## 8. Looking Ahead: Why This Matters for Week 2
In **Week 2 (The Librarian)**, every raw capture you store in `raw/` this week will be read automatically by an LLM to assign **PARA categories (Projects, Areas, Resources, Archives)**, generate summaries, and compute vector embeddings for automatic cross-note linking. Building a clean, reliable capture pipeline with rich metadata today ensures your AI has pristine data to organize tomorrow.
