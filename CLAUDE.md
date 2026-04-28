# Readily Compliance

MVP healthcare compliance web app. A pre-loaded P&P library is audited against an uploaded regulatory document using Gemini, surfacing gaps and evidence.

## Tech Stack

- **Streamlit** — UI and app server
- **pypdf** — PDF text extraction
- **Google Generative AI Python SDK** — Gemini API calls for compliance analysis

## File Layout

```
app.py              # Streamlit entry point; page layout and routing only
pdf_utils.py        # PDF text extraction (pypdf)
llm.py              # Gemini API calls and prompt logic
ingest_policies.py  # One-time script: PDFs in policies/ → policies.json
policies/           # Pre-loaded P&P PDFs (gitignored) + README.md
policies.json       # Extracted text from all P&Ps; committed to repo
requirements.txt    # Python dependencies
.env                # API keys (not committed)
```

New modules are added only when a file exceeds ~150 lines or has a clearly distinct responsibility.

## Domain Notes

- The P&P library is pre-loaded, not uploaded per session. A healthcare org's library
  is a stable compliance source-of-truth; new regulatory checklists (e.g., DHCS All
  Plan Letters) arrive periodically and are audited against it.
- The regulatory document is the only per-session input.
- `ingest_policies.py` extracts text from PDFs in `policies/` and writes
  `policies.json`; run it once whenever the library changes.
- The app loads `policies.json` at startup via `@st.cache_resource`.

## Coding Conventions

- Small, single-purpose functions — each does one thing
- Type hints on all function signatures
- No premature abstraction — solve the concrete problem first
- No comments explaining what code does; only add one if the *why* is non-obvious
- No global mutable state; pass data explicitly
- Secrets via `os.getenv`, never hardcoded
