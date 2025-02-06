import ollama
import psycopg
from utils.config import config
from utils.helpers import token_count
from langchain.text_splitter import RecursiveCharacterTextSplitter


class LocalLLM:
    def __init__(self):
        self.db = config.get_section("database")
        self.llm = config.get_section("models")["llama"]
        self.prompts = config.get_section("prompts")
        self.chunking = config.get_section("chunking")


    def import_data(self):
        """Imports stored data from database."""
        conn = psycopg.connect(
            dbname = self.db['name'],
            user = self.db['user'],
            password = self.db['pwd'],
            host = self.db['host'],
            port = self.db['port']
        )
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM articles LIMIT 1;")
        articles = cursor.fetchall() # list of tuples (each one is a database row)
        conn.close()
        return articles
    

    def chunking(self, text):
        """
        Text splitter for making content chunks for the LLM.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = self.chunking["size"],
            chunk_overlap = self.chunking["overlap"]
        )
        return splitter.split_text(text)


    def categorize(self, text):
        """
        Categorizes the imported data using a prompt with the local LLM.
        Don't need to simulate multi-turn chat here i.e. ollama.chat.
        Includes content chunking for efficiency.
        """
        tokens = token_count(text)

        if tokens <= self.chunking["limit"]:
            prompt = f"{self.prompts['categories']}\n{text}"
            response = ollama.generate(model=self.llm, prompt=prompt)
            return response["response"].strip()
        
        else:
            output = []
            chunks = self.chunking(text)
            for chunk in chunks:
                # No longer getting a label per article; now a label per chunk
                prompt = f"{self.prompts['categories']}\n{chunk}"
                response = ollama.generate(model=self.llm, prompt=prompt)
                output.append(response["response"].strip())

            # The most frequent category will be our determination
            return max(set(output), key=output.count)


if __name__ == "__main__":
    llm = LocalLLM()
    articles = llm.import_data()

    for content in articles:
        category = llm.categorize(content[0])
        print(f"Category: {category}")