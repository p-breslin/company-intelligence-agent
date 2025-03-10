import logging
from utils.config import ConfigLoader
from backend.LLM_integration import LocalLLM

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

model = "llama-instruct"  # granite-instruct
cfg = ConfigLoader("llmConfig")
llm = LocalLLM(model=model)
test_article = ConfigLoader("testsConfig").get_value("instruct_article")

test_query = (
    "How much is the global AI market in aerospace and defense projected to surge?"
)
print(f"Query:\n{test_query}\n\n")


no_chunking = llm.generate(test_query, test_article)
print(f"Without chunking:\n{no_chunking}\n\n")

custom_chunking = {"size": 2000, "overlap": 20, "limit": 1000}
llm = LocalLLM(model=model, custom_chunking=custom_chunking)
chunking = llm.generate(test_query, test_article)
print(f"With chunking:\n{chunking}")
