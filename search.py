# search.py

import os

import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

from mongo import get_document_by_id

from config import (
    EMBED_MODEL,
    FAISS_INDEX,
    TOP_K_RESULTS
)


# ---------------------------------
# Load Embedding Model
# ---------------------------------

model = SentenceTransformer(
    EMBED_MODEL
)

_index = None


def _load_index():
    global _index
    if _index is None:
        if not os.path.exists(FAISS_INDEX):
            raise FileNotFoundError(
                "FAISS index not found. "
                "Please upload a PDF first."
            )
        _index = faiss.read_index(FAISS_INDEX)
    return _index


def invalidate_index():
    global _index
    _index = None



# ---------------------------------
# Search Function
# ---------------------------------

def search(
        query,
        top_k=TOP_K_RESULTS
):
    """
    Search similar PDF chunks.

    Returns:
        List of matching documents
    """


    # -----------------------------
    # Convert question to vector
    # -----------------------------

    query_embedding = model.encode(
        query
    )


    query_vector = np.array(
        [query_embedding]
    ).astype(
        "float32"
    )


    # -----------------------------
    # FAISS Search
    # -----------------------------

    distances, ids = _load_index().search(
        query_vector,
        top_k
    )


    results = []


    # -----------------------------
    # Retrieve documents from MongoDB
    # -----------------------------

    for vector_id in ids[0]:


        # FAISS returns -1 when
        # no result exists

        if vector_id == -1:

            continue


        document = get_document_by_id(
            int(vector_id)
        )


        if document:


            results.append(

                {

                    "text":
                        document["text"],


                    "filename":
                        document.get(
                            "filename",
                            ""
                        ),


                    "page":
                        document.get(
                            "page",
                            0
                        ),


                    "chunk_number":
                        document.get(
                            "chunk_number",
                            0
                        ),


                    "score":
                        float(
                            distances[0][
                                len(results)
                            ]
                        )

                }

            )


    return results