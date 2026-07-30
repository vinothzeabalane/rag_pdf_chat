# mongo.py

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from config import (
    MONGO_URL,
    DB_NAME,
    COLLECTION_NAME
)


# ---------------------------------
# Create MongoDB Client
# ---------------------------------

try:

    client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=5000
    )


    # Test connection

    client.admin.command(
        "ping"
    )


    print(
        "MongoDB connected successfully"
    )


except ConnectionFailure as e:

    print(
        f"MongoDB connection failed: {e}"
    )

    raise



# ---------------------------------
# Database
# ---------------------------------

db = client[
    DB_NAME
]


# ---------------------------------
# Collection
# ---------------------------------

collection = db[
    COLLECTION_NAME
]



# ---------------------------------
# Insert Documents
# ---------------------------------

def insert_documents(documents):
    """
    Insert multiple PDF chunks
    into MongoDB
    """

    if not documents:

        return None


    result = collection.insert_many(
        documents
    )


    return result.inserted_ids



# ---------------------------------
# Find Document by Vector ID
# ---------------------------------

def get_document_by_id(doc_id):
    """
    Retrieve chunk using FAISS ID
    """

    return collection.find_one(
        {
            "vector_id": doc_id
        }
    )



# ---------------------------------
# Find Documents by Document ID
# ---------------------------------

def get_documents_by_document_id(
        document_id
):

    """
    Retrieve all chunks
    belonging to one PDF
    """

    return list(
        collection.find(
            {
                "document_id":
                    document_id
            }
        )
    )



# ---------------------------------
# Delete PDF Data
# ---------------------------------

def delete_document(
        document_id
):

    """
    Delete all chunks
    of a PDF
    """

    result = collection.delete_many(
        {
            "document_id":
                document_id
        }
    )


    return result.deleted_count



# ---------------------------------
# Count Documents
# ---------------------------------

def count_documents():

    return collection.count_documents(
        {}
    )