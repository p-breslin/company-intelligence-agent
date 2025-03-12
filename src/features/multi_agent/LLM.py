import ollama
import logging


def call_llm(messages):
    """
    Sends a list of messages (role + content) to the local LLM and returns its response as a string. Wraps Ollama's API call.
    """
    try:
        response = ollama.chat(
            model="granite3.2:2b-instruct-q4_K_M",
            messages=messages,
            stream=False,
            options={"keep_alive": "5m"},
        )
        return response["message"]["content"].strip()
    except Exception as e:
        logging.error(f"LLM request failed: {e}")
        return f"LLM Error: {str(e)}"
