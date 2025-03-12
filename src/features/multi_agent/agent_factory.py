import os
import re
import asyncio
import logging
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from app.main.embedding_search import EmbeddingSearch

from features.multi_agent.LLM import call_llm
from features.multi_agent.prompts import QUERY_GENERATOR, QUERY_LIST
from features.multi_agent.cfg import TAVILY_SEARCH_PARAMS, DEFAULT_EXTRACTION_SCHEMA


load_dotenv()
tavily_async_client = AsyncTavilyClient(os.getenv("TAVILY_API_KEY"))


def agent_check_database(user_input):
    """Agent 1: Searches vector and graph databases"""
    data, content = EmbeddingSearch(user_input).run()
    if not data or not content:
        logging.info("No stored data; initiating web search.")
        agent_web_search()

    logging.info("Using stored data.")
    agent_refine_results()


def agent_generate_queries(user_input):
    """Agent 2: Generates search queries"""
    instructions = QUERY_GENERATOR.format(
        company=user_input,
        schema=DEFAULT_EXTRACTION_SCHEMA,
        user_notes=None,
        max_search_queries=2,
    )
    messages = [
        {"role": "system", "content": instructions},
        {
            "role": "user",
            "content": QUERY_LIST.format(max_search_queries=2),
        },
    ]
    output = call_llm(messages)
    search_queries = re.findall(r'"\s*(.*?)\s*"', output)  # remove enumeration
    logging.info(f"Generated search queries: {search_queries}")
    agent_web_search(search_queries)


async def agent_web_search(search_queries):
    """Agent 3: Finds new information via web search"""
    tasks = []
    for query in search_queries:
        tasks.append(tavily_async_client.search(query, **TAVILY_SEARCH_PARAMS))

    # Execute all searches concurrently
    search_results = await asyncio.gather(*tasks)
    agent_refine_results(search_results)


def agent_refine_results(results):
    """Agent 4: Refines results"""
    pass


def agent_revise_results():
    """Agent 5: Revises results"""
    pass


def agent_store_data():
    """Agent 6: Stores new data"""
    pass


def agent_return_results():
    """Agent 7: Returns results"""
    pass
