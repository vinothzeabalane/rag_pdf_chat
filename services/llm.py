# llm.py

import ollama
import time

from config import LLM_MODEL

from logging_utils import configure_logger, set_request_id, get_request_id


logger = configure_logger(__name__)


# ---------------------------------
# Create prompt
# ---------------------------------

def create_prompt(question, context):
    logger.debug(
        "llm:create-prompt question_chars=%s context_chars=%s",
        len(question),
        len(context)
    )

    return (
        "You are a helpful assistant.\n"
        "Answer the question only using the provided context.\n"
        "If the answer is not in the context, say: "
        "'I could not find the answer in the provided document.'\n\n"
        f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
    )


# ---------------------------------
# Call Ollama LLM
# ---------------------------------

def generate_answer(question, context, request_id=None):
    start_time = time.perf_counter()

    if request_id:
        set_request_id(request_id)

    logger.info(
        "llm:start request_id=%s model=%s question_chars=%s context_chars=%s",
        get_request_id(),
        LLM_MODEL,
        len(question),
        len(context)
    )

    prompt = create_prompt(question, context)

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response["message"]["content"]

        logger.info(
            "llm:done answer_chars=%s elapsed=%.3fs",
            len(content),
            time.perf_counter() - start_time
        )

        return content

    except Exception as e:
        logger.exception(
            "llm:error model=%s error=%s",
            LLM_MODEL,
            str(e)
        )

        return f"LLM connection error: {str(e)}"
