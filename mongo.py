# mongo.py

from pymongo import MongoClient, ASCENDING, DESCENDING

from config import (
    MONGO_URI,
    MONGO_DB,
    MONGO_COLLECTION
)



# ---------------------------------
# MongoDB Connection
# ---------------------------------

client = MongoClient(
    MONGO_URI
)


db = client[
    MONGO_DB
]


collection = db[
    MONGO_COLLECTION
]



# ---------------------------------
# Test Connection
# ---------------------------------

try:

    client.admin.command(
        "ping"
    )

    print(
        "MongoDB connected successfully"
    )


except Exception as e:

    print(
        "MongoDB connection failed:",
        e
    )

    raise e



# ---------------------------------
# Create MongoDB Indexes
# ---------------------------------

def create_indexes():

    """
    Create indexes for faster search
    """

    # Faster duplicate-PDF lookup (not unique — every chunk of a PDF shares the same hash)

    collection.create_index(
        [
            (
                "file_hash",
                ASCENDING
            )
        ]
    )


    # Faster vector lookup

    collection.create_index(
        [
            (
                "vector_id",
                ASCENDING
            )
        ]
    )


    # Faster document lookup

    collection.create_index(
        [
            (
                "document_id",
                ASCENDING
            )
        ]
    )


    print(
        "MongoDB indexes created"
    )



# Create indexes automatically

create_indexes()



# ---------------------------------
# Get document by vector ID
# ---------------------------------

def get_document_by_id(
        vector_id
):

    """
    Retrieve chunk using FAISS vector ID
    """


    document = collection.find_one(

        {
            "vector_id":
                vector_id
        }

    )


    return document



# ---------------------------------
# Check duplicate PDF
# ---------------------------------

def document_exists(
        file_hash
):

    """
    Check whether PDF already exists
    """


    document = collection.find_one(

        {
            "file_hash":
                file_hash
        }

    )


    return document



# ---------------------------------
# Get next vector ID
# ---------------------------------

def get_last_vector_id():

    """
    Get highest vector ID
    """


    document = collection.find_one(

        sort=[
            (
                "vector_id",
                DESCENDING
            )
        ]

    )


    if document:

        return document[
            "vector_id"
        ]


    return 0



# ---------------------------------
# Get all documents
# ---------------------------------

def get_all_documents():

    """
    Return uploaded PDFs
    """


    documents = collection.find(
        {},
        {
            "_id":0,
            "embedding":0
        }
    )


    return list(
        documents
    )



# ---------------------------------
# Delete one document
# ---------------------------------

def delete_document(
        document_id
):

    """
    Delete PDF chunks
    """


    result = collection.delete_many(

        {
            "document_id":
                document_id
        }

    )


    return result.deleted_count



# ---------------------------------
# Delete all documents
# ---------------------------------

def delete_all_documents():

    """
    Development use only
    """


    result = collection.delete_many(
        {}
    )


    return result.deleted_count