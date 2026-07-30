# app.py

import os
import streamlit as st

from ingest import ingest_pdf
from search import search, invalidate_index
from llm import ask_llm


# -----------------------------
# Configuration
# -----------------------------

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# -----------------------------
# Streamlit Page Configuration
# -----------------------------

st.set_page_config(
    page_title="PDF RAG Chat",
    page_icon="📄",
    layout="wide"
)


st.title("📄 PDF RAG Chat Assistant")

st.write(
    "Upload any PDF and ask questions related to its content."
)


# -----------------------------
# Session State
# -----------------------------

if "processed" not in st.session_state:

    st.session_state.processed = False


if "document_name" not in st.session_state:

    st.session_state.document_name = ""


# -----------------------------
# PDF Upload Section
# -----------------------------

uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=["pdf"]
)


if uploaded_file:


    file_path = os.path.join(
        UPLOAD_DIR,
        uploaded_file.name
    )


    # Save uploaded PDF

    with open(file_path, "wb") as f:

        f.write(
            uploaded_file.getbuffer()
        )


    st.success(
        f"Uploaded: {uploaded_file.name}"
    )


    # -----------------------------
    # Process PDF
    # -----------------------------

    if st.button(
        "Process PDF"
    ):


        with st.spinner(
            "Extracting text and creating embeddings..."
        ):


            document_id = ingest_pdf(
                file_path
            )

            invalidate_index()


            st.session_state.processed = True

            st.session_state.document_name = (
                uploaded_file.name
            )


            st.session_state.document_id = (
                document_id
            )


        st.success(
            "PDF processed successfully!"
        )



# -----------------------------
# Question Section
# -----------------------------

st.divider()


if st.session_state.processed:


    st.subheader(
        f"Ask questions about: {st.session_state.document_name}"
    )


    question = st.text_input(
        "Enter your question"
    )


    if st.button(
        "Ask"
    ):


        if question.strip():


            with st.spinner(
                "Searching document..."
            ):


                # -----------------------------
                # Vector Search
                # -----------------------------

                results = search(
                    question,
                    top_k=5
                )


                context = "\n\n".join(
                    r["text"] for r in results
                )


                # -----------------------------
                # LLM Answer
                # -----------------------------

                answer = ask_llm(
                    question,
                    context
                )


            st.subheader(
                "Answer"
            )


            st.write(
                answer
            )


            # -----------------------------
            # Show Retrieved Context
            # -----------------------------

            with st.expander(
                "Show retrieved document chunks"
            ):

                for i, chunk in enumerate(results):

                    st.markdown(
                        f"**Chunk {i+1}:**"
                    )

                    st.write(
                        chunk
                    )


        else:

            st.warning(
                "Please enter a question."
            )


else:

    st.info(
        "Please upload and process a PDF first."
    )