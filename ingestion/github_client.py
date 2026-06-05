import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

REPOS = [
    "tensorflow/tensorflow",
    "pytorch/pytorch",
    "kubernetes/kubernetes",
    "facebook/react",
    "microsoft/vscode"
]

def get(endpoint, params=None):
    """Make a single GET request to GitHub API with rate limit handling."""
    url = f"{BASE_URL}{endpoint}"
    params = params or {}

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 403:
        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait = max(reset_time - int(time.time()), 10)
        print(f"Rate limit hit. Waiting {wait}s...")
        time.sleep(wait)
        return get(endpoint, params)

    response.raise_for_status()
    return response.json()

def get_paginated(endpoint, params=None, max_pages=5):
    """Fetch multiple pages from a GitHub endpoint."""
    params = params or {}
    params["per_page"] = 100
    results = []

    for page in range(1, max_pages + 1):
        params["page"] = page
        data = get(endpoint, params)
        if not data:
            break
        results.extend(data)
        print(f"  Page {page}: {len(data)} records fetched")

    return results
