# pdf_reader.py

import fitz  # PyMuPDF


def extract_pdf(pdf_path):
    """Return list of {"page": int, "text": str} for each page."""

    doc = fitz.open(pdf_path)

    pages = []

    for page_num, page in enumerate(doc, start=1):

        text = page.get_text()

        if text.strip():

            pages.append(
                {
                    "page": page_num,
                    "text": text
                }
            )

    doc.close()

    return pages
