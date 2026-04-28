import json
from pathlib import Path

from pdf_utils import extract_pdf_text

POLICIES_DIR = Path("policies")
OUTPUT = Path("policies.json")


def main() -> None:
    pdfs = sorted(POLICIES_DIR.rglob("*.pdf"))
    if not pdfs:
        print("No PDFs found in policies/")
        return

    library: dict[str, str] = {}
    for pdf in pdfs:
        key = str(pdf.relative_to(POLICIES_DIR))
        with pdf.open("rb") as f:
            text = extract_pdf_text(f)
        library[key] = text
        print(f"  {key}: {len(text):,} chars")

    OUTPUT.write_text(json.dumps(library, indent=2))
    total = sum(len(v) for v in library.values())
    print(f"\nWrote {len(library)} documents, {total:,} total chars → {OUTPUT}")


if __name__ == "__main__":
    main()
