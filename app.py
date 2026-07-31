# app.py

import os
import time
import streamlit as st

from ingest import ingest_pdf

from search import search

from llm import generate_answer

from mongo import get_all_documents

from delete_document import delete_document

from logging_utils import (
    configure_logger,
    start_request_id,
    clear_request_id,
    get_request_id,
    set_debug_enabled,
    is_debug_enabled
)


logger = configure_logger(__name__)



# ---------------------------------
# Streamlit Configuration
# ---------------------------------

st.set_page_config(

    page_title="PDF RAG Chat",

    page_icon="📄",

    layout="wide"

)



# ---------------------------------
# Title
# ---------------------------------

st.title(
    "📄 PDF RAG Chat using FAISS + MongoDB + Ollama"
)



st.write(
    """
Upload a PDF document and ask questions.
The system will retrieve relevant sections
using FAISS and generate answers using Ollama.
"""
)



# ---------------------------------
# Session State
# ---------------------------------

if "document_id" not in st.session_state:

    st.session_state.document_id = None



# ---------------------------------
# PDF Upload
# ---------------------------------

st.sidebar.header(
    "Logging"
)

debug_enabled = st.sidebar.checkbox(
    "Enable debug logs",
    value=is_debug_enabled(),
    help="Enable verbose backend logs for troubleshooting."
)

set_debug_enabled(debug_enabled)

logger.info(
    "logging:mode debug_enabled=%s",
    debug_enabled
)

st.sidebar.header(
    "Upload PDF"
)


uploaded_file = st.sidebar.file_uploader(

    "Choose PDF",

    type=[
        "pdf"
    ]

)



if uploaded_file:

    logger.debug(
        "upload:selected filename=%s size_bytes=%s",
        uploaded_file.name,
        uploaded_file.size
    )


    upload_dir = "uploads"


    os.makedirs(

        upload_dir,

        exist_ok=True

    )


    pdf_path = os.path.join(

        upload_dir,

        uploaded_file.name

    )



    # Save uploaded PDF

    with open(

        pdf_path,

        "wb"

    ) as file:


        file.write(

            uploaded_file.getbuffer()

        )

    logger.debug(
        "upload:saved path=%s",
        pdf_path
    )



    if st.sidebar.button(
        "Process PDF"
    ):

        process_start = time.perf_counter()
        request_id = start_request_id("process")

        logger.info(
            "process:start request_id=%s filename=%s",
            request_id,
            uploaded_file.name
        )


        with st.spinner(
            "Processing PDF..."
        ):


            try:


                document_id = ingest_pdf(
                    pdf_path,
                    request_id=request_id
                )


                st.session_state.document_id = document_id

                logger.info(
                    "process:done document_id=%s elapsed=%.3fs",
                    document_id,
                    time.perf_counter() - process_start
                )


                st.sidebar.success(

                    "PDF processed successfully"

                )


            except Exception as e:

                logger.exception(
                    "process:error request_id=%s filename=%s error=%s",
                    get_request_id(),
                    uploaded_file.name,
                    str(e)
                )


                st.sidebar.error(

                    str(e)

                )

            finally:
                clear_request_id()



# ---------------------------------
# Manage Documents
# ---------------------------------

st.sidebar.divider()

st.sidebar.header(
    "Manage Documents"
)


chunks = get_all_documents()

logger.debug(
    "documents:loaded chunk_records=%s",
    len(chunks)
)


# Deduplicate chunks down to one entry per PDF

uploaded_documents = {
    chunk["document_id"]: chunk["filename"]
    for chunk in chunks
}


if not uploaded_documents:

    st.sidebar.info(
        "No documents uploaded yet"
    )

else:

    for document_id, filename in uploaded_documents.items():

        col1, col2 = st.sidebar.columns(
            [3, 1]
        )

        col1.write(
            filename
        )

        if col2.button(
            "🗑️",
            key=f"delete_{document_id}"
        ):

            request_id = start_request_id("delete")

            logger.info(
                "delete:start request_id=%s document_id=%s filename=%s",
                request_id,
                document_id,
                filename
            )

            with st.spinner(
                "Deleting document..."
            ):

                try:

                    delete_document(
                        document_id,
                        request_id=request_id
                    )

                    if st.session_state.document_id == document_id:

                        st.session_state.document_id = None

                    st.sidebar.success(
                        f"Deleted: {filename}"
                    )

                    logger.info(
                        "delete:done document_id=%s",
                        document_id
                    )

                    st.rerun()

                except Exception as e:

                    logger.exception(
                        "delete:error request_id=%s document_id=%s error=%s",
                        get_request_id(),
                        document_id,
                        str(e)
                    )

                    st.sidebar.error(
                        str(e)
                    )

                finally:
                    clear_request_id()



# ---------------------------------
# Question Section
# ---------------------------------

st.divider()



question = st.text_input(

    "Ask a question about your PDF"

)



if st.button(
    "Ask"
):


    if not question:


        st.warning(

            "Please enter a question"

        )


    else:

        request_id = start_request_id("ask")

        logger.info(
            "ask:start request_id=%s question_chars=%s",
            request_id,
            len(question)
        )


        with st.spinner(

            "Searching document..."

        ):


            try:


                # -------------------------
                # FAISS Retrieval
                # -------------------------

                results = search(

                    question,

                    top_k=5,
                    request_id=request_id

                )

                logger.info(
                    "ask:retrieval request_id=%s results=%s",
                    get_request_id(),
                    len(results)
                )



                if not results:

                    logger.warning(
                        "ask:no-results request_id=%s question_chars=%s",
                        get_request_id(),
                        len(question)
                    )


                    st.warning(

                        "No relevant information found"

                    )


                else:


                    # -------------------------
                    # Prepare context
                    # -------------------------

                    context = "\n\n".join(

                        [

                            result["text"]

                            for result in results

                        ]

                    )

                    logger.debug(
                        "ask:context-built request_id=%s chars=%s",
                        get_request_id(),
                        len(context)
                    )



                    # -------------------------
                    # Generate answer
                    # -------------------------

                    answer = generate_answer(

                        question,

                        context,

                        request_id=request_id

                    )

                    logger.info(
                        "ask:answer-generated request_id=%s chars=%s",
                        get_request_id(),
                        len(answer)
                    )



                    st.subheader(

                        "Answer"

                    )


                    st.write(

                        answer

                    )

                    # -------------------------
                    # Show sources
                    # -------------------------

                    st.subheader(
                        "Sources"
                    )

                    for result in results:

                        with st.expander(
                            f"{result['filename']} - Page {result['page']}"
                        ):

                            st.write(
                                result["text"]
                            )

                            st.write(
                                "Score:",
                                result["score"]
                            )

            except Exception as e:

                logger.exception(
                    "ask:error request_id=%s error=%s",
                    get_request_id(),
                    str(e)
                )

                st.error(
                    str(e)
                )

            finally:
                clear_request_id()