from pypdf import PdfReader


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    return "".join(page.extract_text() or "" for page in reader.pages)
