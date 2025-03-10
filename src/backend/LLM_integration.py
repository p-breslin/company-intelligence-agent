import ollama
import logging
from utils.config import ConfigLoader
from utils.helpers import token_count
from langchain.text_splitter import RecursiveCharacterTextSplitter


class LocalLLM:
    """
    Wraps a local LLM for conversation-based responses, with the ability to handle multi-turn exchanges and chunk large inputs to avoid token limits.
    """

    def __init__(self, conversation_limit=5):
        config = ConfigLoader("llmConfig")
        self.llm = config.get_section("models")["llama-instruct"]
        self.prompts = config.get_section("prompts")
        self.chunking = config.get_section("chunking")

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

    def handle_chunking(self, input_prompt, multi_turn=False):
        """
        Breaks up a large prompt into smaller chunks and queries the model chunk by chunk. Then merges and summarizes the chunked responses into a single final response.
        """
        chunks = self.chunk_text(input_prompt)
        chunked_responses = []

        # Retrieve recent conversation context if multi-turn
        prior_msgs = self.prior_messages() if multi_turn else []

        # For each chunk, append the chunk to conversation context and query LLM
        for chunk in chunks:
            messages = prior_msgs + [{"role": "user", "content": chunk}]
            response = self.call_llm(messages)
            chunked_responses.append(response)

        # Summarize all chunked responses
        summary_prompt = (
            "You have multiple responses that are each part of a larger document. Merge and summarize them into one concise, well-structured answer.\n\nPartial Responses:\n"
            + "\n".join(chunked_responses)
        )

        # Combine the summarized chunks with the user prompt
        messages = messages + [{"role": "user", "content": summary_prompt}]
        final_response = self.call_llm(messages)

        # Update the conversation history
        self.conversation_history.extend(
            [
                {"role": "user", "content": input_prompt},
                {"role": "assistant", "content": final_response},
            ]
        )
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
        if token_count(input_prompt) > self.chunking["limit"]:
            output = self.handle_chunking(input_prompt, multi_turn)
        else:
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
