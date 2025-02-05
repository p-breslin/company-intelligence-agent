import ollama
import psycopg
from utils.config import config

class LocalLLM:
    def __init__(self):
        self.db = config.get_section("database")
        self.llm = config.get_section("models")["llama"]
        self.prompts = config.get_section("prompts")

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
        articles = cursor.fetchall()
        conn.close()
        print(articles)
        return articles

    def categorize(self, text):
        """
        Categorizes the imported data using a prompt with the local LLM.
        Don't need to simulate multi-turn chat here i.e. ollama.chat
        """
        prompt = f"{self.prompts["categories"]}\n{text}"
        response = ollama.generate(model=self.llm, prompt=prompt)
        return response["response"].strip()


if __name__ == "__main__":
    llm = LocalLLM()
    articles = llm.import_data()

    for content in articles:
        category = llm.categorize(content)
        print(f"Category: {category}")