from github_client import get_paginated
from datetime import datetime

def extract_issues(repo, max_pages=5):
    """Pull issue data for resolution time analysis."""
    owner, name = repo.split("/")

    print(f"Extracting issues: {repo}")
    issues = get_paginated(
        f"/repos/{owner}/{name}/issues",
        params={"state": "closed", "sort": "updated", "direction": "desc"},
        max_pages=max_pages
    )

    rows = []
    for issue in issues:
        # GitHub issues endpoint returns PRs too — filter them out
        if "pull_request" in issue:
            continue

        created = issue.get("created_at")
        closed = issue.get("closed_at")

        resolution_hours = None
        if created and closed:
            delta = datetime.fromisoformat(closed.replace("Z", "")) - \
                    datetime.fromisoformat(created.replace("Z", ""))
            resolution_hours = round(delta.total_seconds() / 3600, 2)

        rows.append({
            "repo": repo,
            "issue_number": issue.get("number"),
            "title": issue.get("title", "")[:300],
            "state": issue.get("state"),
            "author_login": issue.get("user", {}).get("login"),
            "labels": ", ".join([l["name"] for l in issue.get("labels", [])]),
            "created_at": created,
            "closed_at": closed,
            "resolution_hours": resolution_hours,
            "comments": issue.get("comments", 0),
            "extracted_at": datetime.utcnow().isoformat()
        })

    print(f"  Total issues extracted: {len(rows)}")
    return rows
