# app.py

import os
import streamlit as st

from ingest import ingest_pdf

from search import search

from llm import generate_answer

from mongo import get_all_documents

from delete_document import delete_document



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
    "Upload PDF"
)


uploaded_file = st.sidebar.file_uploader(

    "Choose PDF",

    type=[
        "pdf"
    ]

)



if uploaded_file:


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



    if st.sidebar.button(
        "Process PDF"
    ):


        with st.spinner(
            "Processing PDF..."
        ):


            try:


                document_id = ingest_pdf(

                    pdf_path

                )


                st.session_state.document_id = document_id


                st.sidebar.success(

                    "PDF processed successfully"

                )


            except Exception as e:


                st.sidebar.error(

                    str(e)

                )



# ---------------------------------
# Manage Documents
# ---------------------------------

st.sidebar.divider()

st.sidebar.header(
    "Manage Documents"
)


chunks = get_all_documents()


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

            with st.spinner(
                "Deleting document..."
            ):

                try:

                    delete_document(
                        document_id
                    )

                    if st.session_state.document_id == document_id:

                        st.session_state.document_id = None

                    st.sidebar.success(
                        f"Deleted: {filename}"
                    )

                    st.rerun()

                except Exception as e:

                    st.sidebar.error(
                        str(e)
                    )



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


        with st.spinner(

            "Searching document..."

        ):


            try:


                # -------------------------
                # FAISS Retrieval
                # -------------------------

                results = search(

                    question,

                    top_k=5

                )



                if not results:


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



                    # -------------------------
                    # Generate answer
                    # -------------------------

                    answer = generate_answer(

                        question,

                        context

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


                st.error(

                    str(e)

                )