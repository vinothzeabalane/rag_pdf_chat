# chunker.py

from config import CHUNK_OVERLAP
from logging_utils import configure_logger


logger = configure_logger(__name__)


def chunk_text(text, chunk_size):
    """Split text into overlapping word-count chunks."""

    words = text.split()

    logger.debug(
        "chunker:start words=%s chunk_size=%s overlap=%s",
        len(words),
        chunk_size,
        CHUNK_OVERLAP
    )

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        start += chunk_size - CHUNK_OVERLAP

    logger.debug(
        "chunker:done chunks=%s",
        len(chunks)
    )

    return chunks
