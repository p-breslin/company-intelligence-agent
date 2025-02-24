import asyncio
import aiohttp
import logging
from utils.config import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def post_request(url, jina_key):
    """Fetches Markdown from Jina.ai Reader API for a single website."""

    api_url = f"https://r.jina.ai/{url}"
    headers = {"Authorization": f"Bearer {jina_key}"}
    payload = {
        "remove_all_images": True,
        "gather_all_links_at_the_end": False,
        "token_budget": 15000,
    }

    max_retries = 5
    retry_delay = 1  # Start with 1 second delay

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.post(
                    api_url, headers=headers, json=payload, timeout=15
                ) as response:

                    # Handle 429 Too Many Requests
                    if response.status == 429:
                        logging.warning(
                            f"Rate limit hit. Retrying in {retry_delay}s..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue

                    response.raise_for_status()  # For non-200 responses
                    return await response.text()  # Return raw markdown

            except aiohttp.ClientError as e:
                logging.error(f"Request failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    logging.error(f"Markdown fetch failed after {max_retries} retries: {url}")
    return None


async def get_request(url, jina_key):

    api_url = f"https://r.jina.ai/{url}"
    headers = {"Authorization": f"Bearer {jina_key}"}
    # response = requests.get(url, headers=headers)

    max_retries = 5
    retry_delay = 1
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 429:
                        logging.warning(
                            f"Rate limit hit. Retrying in {retry_delay}s..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue

                    response.raise_for_status()  # For non-200 responses
                    return await response.text()  # Return raw markdown

            except aiohttp.ClientError as e:
                logging.error(f"Request failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    logging.error(f"Markdown fetch failed after {max_retries} retries: {url}")
    return None


# Test Function
async def test():
    config = ConfigLoader("API_KEYS")
    jina_key = config.get_value("jina")
    url = "https://www.lightreading.com/ai-machine-learning/will-ai-spark-a-massive-pickup-in-mobile-data-traffic-"

    # markdown = await post_request(url, jina_key)
    markdown = await get_request(url, jina_key)

    if markdown:
        print("Extracted Markdown:\n", markdown)
    else:
        print("Failed to fetch markdown.")


# Run the test function
asyncio.run(test())
