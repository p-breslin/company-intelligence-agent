import re
import logging
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler


class CrawlLinks:
    def __init__(self):
        pass

    async def crawl_links(self, domain):
        """Crawl the domain and extract article URLs using Crawl4AI."""
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=domain)

                if result.success:
                    links = [link["href"] for link in result.links.get("internal", [])]
                    return links
                else:
                    logging.warning(f"Failed to crawl domain: {domain}")
                    return []
        except Exception as e:
            logging.error(f"Unexpected error crawling links: {e}")
        return []

    def initial_filter(self, links):
        """Reduce list of links to 'main' domains of interest."""
        keywords = [
            "news",
            "blog",
            "blogs",
            "article",
            "story",
            "post",
            "press",
            "press-release",
            "press-releases",
            "press-newsroom",
            "news-analysis",
            "articles",
            "stories",
            "analysis",
            "latest-news",
            "resource",
            "top-stories-of-the-week",
            "newsroom",
            "news-and-resources",
            "market-analysis",
            "whatsnew.shtml",
            "artificial-intelligence-ai",
            "analyst-angle",
        ]

        matches = []
        for link in links:
            parsed = urlparse(link)
            path = parsed.path  # Get the path without query or fragment

            # Strip any trailing slash
            if path.endswith("/"):
                path = path[:-1]

            # Split on "/" and take the last part
            last_segment = path.split("/")[-1].lower() if path else ""

            # If it matches any of the keywords, keep this link
            if last_segment in keywords:
                matches.append(link)

        return matches

    def final_filter(self, links, min_word_count=4):
        """Reduces links to those with last segment >= min_word_count."""
        filtered = []
        for link in links:
            end = link.rstrip("/").split("/")[-1]  # Last segment of the URL
            words = re.split(r"[-_]", end)  # Split on hyphens or underscores

            # Count words (allowing words with numbers)
            word_count = sum(1 for w in words if re.match(r"^[a-zA-Z0-9]+$", w))

            if word_count >= min_word_count:
                filtered.append(link)

        return filtered

    async def run(self, feed):
        articles = []

        # First crawl: extracts links from base domain
        links = await self.crawl_links(feed)

        # Initial filter: filters links to pages we care about
        filtered_links = self.initial_filter(links)

        filtered_articles = []
        for link in filtered_links:
            # Second crawl: extracts links from pages we care about
            article_links = await self.crawl_links(link)

            # Final filter: filters links to articles we care about
            filtered_article_links = self.final_filter(article_links)

            # Picking first five (hopefully the latest?)
            filtered_articles.extend(filtered_article_links[:1])

        # Remove base domain urls if any remain
        filtered_articles = [
            item for item in filtered_articles if item not in filtered_links
        ]
        articles.extend(filtered_articles)

        return articles
