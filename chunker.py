# chunker.py

from config import CHUNK_OVERLAP


def chunk_text(text, chunk_size):
    """Split text into overlapping word-count chunks."""

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        start += chunk_size - CHUNK_OVERLAP

    return chunks
