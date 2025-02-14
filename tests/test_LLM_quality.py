import pandas as pd
from utils.config import ConfigLoader
from backend.LLM_integration import LocalLLM


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
            response = llm.generate_response(q, self.article, prompt="test")
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


if __name__ == "__main__":
    test = TestLLM()
    test.LLM_response()
    test.save_dataframe()
