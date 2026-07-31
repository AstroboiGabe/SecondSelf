# Week 3 Execution Checklist: The Cartographer

## Phase 1: The Graph Builder (`build_graph.py`)
- `[x]` Create `build_graph.py` to scan the `wiki/` directory.
- `[x]` Implement parser to extract Title, PARA Category, Tags, and Summary from YAML frontmatter.
- `[x]` Implement Markdown link extractor to find all `[[Semantic Links]]` for edge mapping.
- `[x]` Export the node and edge structures into `graph_data.js` (to avoid local CORS issues).

## Phase 2: The Interactive Frontend (`index.html`)
- `[x]` Create `index.html` pulling in `vis-network` (Vis.js).
- `[x]` Implement a premium dark-mode, glassmorphism UI with modern typography (Inter).
- `[x]` Map PARA categories to distinct colors (Projects=Red/Pink, Areas=Blue, Resources=Green, Archives=Gray).
- `[x]` Implement hover tooltips to show the 1-sentence AI summaries dynamically.

## Phase 3: Final Verification
- `[x]` Run `build_graph.py` to generate the interactive knowledge graph from the existing 15 items.
- `[x]` Visually verify `index.html` structure and interactions.
