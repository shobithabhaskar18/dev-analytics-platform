from github_client import get_paginated, REPOS
from datetime import datetime, timedelta

def extract_commits(repo, days_back=90):
    """Pull commit history for a repo for the last N days."""
    since = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
    owner, name = repo.split("/")

    print(f"Extracting commits: {repo}")
    commits = get_paginated(
        f"/repos/{owner}/{name}/commits",
        params={"since": since},
        max_pages=5
    )

    rows = []
    for c in commits:
        rows.append({
            "repo": repo,
            "sha": c.get("sha"),
            "author_login": c.get("author", {}).get("login") if c.get("author") else None,
            "author_name": c.get("commit", {}).get("author", {}).get("name"),
            "message": c.get("commit", {}).get("message", "")[:500],
            "committed_at": c.get("commit", {}).get("author", {}).get("date"),
            "extracted_at": datetime.utcnow().isoformat()
        })

    print(f"  Total commits extracted: {len(rows)}")
    return rows
