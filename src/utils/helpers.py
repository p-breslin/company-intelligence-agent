import re
import html
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def compute_hash(title, url):
    """ Hashes title + base domain to ensure consistency across RSS & scraping """
    base_domain = urlparse(url).netloc  # Extracts the domain
    return hashlib.md5((title + base_domain).encode('utf-8')).hexdigest()


def clean_raw_html(raw_html, feed="rss"):
    """Extracts text from raw HTML while removing unnecessary elements."""

    # Parse with BeautifulSoup to remove HTML tags
    soup = BeautifulSoup(raw_html, "html.parser")
    
    if feed=="rss":
        # Extract text while preserving paragraph breaks
        text = "\n\n".join(soup.stripped_strings)

        # Normalize spacing and convert HTML entities
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()

    if feed=="web":
        # Use space instead of newlines for better readability
        text = soup.get_text(separator=" ") 

        # Remove excessive whitespace (noramlizes whitespace)
        text = re.sub(r"\s+", " ", text).strip()
    
    return text   


def token_count(text):
    """
    Estimates the token count based on word and character length.
    Approx. number of tokens per word in English = 0.75.
    Average number of characters per token = 4.
    If text has many short words: (characters/4) gives better estimate.
	If text has longer words: (words*0.75) is more accurate.
    """
    words = text.split()
    chars = len(text)
    return int(max(len(words)*0.75, chars/4))