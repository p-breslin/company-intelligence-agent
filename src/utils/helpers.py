import hashlib
from urllib.parse import urlparse

def compute_hash(title, url):
    """ Hashes title + base domain to ensure consistency across RSS & scraping """
    base_domain = urlparse(url).netloc  # Extracts the domain
    return hashlib.md5((title + base_domain).encode('utf-8')).hexdigest()