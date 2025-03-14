import ollama
import logging


def call_local_llm(messages):
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


def call_llm(client, messages, schema=False):
    """
    Sends a list of messages (role + content) to ChatGPT.
    """
    try:
        if schema:
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=messages,
                response_format=schema,
            )
            content = response.choices[0].message.content
            logging.info(f"ChatGPT structured response: {content}")
            return content
        else:
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18", messages=messages
            )
            content = response.choices[0].message.content
            logging.info(f"ChatGPT unstructured response: {content}")
            return content

    except Exception as e:
        logging.error(f"ChatGPT request failed: {e}")
        return f"ChatGPT Error: {str(e)}"
