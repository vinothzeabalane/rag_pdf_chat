# config.py

import os


# ==============================
# MongoDB Configuration
# ==============================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

MONGO_DB = os.getenv(
    "MONGO_DB",
    "rag_db"
)

MONGO_COLLECTION = os.getenv(
    "MONGO_COLLECTION",
    "documents"
)


# ==============================
# Embedding Model Configuration
# ==============================

# Sentence Transformer model
# Used to convert text/questions into vectors

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "all-MiniLM-L6-v2"
)


# ==============================
# FAISS Configuration
# ==============================

STORAGE_DIR = "storage"

FAISS_INDEX_DIR = STORAGE_DIR

FAISS_INDEX = os.path.join(
    FAISS_INDEX_DIR,
    "faiss.index"
)


# ==============================
# PDF Upload Configuration
# ==============================

UPLOAD_DIR = os.path.join(
    STORAGE_DIR,
    "uploads"
)


# ==============================
# Chunking Configuration
# ==============================

# Number of words in each chunk

CHUNK_SIZE = 500


# Number of overlapping words
# Helps preserve context between chunks

CHUNK_OVERLAP = 50


# ==============================
# Vector Search Configuration
# ==============================

# Number of similar chunks returned

TOP_K_RESULTS = 5


# ==============================
# LLM Configuration
# ==============================

# Ollama local API

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)


# Local model name

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "llama3.1:8b"
)


# ==============================
# Application Configuration
# ==============================

APP_NAME = "PDF RAG Chat Assistant"


DEBUG = True