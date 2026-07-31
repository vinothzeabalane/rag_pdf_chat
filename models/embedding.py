from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL

from logging_utils import configure_logger


logger = configure_logger(__name__)

_model = None


def get_embedding_model():
    global _model

    if _model is None:
        logger.info(
            "embedding:load-model name=%s",
            EMBED_MODEL
        )
        _model = SentenceTransformer(EMBED_MODEL)

    return _model


def encode_text(text):
    return get_embedding_model().encode(text)
