import ollama
from collections import Counter
from utils.config import config
from utils.helpers import token_count, load_postgres_data
from langchain.text_splitter import RecursiveCharacterTextSplitter


class LocalLLM:
    def __init__(self, conversation_limit=5):
        self.db = config.get_section("DB_USER")
        self.llm = config.get_section("models")["llama"]
        self.prompts = config.get_section("prompts")
        self.chunking = config.get_section("chunking")
        self.conversation_limit = conversation_limit
        self.conversation_history = []

    def chunk_text(self, text):
        """Text splitter for making content chunks for the LLM."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunking["size"], chunk_overlap=self.chunking["overlap"]
        )
        return splitter.split_text(text)

    def generate_response(self, user_query, retrieved_text, multi_turn=False):
        """
        Uses the Local LLM to generate either a:
            - Single response from one turn conversation.
            - Many responses with context using a multi-turn conversation.
            - The user query and the retrieved content is input to the LLM.
            - Output of LLM is a generated refined response.
        """
        input = f"User Query: {user_query}\n\nRetrieved Content:\n{retrieved_text}"

        # Step 1: Handle Chunking (if needed)
        if token_count(input) > self.chunking["limit"]:
            chunks = self.chunk_text(input)
            chunked_responses = []

            if multi_turn:
                # Multi-turn mode maintains the conversation history
                for chunk in chunks:
                    self.conversation_history.append({"role": "user", "content": chunk})

                try:
                    # Generate response in multi-turn mode
                    response = ollama.chat(
                        model=self.llm, messages=self.conversation_history
                    )
                    output = response["message"]["content"].strip()

                    # Store agent response in history
                    self.conversation_history.append(
                        {"role": "agent", "content": output}
                    )
                    return output

                except Exception as e:
                    return f"LLM Error: {str(e)}"

            else:
                # Process each chunk independently in single-turn mode
                for chunk in chunks:
                    try:
                        response = ollama.generate(model=self.llm, prompt=chunk)
                        chunked_responses.append(response["response"].strip())
                    except Exception as e:
                        chunked_responses.append(f"LLM Error on chunk: {str(e)}")

                # Merge responses into a coherent answer
                summary_prompt = f"Here are multiple responses related to the same query:\n\n{'\n'.join(chunked_responses)}\n\nPlease summarize them into a single, well-structured answer."

                try:
                    response = ollama.generate(model=self.llm, prompt=summary_prompt)
                    return response["response"].strip()
                except Exception as e:
                    return f"LLM Summarization Error: {str(e)}"

        # Step 2: No Chunking Required: Single-Turn or Multi-Turn Processing
        try:
            if multi_turn:
                self.conversation_history.append({"role": "user", "content": input})

                # Trim conversation history if it exceeds the limit
                # Each exchange has 2 messages (one from user, one from agent)
                if len(self.conversation_history) > self.conversation_limit * 2:
                    self.conversation_history = self.conversation_history[
                        -self.conversation_limit * 2 :
                    ]

                # Call Ollama with full conversation history
                response = ollama.chat(
                    model=self.llm, messages=self.conversation_history
                )
                output = response["message"]["content"].strip()

                # Store agent response in history
                self.conversation_history.append({"role": "agent", "content": output})

            else:
                # Single-turn mode does not maintain conversation history
                response = ollama.generate(model=self.llm, prompt=input)
                output = response["response"].strip()

            return output

        except Exception as e:
            return f"LLM Error: {str(e)}"  # Return error message if API fails


if __name__ == "__main__":
    llm = LocalLLM()
