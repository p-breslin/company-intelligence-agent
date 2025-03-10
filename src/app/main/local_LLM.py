import ollama
import logging
from utils.config import ConfigLoader
from utils.helpers import token_count
from langchain.text_splitter import RecursiveCharacterTextSplitter


class LocalLLM:
    """
    Wraps a local LLM for conversation-based responses, with the ability to handle multi-turn exchanges and chunk large inputs to avoid token limits.
    """

    def __init__(
        self, model="llama-instruct", conversation_limit=5, custom_chunking=None
    ):
        cfg = ConfigLoader("llmConfig")
        self.llm = cfg.get_section("models")[model]
        self.prompts = cfg.get_section("prompts")
        self.chunked_summary = cfg.get_value("chunked_summary")

        # Option to pass custom chunk options for testing purposes
        if custom_chunking:
            self.chunking = custom_chunking
        else:
            self.chunking = cfg.get_section("chunking")

        # Limit on how many user+assistant pairs of messages to keep around
        self.conversation_limit = conversation_limit

        # Stores as a list of dicts: [{"role": "...", "content": "..."}]
        self.conversation_history = []

    def chunk_text(self, text):
        """
        Splits large text into smaller overlapping chunks according to the
        configured chunk_size and chunk_overlap values.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunking["size"], chunk_overlap=self.chunking["overlap"]
        )
        return splitter.split_text(text)

    def call_llm(self, messages):
        """
        Sends a list of messages (role + content) to the local LLM and returns its response as a string. Wraps Ollama's API call.
        """
        try:
            response = ollama.chat(
                model=self.llm,
                messages=messages,
                stream=False,
                options={"keep_alive": "5m"},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logging.error(f"LLM request failed: {e}")
            return f"LLM Error: {str(e)}"

    def prior_messages(self):
        """
        Retrieves the most recent messages from conversation history. Each user + assistant pair is effectively 2 messages, so we multiple by 2.
        """
        max_messages = self.conversation_limit * 2
        return self.conversation_history[-max_messages:]

    def handle_chunking(self, query, context, multi_turn=False):
        """
        Breaks up a large prompt into smaller chunks and queries the model chunk by chunk. Then merges and summarizes the chunked responses into a single final response.
        """
        chunks = self.chunk_text(context)
        logging.info(f"Text split into {len(chunks)} chunks.")
        chunked_responses = []

        # Retrieve recent conversation context if multi-turn
        prior_msgs = self.prior_messages() if multi_turn else []

        # For each chunk, append the chunk to conversation context and query LLM
        for i, chunk in enumerate(chunks):
            logging.info(f"Chunk {i + 1}")

            # Give LLM chunking context
            messages = prior_msgs + [
                {
                    "role": "user",
                    "content": f'###Task:\nYou are tasked with summarizing a chunk of text that belongs to a larger document. This document has been split into multiple smaller documents. You will be given one of these smaller documents. To achieve your task, you will concisely summarize the given document while retaining the critical information and including any numbers or statistics. To do this, you will ONLY use the text from the given document. Be sure to include any information that might help to answer this question: "{query}"\n\n### Document Part {i + 1}/{len(chunks)}:\n{chunk}',
                }
            ]
            logging.debug(messages[0]["content"])
            response = self.call_llm(messages)
            logging.debug(f"\nResponse:\n{response}\n\n")
            chunked_responses.append(response)

        # Summarize all chunked responses
        summary_prompt = self.chunked_summary.format(query=query) + "\n".join(
            chunked_responses
        )
        logging.debug(summary_prompt)

        # Combine the summarized chunks with the user prompt
        messages = messages + [{"role": "user", "content": summary_prompt}]
        final_response = self.call_llm(messages)

        return final_response

    def generate(self, query, context, prompt_format="concise", multi_turn=False):
        """Generate a response with optional multi-turn conversation support."""
        if multi_turn:
            original_query = ""
            previous_response = ""

            # Retrieve the most recent user+assistant pair
            for history in reversed(self.conversation_history):
                if history["role"] == "user" and not original_query:
                    original_query = history["content"]
                elif history["role"] == "assistant" and not previous_response:
                    previous_response = history["content"]
                if original_query and previous_response:
                    break

            # Build prompt using the stored multi-turn pieces
            input_prompt = self.prompts[prompt_format].format(
                user_query=query,
                context=context,
                original_query=original_query,
                previous_response=previous_response,
            )
        else:
            # Single-turn prompt
            input_prompt = self.prompts[prompt_format].format(
                user_query=query, context=context
            )

        # If token limits exceeded; chunking required
        tokens = token_count(input_prompt)
        if tokens > self.chunking["limit"]:
            logging.info(f"Token count = {tokens}")
            output = self.handle_chunking(query, context, multi_turn)
        else:
            logging.info("No chunking required.")
            # Get prior messages if multi-turn
            if multi_turn:
                messages = self.prior_messages()
            else:
                messages = []
            messages = messages + [{"role": "user", "content": input_prompt}]
            output = self.call_llm(messages)

        # Update conversation history
        self.conversation_history.extend(
            [
                {"role": "user", "content": input_prompt},
                {"role": "assistant", "content": output},
            ]
        )
        return output


if __name__ == "__main__":
    llm = LocalLLM()
