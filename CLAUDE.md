# Readily Compliance

MVP healthcare compliance web app. Accepts policy/procedure documents, analyzes them against regulatory frameworks using Gemini, and surfaces gaps or risks.

## Tech Stack

- **Streamlit** — UI and app server
- **pypdf** — PDF text extraction
- **Google Generative AI Python SDK** — Gemini API calls for compliance analysis

## File Layout

```
app.py              # Streamlit entry point; page layout and routing only
extractor.py        # PDF text extraction (pypdf)
analyzer.py         # Gemini API calls and prompt logic
requirements.txt    # Python dependencies
.env                # API keys (not committed)
```

New modules are added only when a file exceeds ~150 lines or has a clearly distinct responsibility.

## Coding Conventions

- Small, single-purpose functions — each does one thing
- Type hints on all function signatures
- No premature abstraction — solve the concrete problem first
- No comments explaining what code does; only add one if the *why* is non-obvious
- No global mutable state; pass data explicitly
- Secrets via `os.getenv`, never hardcoded
