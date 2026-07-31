# pdf_reader.py

import fitz  # PyMuPDF

from logging_utils import configure_logger


logger = configure_logger(__name__)


def extract_pdf(pdf_path):
    """Return list of {"page": int, "text": str} for each page."""

    logger.info(
        "pdf_reader:start path=%s",
        pdf_path
    )

    doc = fitz.open(pdf_path)

    pages = []

    total_pages = len(doc)

    for page_num, page in enumerate(doc, start=1):

        text = page.get_text()

        if text.strip():

            pages.append(
                {
                    "page": page_num,
                    "text": text
                }
            )

        else:
            logger.debug(
                "pdf_reader:empty-page page=%s",
                page_num
            )

    doc.close()

    logger.info(
        "pdf_reader:done total_pages=%s text_pages=%s",
        total_pages,
        len(pages)
    )

    return pages
