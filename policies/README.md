# Policy Library

Drop your P&P PDFs into this folder, then run from the project root:

    python ingest_policies.py

This extracts text from every PDF and writes `policies.json` at the project root.

The actual PDF files are gitignored (they may be large or proprietary).
`policies.json` is committed so the deployed app works without re-running ingestion.
