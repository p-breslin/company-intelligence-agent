import asyncio
import logging
import requests
from mistralai import Mistral
from utils.config import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def mistral_request_async(model, query, api_key):
    """Asynchronous function to make a request to Mistral."""
    client = Mistral(api_key=api_key)
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            response = await client.chat.complete_async(
                model=model, messages=query, response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            error_message = str(e)
            if "RESOURCE_EXHAUSTED" in error_message or "429" in error_message:
                logging.warning(f"Rate limit hit. Retrying in {retry_delay}s...")
            elif "503" in error_message or "timeout" in error_message:
                logging.warning(f"Temporary issue. Retrying... {e}")
            else:
                logging.error(f"Error: {e}")
                return None
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff

    logging.error("Mistral request failed after retries.")
    return None


def mistral_request_sync(model, query, api_key):
    """Synchronous function to make a single request to Mistral."""
    client = Mistral(api_key=api_key)
    try:
        response = client.chat.complete(
            model=model, messages=query, response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Mistral request failed: {e}")
        return None


# Test Functions
async def test_async(model, query, api_key):
    response = await mistral_request_async(model, query, api_key)
    if response:
        print("Async Response:", response)
    else:
        print("Async Mistral request failed.")


def test_sync(model, query, api_key):
    response = mistral_request_sync(model, query, api_key)
    if response:
        print("Sync Response:", response)
    else:
        print("Sync Mistral request failed.")


# Run the tests
if __name__ == "__main__":
    api_key = ConfigLoader("API_KEYS").get_value("mistral")
    config = ConfigLoader("llmConfig")
    prompt = config.get_value("data_extraction_prompt")
    model = config.get_section("models")["mistral"]
    url = "https://www.lightreading.com/ai-machine-learning/will-ai-spark-a-massive-pickup-in-mobile-data-traffic-"
    markdown = requests.get(f"https://r.jina.ai/{url}")
    query = [
        {"role": "system", "content": f"{prompt}"},
        {"role": "user", "content": f"{markdown.text}"},
    ]

    # test_sync(model, query, api_key)
    asyncio.run(test_async(model, query, api_key))
