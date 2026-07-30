# ingest.py

import os
import uuid

import numpy as np
import faiss

from sentence_transformers import SentenceTransformer

from mongo import collection

from pdf_reader import extract_pdf

from chunker import chunk_text

from config import (
    EMBED_MODEL,
    FAISS_INDEX,
    FAISS_INDEX_DIR,
    CHUNK_SIZE
)


# ---------------------------------
# Load embedding model
# ---------------------------------

model = SentenceTransformer(
    EMBED_MODEL
)


# ---------------------------------
# Create index directory
# ---------------------------------

os.makedirs(
    FAISS_INDEX_DIR,
    exist_ok=True
)


# ---------------------------------
# Ingest PDF
# ---------------------------------

def ingest_pdf(pdf_path):

    """
    Process PDF:
    - Extract text
    - Create chunks
    - Generate embeddings
    - Store in MongoDB
    - Create FAISS index

    Returns:
        document_id
    """


    # Unique ID for uploaded PDF

    document_id = str(
        uuid.uuid4()
    )


    print(
        f"Processing document: {document_id}"
    )


    # ---------------------------------
    # Extract PDF pages
    # ---------------------------------

    pages = extract_pdf(
        pdf_path
    )


    mongo_documents = []

    vectors = []

    vector_ids = []


    vector_id = 1



    # ---------------------------------
    # Process each page
    # ---------------------------------

    for page in pages:


        page_number = page["page"]

        text = page["text"]


        # Split page into chunks

        chunks = chunk_text(
            text,
            CHUNK_SIZE
        )


        for chunk_number, chunk in enumerate(chunks):


            if not chunk.strip():

                continue


            # ---------------------------------
            # Create embedding
            # ---------------------------------

            embedding = model.encode(
                chunk
            )


            vectors.append(
                embedding
            )


            vector_ids.append(
                vector_id
            )


            # ---------------------------------
            # MongoDB document
            # ---------------------------------

            mongo_documents.append(
                {

                    "vector_id": vector_id,


                    "document_id": document_id,


                    "filename":
                        os.path.basename(
                            pdf_path
                        ),


                    "page":
                        page_number,


                    "chunk_number":
                        chunk_number,


                    "text":
                        chunk,


                    "embedding":
                        embedding.tolist()

                }
            )


            vector_id += 1



    # ---------------------------------
    # Store data in MongoDB
    # ---------------------------------

    if mongo_documents:

        collection.delete_many({})

        collection.insert_many(
            mongo_documents
        )


    print(
        f"Inserted {len(mongo_documents)} chunks into MongoDB"
    )



    # ---------------------------------
    # Create FAISS index
    # ---------------------------------

    vectors = np.array(
        vectors
    ).astype(
        "float32"
    )


    dimension = vectors.shape[1]


    # L2 distance similarity search

    base_index = faiss.IndexFlatL2(
        dimension
    )


    # Map vector ID -> MongoDB document ID

    index = faiss.IndexIDMap(
        base_index
    )


    index.add_with_ids(

        vectors,

        np.array(
            vector_ids
        )

    )


    # Save index

    faiss.write_index(
        index,
        FAISS_INDEX
    )


    print(
        "FAISS index created"
    )


    return document_id