# llm.py

import ollama

from config import LLM_MODEL


# ---------------------------------
# Create prompt
# ---------------------------------

def create_prompt(question, context):
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

def generate_answer(question, context):
    prompt = create_prompt(question, context)

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

    except Exception as e:
        return f"LLM connection error: {str(e)}"
