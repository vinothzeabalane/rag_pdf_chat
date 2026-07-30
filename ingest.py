# ingest.py

import os
import uuid
import hashlib

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
# Create FAISS directory
# ---------------------------------

os.makedirs(
    FAISS_INDEX_DIR,
    exist_ok=True
)



# ---------------------------------
# Calculate PDF hash
# ---------------------------------

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:

        while chunk := file.read(8192):

            sha256.update(
                chunk
            )


    return sha256.hexdigest()



# ---------------------------------
# Get next vector ID
# ---------------------------------

def get_next_vector_id():


    last_document = collection.find_one(
        sort=[
            (
                "vector_id",
                -1
            )
        ]
    )


    if last_document:

        return (
            last_document["vector_id"]
            +
            1
        )

    else:

        return 1



# ---------------------------------
# Load or create FAISS index
# ---------------------------------

def load_faiss_index(
        dimension=None
):


    if os.path.exists(
        FAISS_INDEX
    ):

        print(
            "Loading existing FAISS index"
        )


        return faiss.read_index(
            FAISS_INDEX
        )


    else:

        if dimension is None:

            raise Exception(
                "Dimension required for new FAISS index"
            )


        print(
            "Creating new FAISS index"
        )


        base_index = faiss.IndexFlatL2(
            dimension
        )


        return faiss.IndexIDMap(
            base_index
        )



# ---------------------------------
# Ingest PDF
# ---------------------------------

def ingest_pdf(
        pdf_path
):

    """
    Production PDF ingestion pipeline

    Steps:

    1. Calculate file hash
    2. Check duplicate
    3. Extract PDF
    4. Create chunks
    5. Generate embeddings
    6. Insert MongoDB
    7. Update FAISS index

    """



    # ---------------------------------
    # Check duplicate document
    # ---------------------------------

    file_hash = calculate_file_hash(
        pdf_path
    )


    existing = collection.find_one(
        {
            "file_hash": file_hash
        }
    )


    if existing:


        print(
            "Document already exists"
        )


        return existing[
            "document_id"
        ]



    # ---------------------------------
    # New document
    # ---------------------------------

    document_id = str(
        uuid.uuid4()
    )


    print(
        f"New document: {document_id}"
    )



    # ---------------------------------
    # Extract PDF
    # ---------------------------------

    pages = extract_pdf(
        pdf_path
    )


    if not pages:

        raise Exception(
            "PDF contains no text"
        )



    mongo_documents = []

    vectors = []

    vector_ids = []



    next_vector_id = get_next_vector_id()



    # ---------------------------------
    # Process chunks
    # ---------------------------------

    for page in pages:


        page_number = page["page"]

        text = page["text"]



        chunks = chunk_text(
            text,
            CHUNK_SIZE
        )



        for chunk_number, chunk in enumerate(chunks):


            if not chunk.strip():

                continue



            # -----------------------------
            # Generate embedding
            # -----------------------------

            embedding = model.encode(
                chunk
            )



            vectors.append(
                embedding
            )


            vector_ids.append(
                next_vector_id
            )



            # -----------------------------
            # MongoDB document
            # -----------------------------

            mongo_documents.append(

                {

                    "vector_id":
                        next_vector_id,


                    "document_id":
                        document_id,


                    "file_hash":
                        file_hash,


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


            next_vector_id += 1



    if not vectors:

        raise Exception(
            "No chunks generated"
        )



    # ---------------------------------
    # Insert MongoDB
    # ---------------------------------

    collection.insert_many(
        mongo_documents
    )


    print(
        f"Inserted {len(mongo_documents)} chunks"
    )



    # ---------------------------------
    # Update FAISS
    # ---------------------------------

    vectors_np = np.array(
        vectors
    ).astype(
        "float32"
    )


    dimension = vectors_np.shape[1]



    index = load_faiss_index(
        dimension
    )



    index.add_with_ids(

        vectors_np,

        np.array(
            vector_ids
        )

    )



    # ---------------------------------
    # Save FAISS
    # ---------------------------------

    faiss.write_index(
        index,
        FAISS_INDEX
    )


    print(
        "FAISS index updated"
    )


    return document_id