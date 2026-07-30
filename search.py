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

        raise FileNotFoundError(
            "FAISS index not found. "
            "Please upload and process a PDF first."
        )


    index = faiss.read_index(
        FAISS_INDEX
    )


    return index



# ---------------------------------
# Search Function
# ---------------------------------

def search(
        query,
        top_k=TOP_K_RESULTS
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



    results = []



    # ---------------------------------
    # Retrieve MongoDB documents
    # ---------------------------------

    for position, vector_id in enumerate(ids[0]):


        # FAISS returns -1
        # if no result exists

        if vector_id == -1:

            continue



        document = get_document_by_id(

            int(vector_id)

        )



        if document:


            results.append(

                {

                    "vector_id":

                        document[
                            "vector_id"
                        ],


                    "document_id":

                        document[
                            "document_id"
                        ],


                    "filename":

                        document[
                            "filename"
                        ],


                    "page":

                        document[
                            "page"
                        ],


                    "chunk_number":

                        document[
                            "chunk_number"
                        ],


                    "text":

                        document[
                            "text"
                        ],


                    "score":

                        float(
                            distances[0][position]
                        )

                }

            )



    return results