from typing import List

import fitz  # PyMuPDF


def read_pdf(buf: bytes) -> List[str]:
    """Return plain text for each page of the PDF buffer."""
    doc = fitz.open(stream=buf, filetype="pdf")
    pages: List[str] = []
    for page in doc:
        text = page.get_text("text")
        pages.append(text)
    return pages
