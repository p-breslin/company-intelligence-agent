import json
import ollama
from utils.config import ConfigLoader

cfg = ConfigLoader("testsConfig")
template = cfg.get_value("instruct_prompt")
context = cfg.get_value("instruct_article")
prompt = template.format(company="Palantir", article=context)

system_prompt = cfg.get_value("system_prompt").format(company="Palantir")

test1 = [{"role": "user", "content": prompt}]
test2 = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": context},
]


LLMs = [
    "llama3.2:1b",
    "granite3.2:2b",
    "llama3.2:1b-instruct-q4_K_M",
    "granite3.2:2b-instruct-q4_K_M",
]

response = ollama.chat(
    model=f"{LLMs[3]}",
    messages=test2,
    stream=False,
    options={"keep_alive": "1m"},
)
raw_output = response["message"]["content"]
try:
    structured_data = json.loads(raw_output)
    print(json.dumps(structured_data, indent=4))
except json.JSONDecodeError:
    print("ERROR: Model did not return valid JSON. Raw output:")
    print(raw_output)