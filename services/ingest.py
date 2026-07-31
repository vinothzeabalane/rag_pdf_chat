# ingest.py

import os
import uuid
import hashlib
import time

import numpy as np
import faiss

from database.mongo import collection

from pdf_reader import extract_pdf

from chunker import chunk_text

from models.embedding import get_embedding_model

from config import (
    FAISS_INDEX,
    FAISS_INDEX_DIR,
    CHUNK_SIZE
)

from logging_utils import configure_logger, set_request_id, get_request_id


logger = configure_logger(__name__)


# ---------------------------------
# Load embedding model
# ---------------------------------

model = get_embedding_model()


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

        logger.debug(
            "load_faiss_index: loading existing index from %s",
            FAISS_INDEX
        )


        return faiss.read_index(
            FAISS_INDEX
        )


    else:

        if dimension is None:

            raise Exception(
                "Dimension required for new FAISS index"
            )


        logger.debug(
            "load_faiss_index: creating new index with dimension=%s",
            dimension
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
    pdf_path,
    request_id=None
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

    start_time = time.perf_counter()

    if request_id:
        set_request_id(request_id)

    logger.info(
        "ingest_pdf:start request_id=%s path=%s",
        get_request_id(),
        pdf_path
    )

    if not os.path.exists(pdf_path):
        logger.error(
            "ingest_pdf:file-not-found path=%s",
            pdf_path
        )
        raise FileNotFoundError(
            f"File not found: {pdf_path}"
        )



    # ---------------------------------
    # Check duplicate document
    # ---------------------------------

    file_hash = calculate_file_hash(
        pdf_path
    )

    logger.debug(
        "ingest_pdf:file-hash calculated hash=%s",
        file_hash
    )


    existing = collection.find_one(
        {
            "file_hash": file_hash
        }
    )


    if existing:

        logger.info(
            "ingest_pdf:duplicate document_id=%s filename=%s",
            existing.get("document_id"),
            existing.get("filename")
        )

        logger.info(
            "ingest_pdf:done duplicate-skip elapsed=%.3fs",
            time.perf_counter() - start_time
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

    logger.info(
        "ingest_pdf:new-document document_id=%s",
        document_id
    )



    # ---------------------------------
    # Extract PDF
    # ---------------------------------

    pages = extract_pdf(
        pdf_path
    )

    logger.debug(
        "ingest_pdf:extract-pdf pages=%s",
        len(pages) if pages else 0
    )


    if not pages:

        logger.error(
            "ingest_pdf:empty-pdf path=%s",
            pdf_path
        )

        raise Exception(
            "PDF contains no text"
        )



    mongo_documents = []

    vectors = []

    vector_ids = []



    next_vector_id = get_next_vector_id()

    logger.debug(
        "ingest_pdf:vector-id-start next_vector_id=%s",
        next_vector_id
    )

    processed_pages = 0
    total_chunks = 0



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

        logger.debug(
            "ingest_pdf:page-chunked page=%s chunks=%s",
            page_number,
            len(chunks)
        )

        processed_pages += 1



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

            total_chunks += 1



    if not vectors:

        logger.error(
            "ingest_pdf:no-chunks-generated document_id=%s pages=%s",
            document_id,
            processed_pages
        )

        raise Exception(
            "No chunks generated"
        )



    # ---------------------------------
    # Insert MongoDB
    # ---------------------------------

    collection.insert_many(
        mongo_documents
    )

    logger.info(
        "ingest_pdf:mongo-inserted document_id=%s records=%s",
        document_id,
        len(mongo_documents)
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

    logger.info(
        "ingest_pdf:faiss-add document_id=%s vectors=%s dimension=%s",
        document_id,
        len(vector_ids),
        dimension
    )



    # ---------------------------------
    # Save FAISS
    # ---------------------------------

    faiss.write_index(
        index,
        FAISS_INDEX
    )

    logger.info(
        "ingest_pdf:faiss-saved path=%s",
        FAISS_INDEX
    )

    logger.info(
        "ingest_pdf:done document_id=%s pages=%s chunks=%s elapsed=%.3fs",
        document_id,
        processed_pages,
        total_chunks,
        time.perf_counter() - start_time
    )


    return document_id