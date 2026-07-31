# search.py

import os
import time

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

from mongo import get_document_by_id

from config import (
    EMBED_MODEL,
    FAISS_INDEX,
    TOP_K_RESULTS
)

from logging_utils import configure_logger, set_request_id, get_request_id


logger = configure_logger(__name__)


# ---------------------------------
# Load Embedding Model
# ---------------------------------

model = SentenceTransformer(
    EMBED_MODEL
)


# ---------------------------------
# Load FAISS Index
# ---------------------------------

def load_faiss_index():

    """
    Load existing FAISS index
    """

    if not os.path.exists(
        FAISS_INDEX
    ):

        logger.error(
            "search:faiss-missing path=%s",
            FAISS_INDEX
        )

        raise FileNotFoundError(
            "FAISS index not found. "
            "Please upload and process a PDF first."
        )


    index = faiss.read_index(
        FAISS_INDEX
    )

    logger.debug(
        "search:faiss-loaded path=%s ntotal=%s",
        FAISS_INDEX,
        index.ntotal
    )

    return index


# ---------------------------------
# Search Function
# ---------------------------------

def search(
        query,
    top_k=TOP_K_RESULTS,
    request_id=None
):

    """
    Search relevant document chunks.

    Returns:

    [
        {
            text,
            filename,
            page,
            chunk_number,
            score
        }
    ]

    """

    start_time = time.perf_counter()

    if request_id:
        set_request_id(request_id)

    logger.info(
        "search:start request_id=%s query_chars=%s top_k=%s",
        get_request_id(),
        len(query),
        top_k
    )

    # ---------------------------------
    # Load FAISS
    # ---------------------------------

    index = load_faiss_index()

    # ---------------------------------
    # Convert question to embedding
    # ---------------------------------

    query_embedding = model.encode(
        query
    )

    query_vector = np.array(
        [
            query_embedding
        ]
    ).astype(
        "float32"
    )

    # ---------------------------------
    # FAISS similarity search
    # ---------------------------------

    distances, ids = index.search(
        query_vector,
        top_k
    )

    logger.debug(
        "search:faiss-returned ids=%s",
        ids[0].tolist() if len(ids) > 0 else []
    )

    results = []

    # ---------------------------------
    # Retrieve MongoDB documents
    # ---------------------------------

    for position, vector_id in enumerate(ids[0]):

        # FAISS returns -1
        # if no result exists
        if vector_id == -1:
            logger.debug(
                "search:skip-empty-slot position=%s",
                position
            )
            continue

        document = get_document_by_id(
            int(vector_id)
        )

        if document:
            results.append(
                {
                    "vector_id": document["vector_id"],
                    "document_id": document["document_id"],
                    "filename": document["filename"],
                    "page": document["page"],
                    "chunk_number": document["chunk_number"],
                    "text": document["text"],
                    "score": float(distances[0][position])
                }
            )
        else:
            logger.warning(
                "search:mongo-miss vector_id=%s",
                int(vector_id)
            )

    logger.info(
        "search:done results=%s elapsed=%.3fs",
        len(results),
        time.perf_counter() - start_time
    )

    return results
