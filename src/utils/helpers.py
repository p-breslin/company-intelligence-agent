import re
import html
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def compute_hash(title, url):
    """ Hashes title + base domain to ensure consistency across RSS & scraping """
    base_domain = urlparse(url).netloc  # Extracts the domain
    return hashlib.md5((title + base_domain).encode('utf-8')).hexdigest()


def clean_raw_html(raw_html):
    """Extracts text from raw HTML while removing unnecessary elements."""
    
    # Extract all paragraph content (p tags contain the actual text)
    soup = BeautifulSoup(raw_html, "html.parser")
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    
    # Join paragraphs into a single readable text block
    text = "\n\n".join(paragraphs)  # Keeps paragraph breaks for readability

    # Convert HTML entities (e.g., &nbsp; and &quot;)
    text = html.unescape(text)

    # Remove extra spaces, newlines, and multiple consecutive blank lines
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\n{2,}", "\n\n", text)  # Preserve paragraph separation
    return text.strip()   