import hashlib

def compute_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()