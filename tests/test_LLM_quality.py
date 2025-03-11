import ollama
import pandas as pd
from utils.config import ConfigLoader
from app.main.local_LLM import LocalLLM


class TestLLM:
    def __init__(self):
        config = ConfigLoader(filename="testsConfig")
        self.article = config.get_list("article")
        self.questions = config.get_list("Questions")
        self.answers = config.get_list("Answers")
        self.local_LLM = []

    def LLM_response(self):
        llm = LocalLLM()
        for q in self.questions:
            print(q)
            response = llm.generate(q, self.article, prompt_format="test_short")
            self.local_LLM.append(response)

    def save_dataframe(self):
        df = pd.DataFrame(
            {
                "Question": self.questions,
                "Test LLM": self.answers,
                "Local LLM": self.local_LLM,
            }
        )
        df.to_csv("data/test_LLM.csv", index=False)

    def LLM_without_data(self):
        responses = []
        for q in self.questions:
            print(q)
            output = ollama.generate(
                model="llama3.2:1b",
                prompt=f"Provide a one sentence answer to the following query: {q}",
            )
            responses.append(output.response.strip())
        df = pd.DataFrame({"Local LLM without data": responses})
        df.to_csv("data/test_LLM_no_data.csv", index=False)


if __name__ == "__main__":
    test = TestLLM()
    # test.LLM_response()
    # test.save_dataframe()
    test.LLM_without_data()
