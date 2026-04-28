# Readily Compliance

A healthcare compliance web app that audits a regulatory document against a pre-loaded library of Policies & Procedures (P&Ps). Upload a regulatory checklist (e.g., a DHCS All Plan Letter), and the app extracts each requirement, searches the P&P library for evidence, and returns a ✅/❌ result with a verbatim quote and source document for every line item.

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY
```

Drop your P&P PDFs into `policies/`, then ingest them once:

```bash
python ingest_policies.py
```

Then start the app:

```bash
streamlit run app.py
```

## Architecture

The P&P library is pre-loaded at startup from `policies.json` — a flat JSON file mapping filename → extracted text, produced by `ingest_policies.py`. Re-run the ingest script whenever the library changes and commit the updated `policies.json`. The actual PDFs are gitignored.

Each compliance check sends one LLM call per extracted requirement, with the full concatenated policy library as context. Results are cached per session via `@st.cache_data`.

## Production notes

The full-context concatenation approach works well for libraries up to a few hundred pages. At scale (thousands of documents), this would be replaced with a vector database (e.g., pgvector or Pinecone) and semantic retrieval — fetching only the top-k most relevant policy chunks per requirement before calling the LLM.
