# delete_document.py

import os
import time

import faiss
import numpy as np

from database.mongo import collection

from config import FAISS_INDEX

from logging_utils import configure_logger, set_request_id, get_request_id


logger = configure_logger(__name__)


# ---------------------------------
# Load FAISS index
# ---------------------------------

def load_index():

    if not os.path.exists(
        FAISS_INDEX
    ):

        logger.error(
            "delete:faiss-missing path=%s",
            FAISS_INDEX
        )

        raise FileNotFoundError(
            "FAISS index not found"
        )

    logger.debug(
        "delete:faiss-loading path=%s",
        FAISS_INDEX
    )

    return faiss.read_index(
        FAISS_INDEX
    )


# ---------------------------------
# Delete document
# ---------------------------------

def delete_document(
    document_id,
    request_id=None
):

    """
    Delete complete PDF from:

    1. MongoDB
    2. FAISS index

    """

    start_time = time.perf_counter()

    if request_id:
        set_request_id(request_id)

    logger.info(
        "delete:start request_id=%s document_id=%s",
        get_request_id(),
        document_id
    )

    # ---------------------------------
    # Find vectors belonging to PDF
    # ---------------------------------

    documents = list(
        collection.find(
            {
                "document_id": document_id
            },
            {
                "vector_id": 1,
                "_id": 0
            }
        )
    )

    if not documents:

        logger.warning(
            "delete:not-found document_id=%s",
            document_id
        )

        return False

    vector_ids = [
        doc["vector_id"]
        for doc in documents
    ]

    logger.info(
        "delete:vectors-found document_id=%s count=%s",
        document_id,
        len(vector_ids)
    )

    # ---------------------------------
    # Remove from FAISS
    # ---------------------------------

    index = load_index()

    remove_ids = np.array(
        vector_ids
    ).astype(
        "int64"
    )

    removed = index.remove_ids(
        remove_ids
    )

    logger.info(
        "delete:faiss-removed document_id=%s removed=%s",
        document_id,
        removed
    )

    # ---------------------------------
    # Save FAISS
    # ---------------------------------

    faiss.write_index(
        index,
        FAISS_INDEX
    )

    # ---------------------------------
    # Remove MongoDB documents
    # ---------------------------------

    result = collection.delete_many(
        {
            "document_id": document_id
        }
    )

    logger.info(
        "delete:mongo-removed document_id=%s deleted=%s",
        document_id,
        result.deleted_count
    )

    logger.info(
        "delete:done document_id=%s elapsed=%.3fs",
        document_id,
        time.perf_counter() - start_time
    )

    return True


# ---------------------------------
# Example usage
# ---------------------------------

if __name__ == "__main__":

    document_id = input(
        "Enter document ID: "
    )

    delete_document(
        document_id
    )
