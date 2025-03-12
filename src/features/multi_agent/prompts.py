QUERY_LIST = """Generate a list of simple search queries related to the schema that you want to populate. Do not include descriptions about your generated search queries - your response should ONLY be a list of {max_search_queries} search queries and nothing else."""

QUERY_GENERATOR = """You are a search query generator tasked with creating targeted search queries to gather specific company information.

Here is the company you are researching: {company}

Generate at most {max_search_queries} search queries that will help gather the following information:

<schema>
{schema}
</schema>

<user_notes>
{user_notes}
</user_notes>

Your query should:
1. Focus on finding factual, up-to-date company information
2. Target official sources, news, and reliable business databases
3. Prioritize finding information that matches the schema requirements
4. Include the company name and relevant business terms
5. Be specific enough to avoid irrelevant results but simple enough to be short and concise

Create a focused query that will maximize the chances of finding schema-relevant information."""
