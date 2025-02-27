import json
import logging
from dateutil import parser
from utils.helpers import clean_html


def extract_title(soup):
    """
    Extract article title using multiple fallback strategies.
    """
    # <title> tag
    title_tag = soup.find("title")
    if title_tag and title_tag.text.strip():
        return title_tag.text.strip()

    # OpenGraph meta tag
    title = soup.find("meta", attrs={"property": "og:title"}) or soup.find(
        "meta", attrs={"name": "twitter:title"}
    )
    if title and title.get("content"):
        return title["content"].strip()

    # <h1> tag (usually contains article title)
    h1_tag = soup.find("h1")
    if h1_tag and h1_tag.text.strip():
        return h1_tag.text.strip()

    return None


def extract_published_date(soup):
    """
    Extract article published date using multiple fallback strategies.
    """
    selectors = [
        {"property": "article:published_time"},
        {"property": "og:updated_time"},
        {"name": "date"},
        {"property": "publish_date"},
        {"itemprop": "datePublished"},
        {"name": "dc.date"},
        {"name": "dcterms.created"},
    ]

    for selector in selectors:
        tag = soup.find("meta", selector)
        if tag and tag.get("content"):
            try:
                return parser.parse(tag["content"])
            except Exception as e:
                logging.debug(f"Error parsing date '{tag['content']}': {e}")

    return None


def extract_summary(soup):
    """
    Extract article summary using multiple fallback strategies.
    """
    meta_tags = [
        {"name": "description"},
        {"property": "og:description"},
        {"name": "twitter:description"},
    ]

    for meta in meta_tags:
        tag = soup.find("meta", meta)
        if tag and "content" in tag.attrs:
            return tag["content"].strip()

    return None


def extract_content(soup):
    """
    Extract the main article text using multiple fallback strategies.
    """
    # 1) Check for JSON-LD data
    json_ld_data = extract_json_ld(soup)
    if json_ld_data.get("articleBody"):
        return clean_html(json_ld_data["articleBody"], feed="web")

    # 2) Look for an <article> tag
    content_tag = soup.find("article")
    if content_tag:
        # Keeps spacing between paragraphs
        paragraphs = [p.get_text(strip=True) for p in content_tag.find_all("p")]
        if paragraphs:
            return clean_html(" ".join(paragraphs), feed="web")

        # Extract entire <article> text if no <p> tags exist
        return clean_html(content_tag.get_text(separator=" "), feed="web")

    # 3) Try common content container classes
    selectors = [
        "div.article-content",
        "div.entry-content",
        "div.post-content",
        "section.article-body",
        "div#content",
    ]
    for selector in selectors:
        container = soup.select_one(selector)
        if container and container.get_text(strip=True):
            return clean_html(container.get_text(strip=True), feed="web")

    # Extract paragraphs (<p> tags) while preserving spacing
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    if paragraphs:
        return clean_html(" ".join(paragraphs), feed="web")

    # 5) Use entire <body> text (last resort)
    body_tag = soup.find("body")
    if body_tag and body_tag.get_text(strip=True):
        return clean_html(body_tag.get_text(strip=True), feed="web")

    return None


def extract_tags(soup):
    """
    Extract tags/keywords using multiple fallback strategies.
    """
    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
    if meta_keywords and meta_keywords.get("content"):
        return [kw.strip() for kw in meta_keywords["content"].split(",")]

    meta_news_keys = soup.find("meta", attrs={"name": "news_keywords"})
    if meta_news_keys and meta_news_keys.get("content"):
        return [kw.strip() for kw in meta_news_keys["content"].split(",")]

    return "not found"


def extract_json_ld(soup):
    """
    Extract structured article metadata from JSON-LD.
    Returns a dictionary with extracted values.
    """
    data = {}
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            ld_json = json.loads(script.string or "{}")

            # Some pages have an array of JSON-LD objects
            if isinstance(ld_json, list):
                for item in ld_json:
                    if item.get("@type") in ["Article", "NewsArticle", "BlogPosting"]:
                        data.update(item)
            else:
                if ld_json.get("@type") in ["Article", "NewsArticle", "BlogPosting"]:
                    data.update(ld_json)
        except json.JSONDecodeError:
            continue

    return data
