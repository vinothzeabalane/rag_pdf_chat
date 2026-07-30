# delete_document.py


import os

import faiss
import numpy as np


from mongo import collection

from config import FAISS_INDEX



# ---------------------------------
# Load FAISS index
# ---------------------------------

def load_index():

    if not os.path.exists(
        FAISS_INDEX
    ):

        raise FileNotFoundError(
            "FAISS index not found"
        )


    return faiss.read_index(
        FAISS_INDEX
    )



# ---------------------------------
# Delete document
# ---------------------------------

def delete_document(
        document_id
):

    """
    Delete complete PDF from:

    1. MongoDB
    2. FAISS index

    """



    # ---------------------------------
    # Find vectors belonging to PDF
    # ---------------------------------

    documents = list(

        collection.find(

            {
                "document_id":
                    document_id
            },

            {
                "vector_id":1,
                "_id":0
            }

        )

    )



    if not documents:


        print(
            "Document not found"
        )

        return False



    vector_ids = [

        doc["vector_id"]

        for doc in documents

    ]



    print(

        f"Deleting {len(vector_ids)} vectors"

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



    print(

        f"Removed {removed} vectors from FAISS"

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

            "document_id":

                document_id

        }

    )



    print(

        f"Removed {result.deleted_count} MongoDB records"

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