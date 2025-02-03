import feedparser
import requests
from bs4 import BeautifulSoup

# Step 1: Fetch and parse an RSS feed
rss_url = "https://www.experienceflow.ai/feed/"
feed = feedparser.parse(rss_url)

# Step 2: Loop through the RSS feed and print basic metadata
for entry in feed.entries:
    title = entry.title
    link = entry.link
    published = entry.published
    category = entry.category
    summary = entry.summary

    print(f"Title: {title}")
    print(f"Link: {link}")
    print(f"Published: {published}")
    print(f"Category: {category}")
    print(f"Summary: {summary}")
    print("-----------\n")

    # Step 3: Fetch the full webpage content from the link in the RSS feed
    response = requests.get(link)

    # Step 4: Use BeautifulSoup to parse and extract more data from the webpage
    soup = BeautifulSoup(response.content, 'html.parser')