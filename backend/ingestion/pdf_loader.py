"""
Extracts text from PDF files, page by page, so each chunk can carry an accurate
page number in its metadata (needed for citations like "Handbook.pdf, p.12").
"""
from pypdf import PdfReader


def load_pdf(path):
    """Returns a list of (page_number, page_text) tuples, skipping blank pages."""
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))
    return pages
